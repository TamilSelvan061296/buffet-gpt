from pathlib import Path

from langchain_community.document_loaders import BSHTMLLoader
from langchain_core.documents import Document
from langchain_pymupdf4llm import PyMuPDF4LLMLoader


class html_loader:
    """
    Given the html path folder, Uses langchain's document loader methods to load all
    the html files recursively into documents.
    """
    def __init__(self, html_path: str):
        self.html_folder_path = html_path

    def load_html_files(self) -> list[Document]:
        docs: list[Document] = []
        for path in sorted(Path(self.html_folder_path).rglob("*.html")):
            loader = BSHTMLLoader(str(path), open_encoding="windows-1252")
            for doc in loader.load():
                doc.metadata["year"] = int(path.stem)
                docs.append(doc)
        return docs

class pdf_loader:
    """
    Given the pdf path folder, Uses langchain's document loader methods to load all
    the path files recursively into documents.
    """
    def __init__(self, pdf_path):
        self.pdf_folder_path = pdf_path

    def load_pdf_files(self) -> list[Document]:
        docs: list[Document] = []
        for path in sorted(Path(self.pdf_folder_path).rglob("*.pdf")):
            loader = PyMuPDF4LLMLoader(str(path), mode="single")
            for doc in loader.load():
                doc.metadata["year"] = int(path.stem)
                docs.append(doc)
        return docs
