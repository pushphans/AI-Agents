import asyncio

from app.rag.ingestion.ingestion import get_chunks, make_embeddings


async def run_ingestion():
    file_path = "app/sample_data/test_data.pdf"

    chunks = await get_chunks(file_path=file_path, source="test_data.pdf")

    await make_embeddings(chunks=chunks)
    print(f"Done → {len(chunks)} chunks stored in ChromaDB")



asyncio.run(run_ingestion())