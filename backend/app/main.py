import logging
from backend.app.config.logging import configure_logging
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from backend.app.middleware.request_context import request_context_middleware
from backend.app.config.settings import get_settings
from backend.app.api.chat import router as chat_router
from backend.app.api.recipes import router as recipes_router
from backend.app.database.connection import engine

settings = get_settings()

configure_logging()
logger = logging.getLogger(__name__)

logger.info(
    "MealMuse API configured",
    extra={"app_env": settings.app_env},
)

app = FastAPI(
    title="MealMuse API",
    description="Agentic AI-powered meal planning platform",
    version="0.1.0",
)

app.middleware("http")(request_context_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "meal-muse-api",
    }

@app.get("/ready")
def readiness_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Readiness check failed")
        raise HTTPException(
            status_code=503,
            detail="Service is not ready.",
        ) from exc

    return {
        "status": "ready",
        "database": "connected",
    }


app.include_router(chat_router)
app.include_router(recipes_router)