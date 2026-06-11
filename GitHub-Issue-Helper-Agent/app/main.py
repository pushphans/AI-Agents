import logging

from fastapi import FastAPI

from app.api.router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("github-agent")

app = FastAPI(title="GitHub Issue Helper Agent")
app.include_router(router)


@app.get("/health")
async def health():
    logger.info("Health check")
    return {"status": "ok"}
