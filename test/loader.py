from langchain_community.document_loaders import BSHTMLLoader
from langchain_pymupdf4llm import PyMuPDF4LLMLoader

loader = BSHTMLLoader(
    "/home/tamil/work/skunkworks/buffet-gpt/src/buffet_sink/html/1977.html",
    open_encoding="windows-1252",
)
docs = loader.load()

# print(docs)
# print(docs[0].page_content)
# print(docs[0].metadata)

loader_pdf = PyMuPDF4LLMLoader("/home/tamil/work/skunkworks/buffet-gpt/src/buffet_sink/pdf/2007.pdf",
                               mode="single")
docs_pdf = loader_pdf.load()

print(len(docs_pdf))
# print(docs_pdf[0].page_content)
print(docs_pdf[0].metadata)