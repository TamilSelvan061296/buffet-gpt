from pathlib import Path
import logging

from langchain_community.document_loaders import BSHTMLLoader
from langchain_core.documents import Document
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class HtmlLoader:
    """
    Given the html path folder, Uses langchain's document loader methods to load all
    the html files recursively into documents.
    """
    def __init__(self, html_path: str):
        self.html_folder_path = html_path

    def load_html_files(self) -> list[Document]:
        docs: list[Document] = []
        for path in sorted(Path(self.html_folder_path).rglob("*.html")):
            try:
                loader = BSHTMLLoader(str(path), open_encoding="windows-1252")
                for doc in loader.load():
                    doc.metadata["year"] = int(path.stem)
                    docs.append(doc)
            except:
                logger.error(f"Error while parsing {path}")
        return docs

class PdfLoader:
    """
    Given the pdf path folder, Uses langchain's document loader methods to load all
    the path files recursively into documents.
    """
    def __init__(self, pdf_path):
        self.pdf_folder_path = pdf_path

    def load_pdf_files(self) -> list[Document]:
        docs: list[Document] = []
        for path in sorted(Path(self.pdf_folder_path).rglob("*.pdf")):
            try:
                loader = PyMuPDF4LLMLoader(str(path), mode="single")
                for doc in loader.load():
                    doc.metadata["year"] = int(path.stem)
                    docs.append(doc)
            except:
                logger.error(f"Error while parsing {path}")
        return docs


class Chunker:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_docs(self, docs: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True,
        )

        all_chunks = text_splitter.split_documents(docs)

        return all_chunks