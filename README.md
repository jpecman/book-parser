# book-parser

A learning exercise for trying out vector databases. It reads text from books (PDF, EPUB and similar formats) with PyMuPDF, with the goal of storing it in a vector database and searching it.

## Requirements

- Nix with flakes enabled
- Podman or Docker, to run the database

## Running

Enter the development shell from the project root:

```sh
nix develop
python -m book_parser my-book.epub
```

