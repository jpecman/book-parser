import sys
import uuid
from pathlib import Path
from typing import Any

from book_parser.embed import Embedder, create_embedder, split_into_chunks
from book_parser.extract import get_number_of_chapters, read_chapter
from book_parser.stores.qdrant import QdrantStore

BOOKS_DIR = Path("~/tmp/agent-books").expanduser()
# One collection per embedder: their vectors differ in size and can't be mixed.
COLLECTIONS = {"azure": "books", "fastembed": "books_fastembed"}


def store_chapter(path: str, book: str, chapter: int, embedder: Embedder) -> int:
    chunks = split_into_chunks(read_chapter(path, chapter))
    if not chunks:
        return 0

    vectors = embedder.embed(chunks)

    # Derived from book, chapter and position, so a re-run overwrites the
    # same points instead of adding duplicates.
    ids: list[int | str] = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"{book}/{chapter}/{index}"))
        for index in range(len(chunks))
    ]
    payloads: list[dict[str, Any]] = [
        {"book": book, "chapter": chapter, "chunk": index, "text": chunk}
        for index, chunk in enumerate(chunks)
    ]

    store = QdrantStore(
        collection=COLLECTIONS[embedder.name], vector_size=len(vectors[0])
    )
    store.ensure_collection()
    store.upsert(ids, vectors, payloads)
    return len(chunks)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print("Usage: python -m book_parser <file.pdf> [chapter]", file=sys.stderr)
        sys.exit(1)

    path = str(BOOKS_DIR / sys.argv[1])
    book = Path(sys.argv[1]).name

    if len(sys.argv) == 3:
        chapters = [int(sys.argv[2])]
    else:
        chapters = list(range(get_number_of_chapters(path)))

    embedder = create_embedder()

    total = 0
    for chapter in chapters:
        stored = store_chapter(path, book, chapter, embedder)
        print(f"Chapter {chapter}: {stored} chunks")
        total += stored

    print(f"Stored {total} chunks in Qdrant collection '{COLLECTIONS[embedder.name]}'")


if __name__ == "__main__":
    main()
