import argparse
import sys
from pathlib import Path

from book_parser.books import BOOKS_DIR, exclude_books, find_books
from book_parser.dry_run import print_chunks, print_embeddings
from book_parser.embed import create_embedder
from book_parser.errors import BookParserError
from book_parser.ingest import ingest_books
from book_parser.settings import ChunkSettings, load_chunk_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m book_parser")
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        help=f"folder with books to embed (default: {BOOKS_DIR})",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        metavar="BOOK",
        help="file names of books in the folder to skip",
    )
    parser.add_argument(
        "--start-chapter",
        type=int,
        metavar="N",
        help="start the first book at chapter N, counted from 0 as in the log",
    )
    dry_runs = parser.add_mutually_exclusive_group()
    dry_runs.add_argument(
        "--dry-run",
        type=Path,
        metavar="BOOK",
        help="print how one book would be chunked, without embedding or storing",
    )
    dry_runs.add_argument(
        "--dry-run-embed",
        type=Path,
        metavar="BOOK",
        help="also embed the chunks of one book, still without storing",
    )
    args = parser.parse_args()

    dry_run = args.dry_run or args.dry_run_embed
    if dry_run and (args.directory or args.exclude or args.start_chapter is not None):
        parser.error(
            "a dry run takes a single book, not a directory, --exclude or --start-chapter"
        )
    if args.start_chapter is not None and args.start_chapter < 0:
        parser.error("--start-chapter must be 0 or more")
    return args


# The one place that turns expected errors into a message and exit code 1.
def main() -> None:
    args = parse_args()
    try:
        settings = load_chunk_settings()
        if args.dry_run or args.dry_run_embed:
            _dry_run(args, settings)
        else:
            _ingest(args, settings)
    except BookParserError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


def _dry_run(args: argparse.Namespace, settings: ChunkSettings) -> None:
    dry_run_book: Path = args.dry_run or args.dry_run_embed
    book = dry_run_book.expanduser()
    if not book.is_file():
        raise BookParserError(f"Not a file: {book}")
    if args.dry_run:
        print_chunks(book, settings)
    else:
        print_embeddings(book, create_embedder(), settings)


def _ingest(args: argparse.Namespace, settings: ChunkSettings) -> None:
    directory: Path = args.directory.expanduser() if args.directory else BOOKS_DIR
    if not directory.is_dir():
        raise BookParserError(f"Not a directory: {directory}")

    found = find_books(directory)
    if not found:
        raise BookParserError(f"No books found in {directory}")

    books, unmatched = exclude_books(found, args.exclude)
    for name in unmatched:
        print(f"Excluded book '{name}' is not in the directory", file=sys.stderr)
    if len(books) < len(found):
        print(f"Skipping {len(found) - len(books)} excluded books")
    if not books:
        raise BookParserError(f"All books in {directory} are excluded")

    ingest_books(books, settings, args.start_chapter or 0)
