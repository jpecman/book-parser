import time
from pathlib import Path

from book_parser.chunking import split_into_chunks
from book_parser.embed import Embedder
from book_parser.extract import get_number_of_chapters, read_chapter
from book_parser.ingest import collection_name
from book_parser.settings import ChunkSettings


def print_chunks(book: Path, settings: ChunkSettings) -> None:
    total = 0
    for chapter in range(get_number_of_chapters(str(book))):
        chunks = split_into_chunks(
            read_chapter(str(book), chapter), settings.size, settings.overlap
        )
        print(f"Chapter {chapter}: {len(chunks)} chunks")
        for index, chunk in enumerate(chunks):
            print(f"  {index} [{len(chunk)}] {chunk}")
        total += len(chunks)
    print(f"{total} chunks, nothing embedded or stored")


def print_embeddings(book: Path, embedder: Embedder, settings: ChunkSettings) -> None:
    total = 0
    embed_seconds = 0.0
    for chapter in range(get_number_of_chapters(str(book))):
        chunks = split_into_chunks(
            read_chapter(str(book), chapter), settings.size, settings.overlap
        )
        embed_started = time.perf_counter()
        vectors = embedder.embed(chunks) if chunks else []
        duration = time.perf_counter() - embed_started
        size = len(vectors[0]) if vectors else 0
        print(
            f"Chapter {chapter}: {len(chunks)} chunks, vector size {size} "
            f"({duration:.1f} s)"
        )
        total += len(chunks)
        embed_seconds += duration
    collection = collection_name(embedder, settings)
    print(f"Embedded {total} chunks for collection '{collection}', nothing stored")
    print(f"Embedding took {embed_seconds:.1f} s in total")
