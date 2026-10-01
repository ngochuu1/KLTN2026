from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from sqlalchemy import text

from app.api.v1.router import router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.exception_handlers import (
    app_error_handler, http_error_handler, unexpected_error_handler, validation_error_handler,
)
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        yield
    finally:
        await engine.dispose()


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_url).rstrip("/")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router)
