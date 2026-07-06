from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ChatRequest, ChatResponse, chat_handler

app = FastAPI(
    title="E-Commerce Shopping Assistant",
    description="AI-powered multi-intent e-commerce assistant built with LangGraph",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "E-Commerce Shopping Assistant",
        "docs": "/docs",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await chat_handler(request)
