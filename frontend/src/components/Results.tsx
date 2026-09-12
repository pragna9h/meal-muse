import type { ChatResponse } from "../types/chat";
import RecommendationCard from "./RecommendationCard";
import RecipeCard from "./RecipeCard";

interface ResultsProps {
  response: ChatResponse | null;
  onSelectRecipe: (recipeId: string) => void;
}

export default function Results({ response, onSelectRecipe }: ResultsProps) {
  if (!response) {
    return null;
  }

  if (response.result_state === "clarification_required") {
    return (
      <section className="status-panel">
        <p>
          {response.message ??
            response.parsed_intent.clarification_question}
        </p>
      </section>
    );
  }

  if (response.result_state === "no_results") {
    return (
      <section className="status-panel">
        <p>
          {response.message ??
            "MealMuse could not find a matching recipe for that request."}
        </p>
      </section>
    );
  }

  if (response.result_state === "failure") {
    return (
      <section className="status-panel error-panel">
        <p>
          {response.message ??
            "MealMuse could not complete the request right now."}
        </p>
      </section>
    );
  }

  if (response.parsed_intent.intent === "meal_recommendation") {
    return (
      <section className="results-section">
        <div className="results-heading-row">
          <div>
            <p className="eyebrow">Recommended for you</p>
            <h2>Recipes for you</h2>
          </div>

          <span className="result-count">
            {response.recommendations.length} recipes
          </span>
        </div>

        <div className="results-grid">
          {response.recommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation.recipe_id}
              recommendation={recommendation}
              onSelect={onSelectRecipe}
            />
          ))}
        </div>
      </section>
    );
  }

  if (response.parsed_intent.intent === "recipe_search") {
    return (
      <section className="results-section">
        <div className="results-heading-row">
          <div>
            <p className="eyebrow">Recipe search</p>
            <h2>Recipes for you</h2>
          </div>

          <span className="result-count">
            {response.recipes.length} recipes
          </span>
        </div>

        <div className="results-grid">
          {response.recipes.map((recipe) => (
            <RecipeCard key={recipe.recipe_id} 
                        recipe={recipe} 
                        ingredientsAvailable={response.parsed_intent.ingredients_available}
                        onSelect={onSelectRecipe} />
          ))}
        </div>
      </section>
    );
  }

  return null;
}