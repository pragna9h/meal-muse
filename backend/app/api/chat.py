from fastapi import APIRouter, HTTPException, status

from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.orchestration.chat_orchestrator import orchestrate_chat
from backend.app.orchestration.exceptions import (
    ToolExecutionError,
    ToolSelectionError,
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return orchestrate_chat(request.message)

    except ToolSelectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MealMuse could not understand the request.",
        ) from exc

    except ToolExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MealMuse could not complete the request right now.",
        ) from exc