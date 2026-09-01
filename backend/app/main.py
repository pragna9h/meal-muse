from fastapi import FastAPI

from backend.app.api.chat import router as chat_router


app = FastAPI(
    title="MealMuse API",
    description="Agentic AI-powered meal planning platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "meal-muse-api",
    }


app.include_router(chat_router)