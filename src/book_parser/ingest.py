import re
import time
import uuid
from pathlib import Path
from typing import Any

from book_parser.chunking import split_into_chunks
from book_parser.embed import Embedder, create_embedder
from book_parser.errors import BookParserError
from book_parser.extract import get_number_of_chapters, read_chapter
from book_parser.settings import ChunkSettings
from book_parser.stores.qdrant import QdrantStore


# One collection per embedding model and chunking setup, so experiments
# don't overwrite each other.
def collection_name(embedder: Embedder, settings: ChunkSettings) -> str:
    model = re.sub(r"[^A-Za-z0-9_-]", "_", embedder.model_name.split("/")[-1])
    return f"books_{embedder.name}_{model}_c{settings.size}_o{settings.overlap}"


# Derived from book, chapter and position, so a re-run overwrites the same
# points instead of adding duplicates. chat-bot-be uses the same formula.
def point_id(book: str, chapter: int, chunk: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{book}/{chapter}/{chunk}"))


def store_chapter(
    book: Path,
    chapter: int,
    embedder: Embedder,
    store: QdrantStore,
    settings: ChunkSettings,
) -> int:
    chunks = split_into_chunks(
        read_chapter(str(book), chapter), settings.size, settings.overlap
    )
    if not chunks:
        return 0

    vectors = embedder.embed(chunks)

    ids: list[int | str] = [
        point_id(book.name, chapter, index) for index in range(len(chunks))
    ]
    payloads: list[dict[str, Any]] = [
        {"book": book.name, "chapter": chapter, "chunk": index, "text": chunk}
        for index, chunk in enumerate(chunks)
    ]

    store.upsert(ids, vectors, payloads)
    return len(chunks)


# Only the first book can resume part way; the rest start at the beginning.
def ingest_books(books: list[Path], settings: ChunkSettings, start_chapter: int = 0) -> None:
    # Checked before the embedder is created, so a wrong value fails fast.
    first_book_chapters = get_number_of_chapters(str(books[0]))
    if start_chapter >= first_book_chapters:
        raise BookParserError(
            f"--start-chapter {start_chapter} is past the last chapter of "
            f"{books[0].name}, which has chapters 0 to {first_book_chapters - 1}"
        )

    started = time.perf_counter()
    embedder = create_embedder()
    collection = collection_name(embedder, settings)
    store = QdrantStore(collection=collection)
    # One probe embedding gives the vector size, and fails fast if the
    # embedder or Qdrant is unreachable before any book is read.
    store.ensure_collection(vector_size=len(embedder.embed(["probe"])[0]))

    total = 0
    for index, book in enumerate(books):
        first_chapter = start_chapter if index == 0 else 0
        if first_chapter:
            print(f"{book.name} (from chapter {first_chapter})")
        else:
            print(book.name)
        for chapter in range(first_chapter, get_number_of_chapters(str(book))):
            chapter_started = time.perf_counter()
            stored = store_chapter(book, chapter, embedder, store, settings)
            duration = time.perf_counter() - chapter_started
            print(
                f"  {time.strftime('%H:%M:%S')} Chapter {chapter}: "
                f"{stored} chunks ({duration:.1f} s)"
            )
            total += stored

    print(f"Stored {total} chunks in Qdrant collection '{collection}'")
    minutes, seconds = divmod(round(time.perf_counter() - started), 60)
    print(f"Processed {len(books)} books in {minutes} min {seconds} s")
