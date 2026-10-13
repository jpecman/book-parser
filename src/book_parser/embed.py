import os
import re
from typing import Protocol

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


class Embedder(Protocol):
    name: str
    model_name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class AzureEmbedder:
    name = "azure"

    def __init__(self) -> None:
        # in python imports are statements that runs, hence it is only here
        from langchain_openai import AzureOpenAIEmbeddings

        # The deployment name stands in for the model name: it is all we know.
        self.model_name = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
        # Endpoint, key and API version are read from AZURE_OPENAI_ENDPOINT,
        # AZURE_OPENAI_API_KEY and OPENAI_API_VERSION.
        self._model = AzureOpenAIEmbeddings(azure_deployment=self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)


class FastEmbedEmbedder:
    name = "fastembed"
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


class OllamaEmbedder:
    name = "ollama"

    def __init__(self) -> None:
        from langchain_ollama import OllamaEmbeddings

        self.model_name = os.environ["OLLAMA_EMBEDDING_MODEL"]
        self._model = OllamaEmbeddings(
            model=self.model_name,
            base_url=os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)


def create_embedder() -> Embedder:
    provider = os.environ.get("EMBEDDING_PROVIDER", "azure")
    if provider == "azure":
        return AzureEmbedder()
    if provider == "fastembed":
        return FastEmbedEmbedder()
    if provider == "ollama":
        return OllamaEmbedder()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")
