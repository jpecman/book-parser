import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from book_parser.embed import Embedder, create_embedder, split_into_chunks
from book_parser.extract import get_number_of_chapters, read_chapter
from book_parser.stores.qdrant import QdrantStore

BOOKS_DIR = Path("~/tmp/agent-books").expanduser()
BOOK_SUFFIXES = {".epub", ".mobi", ".fb2", ".pdf"}


# One collection per embedding model and chunking setup, so experiments
# don't overwrite each other.
def collection_name(embedder: Embedder, chunk_size: int, overlap: int) -> str:
    model = re.sub(r"[^A-Za-z0-9_-]", "_", embedder.model_name.split("/")[-1])
    return f"books_{embedder.name}_{model}_c{chunk_size}_o{overlap}"


def find_books(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in BOOK_SUFFIXES
    )


def read_setting(name: str, default: int, minimum: int) -> int:
    raw = os.environ.get(name, str(default))
    if not raw.isdecimal() or int(raw) < minimum:
        print(
            f"{name} must be a whole number of at least {minimum}, got '{raw}'",
            file=sys.stderr,
        )
        sys.exit(1)
    return int(raw)


def store_chapter(
    path: str,
    book: str,
    chapter: int,
    embedder: Embedder,
    collection: str,
    chunk_size: int,
    overlap: int,
) -> int:
    chunks = split_into_chunks(read_chapter(path, chapter), chunk_size, overlap)
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

    store = QdrantStore(collection=collection, vector_size=len(vectors[0]))
    store.ensure_collection()
    store.upsert(ids, vectors, payloads)
    return len(chunks)


def print_chunks(book: Path, chunk_size: int, overlap: int) -> None:
    total = 0
    for chapter in range(get_number_of_chapters(str(book))):
        chunks = split_into_chunks(read_chapter(str(book), chapter), chunk_size, overlap)
        print(f"Chapter {chapter}: {len(chunks)} chunks")
        for index, chunk in enumerate(chunks):
            print(f"  {index} [{len(chunk)}] {chunk}")
        total += len(chunks)
    print(f"{total} chunks, nothing embedded or stored")


def print_embeddings(
    book: Path, embedder: Embedder, chunk_size: int, overlap: int
) -> None:
    total = 0
    for chapter in range(get_number_of_chapters(str(book))):
        chunks = split_into_chunks(read_chapter(str(book), chapter), chunk_size, overlap)
        vectors = embedder.embed(chunks) if chunks else []
        size = len(vectors[0]) if vectors else 0
        print(f"Chapter {chapter}: {len(chunks)} chunks, vector size {size}")
        total += len(chunks)
    collection = collection_name(embedder, chunk_size, overlap)
    print(f"Embedded {total} chunks for collection '{collection}', nothing stored")


def main() -> None:
    dry_run = len(sys.argv) == 3 and sys.argv[1] in ("--dry-run", "--dry-run-embed")
    if len(sys.argv) > 2 and not dry_run:
        print(
            "Usage: python -m book_parser [directory]\n"
            "       python -m book_parser --dry-run <book>\n"
            "       python -m book_parser --dry-run-embed <book>",
            file=sys.stderr,
        )
        sys.exit(1)

    chunk_size = read_setting("CHUNK_SIZE", default=500, minimum=1)
    overlap = read_setting("CHUNK_OVERLAP", default=1, minimum=0)

    if dry_run:
        book = Path(sys.argv[2]).expanduser()
        if not book.is_file():
            print(f"Not a file: {book}", file=sys.stderr)
            sys.exit(1)
        if sys.argv[1] == "--dry-run":
            print_chunks(book, chunk_size, overlap)
        else:
            print_embeddings(book, create_embedder(), chunk_size, overlap)
        return

    directory = Path(sys.argv[1]).expanduser() if len(sys.argv) == 2 else BOOKS_DIR
    if not directory.is_dir():
        print(f"Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    books = find_books(directory)
    if not books:
        print(f"No books found in {directory}", file=sys.stderr)
        sys.exit(1)

    started = time.perf_counter()
    embedder = create_embedder()
    collection = collection_name(embedder, chunk_size, overlap)

    total = 0
    for book in books:
        print(book.name)
        for chapter in range(get_number_of_chapters(str(book))):
            stored = store_chapter(
                str(book), book.name, chapter, embedder, collection, chunk_size, overlap
            )
            print(f"  Chapter {chapter}: {stored} chunks")
            total += stored

    print(f"Stored {total} chunks in Qdrant collection '{collection}'")
    minutes, seconds = divmod(round(time.perf_counter() - started), 60)
    print(f"Processed {len(books)} books in {minutes} min {seconds} s")


if __name__ == "__main__":
    main()
