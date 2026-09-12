import { useState } from "react";

import { sendChatMessage } from "./api/chat";
import ChatInput from "./components/ChatInput";
import Results from "./components/Results";
import type { ChatResponse, Recipe } from "./types/chat";
import { getRecipeById } from "./api/recipes";

import mealMuseIcon from "./assets/green_mealmuse_icon.png";
import breakfastBowl from "./assets/breakfast_bowl.png";
import lunchSalad from "./assets/salad.png";
import dinnerPasta from "./assets/pasta.png";
import dessertChocolate from "./assets/chocolate.png";

import "./App.css";

export default function App() {
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isRecipeLoading, setIsRecipeLoading] = useState(false);
  const [recipeError, setRecipeError] = useState<string | null>(null);

  async function handleSubmit(message: string) {
    setIsLoading(true);
    setError(null);
    setResponse(null);
    setSelectedRecipe(null);
    setRecipeError(null);

    try {
      const data = await sendChatMessage(message);
      setResponse(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("MealMuse could not complete the request.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSelectRecipe(recipeId: string) {
  setIsRecipeLoading(true);
  setRecipeError(null);

  try {
    const recipe = await getRecipeById(recipeId);
    setSelectedRecipe(recipe);
  } catch (err) {
    if (err instanceof Error) {
      setRecipeError(err.message);
    } else {
      setRecipeError("MealMuse could not load this recipe.");
    }
  } finally {
    setIsRecipeLoading(false);
  }
}

  return (
    <main className="app-shell">
      <header className="site-header">
        <div className="brand-lockup">
          <img src={mealMuseIcon} alt="MealMuse icon" className="brand-mark"/>

          <div>
            <div className="brand-name">MealMuse</div>
            <div className="brand-tagline">Cook with what you have</div>
          </div>
        </div>
      </header>

      <div className="food-decorations" aria-hidden="true">
        <img
          src={breakfastBowl}
          alt=""
          className="food-decoration food-breakfast"
        />

        <img
          src={lunchSalad}
          alt=""
          className="food-decoration food-lunch"
        />

        <img
          src={dinnerPasta}
          alt=""
          className="food-decoration food-dinner"
        />

        <img
          src={dessertChocolate}
          alt=""
          className="food-decoration food-dessert"
        />
      </div>



      <section className="hero">
        <div className="decor decor-left">
          Good food,
          <br />
          better days
        </div>

        <div className="decor decor-right">
          Meals that fit
          <br />
          our lifestyle
        </div>

        <h1>What should we cook today?</h1>

        <p className="hero-copy">
          Tell me what's in your kitchen, what you're craving, or find a recipe.
        </p>

        <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
      </section>

      {error && (
        <section className="status-panel error-panel">
          <p>{error}</p>
        </section>
      )}

      <Results response={response} onSelectRecipe={handleSelectRecipe} />

      {isRecipeLoading && (
        <section className="status-panel">
          <p>Loading recipe...</p>
        </section>
      )}

      {recipeError && (
        <section className="status-panel error-panel">
          <p>{recipeError}</p>
        </section>
      )}

      {selectedRecipe && (
        <section className="recipe-detail">
          <div className="recipe-detail-header">
            <div>
              <p className="eyebrow">Recipe details</p>
              <h2>{selectedRecipe.name}</h2>
            </div>

            <button
              type="button"
              className="detail-close"
              onClick={() => setSelectedRecipe(null)}
            >
              Close
            </button>
          </div>

          <div className="recipe-detail-meta">
            {selectedRecipe.total_time_minutes != null &&
              selectedRecipe.total_time_minutes > 0 && (
                <span>{selectedRecipe.total_time_minutes} min</span>
              )}

            {selectedRecipe.servings != null && (
              <span>{selectedRecipe.servings} servings</span>
            )}

            {selectedRecipe.nutrition.calories != null && (
              <span>
                {Math.round(selectedRecipe.nutrition.calories)} cal
              </span>
            )}

            {selectedRecipe.nutrition.protein_g != null && (
              <span>
                {Math.round(selectedRecipe.nutrition.protein_g)}g protein
              </span>
            )}
          </div>

          {selectedRecipe.description && (
            <p className="recipe-detail-description">
              {selectedRecipe.description}
            </p>
          )}

          <div className="recipe-detail-grid">
            <div>
              <h3>Ingredients</h3>

              <ul>
                {selectedRecipe.ingredients.map((ingredient, index) => (
                  <li key={`${ingredient.name}-${index}`}>
                    {[
                      ingredient.quantity,
                      ingredient.unit,
                      ingredient.name,
                      ingredient.misc,
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3>Instructions</h3>

              <ol>
                {selectedRecipe.instructions.map((instruction, index) => (
                  <li key={`${instruction}-${index}`}>
                    {instruction}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {selectedRecipe.source_url && (
            <a
              href={selectedRecipe.source_url}
              target="_blank"
              rel="noreferrer"
              className="recipe-link"
            >
              View original recipe →
            </a>
          )}
        </section>
      )}
    </main>
  );
}