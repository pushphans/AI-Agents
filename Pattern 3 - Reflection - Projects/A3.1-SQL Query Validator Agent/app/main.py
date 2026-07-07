from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="SQL Query Validator Agent",
    description="Natural language to validated SQL with reflection loop",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
