import os
from typing import Protocol

from book_parser.errors import BookParserError


class Lemmatizer(Protocol):
    name: str

    # Base forms of the words in text, lowercased, without punctuation.
    def lemmatize(self, text: str) -> list[str]: ...


class MorphoDitaLemmatizer:
    name = "morphodita"

    def __init__(self, tagger_path: str) -> None:
        from ufal.morphodita import Tagger

        self._tagger = Tagger.load(tagger_path)
        if self._tagger is None:
            raise BookParserError(f"Cannot load MorphoDiTa tagger from {tagger_path}")
        self._morpho = self._tagger.getMorpho()

    def lemmatize(self, text: str) -> list[str]:
        from ufal.morphodita import Forms, TaggedLemmas, TokenRanges

        tokenizer = self._tagger.newTokenizer()
        tokenizer.setText(text)
        forms, lemmas, ranges = Forms(), TaggedLemmas(), TokenRanges()
        result: list[str] = []
        while tokenizer.nextSentence(forms, ranges):
            self._tagger.tag(forms, lemmas)
            # Tags starting with Z mark punctuation. rawLemma strips the
            # technical suffixes, e.g. "Praha_;G" becomes "Praha".
            result.extend(
                self._morpho.rawLemma(lemma.lemma).lower()
                for lemma in lemmas
                if not lemma.tag.startswith("Z")
            )
        return result


def create_lemmatizer() -> Lemmatizer:
    provider = os.environ.get("LEMMATIZER", "morphodita")
    if provider == "morphodita":
        tagger_path = os.environ.get("MORPHODITA_TAGGER")
        if not tagger_path:
            raise BookParserError("MORPHODITA_TAGGER must point to a .tagger model file")
        return MorphoDitaLemmatizer(os.path.expanduser(tagger_path))
    raise BookParserError(f"Unknown LEMMATIZER: {provider}")
