import type { Recipe } from "../types/chat";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getRecipeById(recipeId: string): Promise<Recipe> {
  const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}`);

  if (!response.ok) {
    let detail = "MealMuse could not load this recipe.";

    try {
      const errorBody = await response.json();

      if (typeof errorBody.detail === "string") {
        detail = errorBody.detail;
      }
    } catch {
      // Keep fallback message.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<Recipe>;
}