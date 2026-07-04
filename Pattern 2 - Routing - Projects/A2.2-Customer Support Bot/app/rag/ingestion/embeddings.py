from langchain_huggingface import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={
        "device": "cpu",
    },
)
