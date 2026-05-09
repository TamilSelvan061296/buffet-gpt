import logging

from langchain_core.documents import Document
from langchain_voyageai import VoyageAIEmbeddings

logger = logging.getLogger(__name__)


class Embedder:
    """
    Wraps Voyage AI embeddings via LangChain. Given a list of chunks
    (Documents), returns their vector embeddings.
    """
    def __init__(self, model: str):
        self.model = model
        self.embeddings = VoyageAIEmbeddings(model=model)

    def embed_chunks(self, chunks: list[Document]) -> list[list[float]]:
        texts = [c.page_content for c in chunks]
        return self.embeddings.embed_documents(texts)
