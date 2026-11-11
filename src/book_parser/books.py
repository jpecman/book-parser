from pathlib import Path

BOOKS_DIR = Path("~/tmp/agent-books").expanduser()
BOOK_SUFFIXES = {".epub", ".mobi", ".fb2", ".pdf"}


def find_books(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in BOOK_SUFFIXES
    )


# Compares file names only, so a path from shell tab completion works too.
# Returns the remaining books and the excluded names that matched no book.
def exclude_books(books: list[Path], excluded: list[str]) -> tuple[list[Path], list[str]]:
    names = {Path(name).name for name in excluded}
    unmatched = sorted(names - {book.name for book in books})
    return [book for book in books if book.name not in names], unmatched
