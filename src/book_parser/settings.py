import os
from dataclasses import dataclass

from book_parser.errors import BookParserError


@dataclass(frozen=True)
class ChunkSettings:
    size: int
    overlap: int


def load_chunk_settings() -> ChunkSettings:
    return ChunkSettings(
        size=_read_int("CHUNK_SIZE", default=500, minimum=1),
        overlap=_read_int("CHUNK_OVERLAP", default=1, minimum=0),
    )


def _read_int(name: str, default: int, minimum: int) -> int:
    raw = os.environ.get(name, str(default))
    if not raw.isdecimal() or int(raw) < minimum:
        raise BookParserError(
            f"{name} must be a whole number of at least {minimum}, got '{raw}'"
        )
    return int(raw)
