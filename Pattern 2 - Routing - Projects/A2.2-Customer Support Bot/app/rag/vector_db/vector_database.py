from langchain_chroma import Chroma
from app.rag.ingestion.embeddings import embedder
from app.core.config import settings

chroma_db = Chroma(
    collection_name=settings.chroma_collection_name,
    embedding_function=embedder,
    persist_directory=settings.chroma_persist_dir,
)
