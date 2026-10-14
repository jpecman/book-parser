# book-parser

A learning exercise for trying out vector databases. It reads text from books (PDF, EPUB and similar formats) with PyMuPDF, with the goal of storing it in a vector database and searching it.

## Requirements

- Nix with flakes enabled
- Podman or Docker, to run the database

## Running

Enter the development shell from the project root:

```sh
nix develop
python -m book_parser ~/books
```

Every book in the directory is embedded; with no argument it reads `~/tmp/agent-books`. Chunking is set with environment variables, and each combination gets its own collection:

```sh
CHUNK_SIZE=800 CHUNK_OVERLAP=2 python -m book_parser ~/books
```

To skip some books, list their file names after `--exclude`, after the directory:

```sh
python -m book_parser ~/books --exclude dune.epub "Old notes.pdf"
```

To continue an interrupted run, start the first book at a later chapter, numbered from 0 as in the log. The books after it start from the beginning:

```sh
python -m book_parser ~/books --start-chapter 12
```

To see how one book would be chunked without embedding or storing anything:

```sh
python -m book_parser --dry-run ~/books/my-book.epub
```

To also run the chunks through the embedding model, still without storing anything:

```sh
python -m book_parser --dry-run-embed ~/books/my-book.epub
```

