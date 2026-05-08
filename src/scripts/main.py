import logging
from pathlib import Path

import yaml
from langchain_core.documents import Document

from data_ingestor import HtmlLoader, PdfLoader, Chunker
from embedder import Embedder
from buffet_vector_store import BuffetVectorStore

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/app.log',
    filemode='w'
)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    paths = config["data_folder_paths"]
    chunking = config["chunking"]
    embeddings_cfg = config["embeddings"]
    vector_store_cfg = config["vector_store"]

    docs: list[Document] = []

    # load the html docs
    logging.info("Loading HTML files..")
    html = HtmlLoader(paths["html_folder_path"])
    html_docs = html.load_html_files()
    docs.extend(html_docs)

    # load the pdf docs
    logging.info("Loading PDF files")
    pdf = PdfLoader(paths["pdf_folder_path"])
    pdf_docs = pdf.load_pdf_files()
    docs.extend(pdf_docs)

    # chunk the docs
    logging.info("Creating chunks")
    c = Chunker(
        chunk_size=chunking["chunk_size"],
        chunk_overlap=chunking["chunk_overlap"],
    )
    chunks = c.chunk_docs(docs=docs)

    # embed the docs
    logging.info("Embedding chunks")
    embedder = Embedder(model=embeddings_cfg["model"])
    vectors = embedder.embed_chunks(chunks)

    # store the embeddings in the vector store
    logging.info("Storing embeddings in vector store")
    vector_store = BuffetVectorStore(
        path=vector_store_cfg["path"],
        collection_name=vector_store_cfg["collection_name"],
        vector_size=vector_store_cfg["vector_size"],
        embeddings=embedder.embeddings,
    )
    vector_store.store_embeddings(chunks, vectors)



if __name__ == "__main__":
    main()
