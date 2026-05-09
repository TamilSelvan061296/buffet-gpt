import logging
import uuid

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_voyageai import VoyageAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logger = logging.getLogger(__name__)


class BuffetVectorStore:
    """
    Wraps a Qdrant vector store for the Buffett corpus. Creates the collection
    if it doesn't exist and exposes a method to store chunk embeddings.
    """
    def __init__(
        self,
        path: str,
        collection_name: str,
        vector_size: int,
        embeddings: VoyageAIEmbeddings,
    ):
        self.client = QdrantClient(path=path)
        self.collection_name = collection_name

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=embeddings,
        )

    def store_embeddings(
        self, chunks: list[Document], vectors: list[list[float]]
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
