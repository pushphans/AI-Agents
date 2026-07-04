from langchain_core.documents import Document

from app.rag.vector_db.vector_database import chroma_db


async def retrieve_data(query: str, k=5) -> str:
    docs: list[Document] = await chroma_db.asimilarity_search(query, k=k)
    result = ""
    for d in docs:
        result = result + d.page_content + "\n\n"
    return result
 