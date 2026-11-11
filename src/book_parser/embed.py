import os
from typing import Protocol


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
