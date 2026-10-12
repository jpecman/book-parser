import os
from typing import Protocol


def split_into_chunks(text: str, max_chars: int = 500) -> list[str]:
    chunks: list[str] = []
    current = ""
    for word in text.split():
        if current and len(current) + 1 + len(word) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        chunks.append(current)
    return chunks


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class AzureEmbedder:
    name = "azure"

    def __init__(self) -> None:
        # in python imports are statements that runs, hence it is only here
        from langchain_openai import AzureOpenAIEmbeddings

        # Endpoint, key and API version are read from AZURE_OPENAI_ENDPOINT,
        # AZURE_OPENAI_API_KEY and OPENAI_API_VERSION.
        self._model = AzureOpenAIEmbeddings(
            azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._model.embed_documents(texts)


class FastEmbedEmbedder:
    name = "fastembed"

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.embed(texts)]


def create_embedder() -> Embedder:
    provider = os.environ.get("EMBEDDING_PROVIDER", "azure")
    if provider == "azure":
        return AzureEmbedder()
    if provider == "fastembed":
        return FastEmbedEmbedder()
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")
