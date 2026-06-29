import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.router import router
from pydantic import ValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Finance Tracker Agent")


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(include_url=False)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


app.include_router(router=router)
