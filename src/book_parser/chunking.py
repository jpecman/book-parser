import re

# A sentence ends at . ! ? or … (optionally followed by a closing quote or
# bracket) when whitespace comes next.
_SENTENCE_END = re.compile(r'(?<=[.!?…])\s+|(?<=[.!?…]["”“’»)\]])\s+')


def split_into_sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_END.split(" ".join(text.split())) if s]


def _split_words(text: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for word in text.split():
        if current and len(current) + 1 + len(word) > max_chars:
            pieces.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        pieces.append(current)
    return pieces


def split_into_chunks(text: str, max_chars: int = 500, overlap: int = 1) -> list[str]:
    # A sentence longer than max_chars is cut at word boundaries.
    sentences: list[str] = []
    for sentence in split_into_sentences(text):
        if len(sentence) > max_chars:
            sentences.extend(_split_words(sentence, max_chars))
        else:
            sentences.append(sentence)

    chunks: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        if current and len(" ".join([*current, sentence])) > max_chars:
            chunks.append(" ".join(current))
            # Start the next chunk with the last sentences of this one,
            # dropping from the front whatever no longer fits.
            current = current[-overlap:] if overlap else []
            while current and len(" ".join([*current, sentence])) > max_chars:
                current.pop(0)
        current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks
