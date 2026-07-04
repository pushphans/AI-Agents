from langchain_core.documents import Document
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.vector_db.vector_database import chroma_db


async def get_chunks(file_path: str, source: str) -> list[Document]:
    pdf_file = PdfReader(file_path)
    doc = []

    for page_number, page in enumerate(pdf_file.pages):
        text = page.extract_text()
        if text:
            document = Document(
                page_content=text,
                metadata={"page_number": page_number + 1, "source": source},
            )
            doc.append(document)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
    )
    chunks: list[Document] = text_splitter.split_documents(doc)
    return chunks


async def make_embeddings(chunks: list[Document]):
    await chroma_db.aadd_documents(chunks)
