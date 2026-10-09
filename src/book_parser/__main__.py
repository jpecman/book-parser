import sys
from pathlib import Path

from book_parser.extract import read_first_pages

BOOKS_DIR = Path("~/tmp/agent-books").expanduser()


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m book_parser <file.pdf>", file=sys.stderr)
        sys.exit(1)

    print(read_first_pages(str(BOOKS_DIR / sys.argv[1])))


if __name__ == "__main__":
    main()
