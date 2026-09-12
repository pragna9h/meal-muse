import type { ChatRequest, ChatResponse } from "../types/chat";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function sendChatMessage(
  message: string
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
  };

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
       "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "MealMuse could not connect right now. Please try again in a moment."
    );
  }

  if (!response.ok) {
    let detail = "MealMuse could not complete the request.";

    try {
      const errorBody = await response.json();

      if (typeof errorBody.detail === "string") {
        detail = errorBody.detail;
      }
    } catch {
      // Keep the fallback message if the response is not JSON.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<ChatResponse>;
}