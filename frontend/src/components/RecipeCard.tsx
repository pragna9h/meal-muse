import type { Recipe } from "../types/chat";

interface RecipeCardProps {
  recipe: Recipe;
  ingredientsAvailable: string[];
  onSelect: (recipeId: string) => void;
}

export default function RecipeCard({ recipe, ingredientsAvailable, onSelect }: RecipeCardProps) {

    const matchedIngredients = ingredientsAvailable.filter((ingredient) =>
        recipe.normalized_ingredients.some((recipeIngredient) =>
            recipeIngredient.includes(ingredient.toLowerCase())
        )
    );

    const ingredientPreview = recipe.normalized_ingredients.slice(0, 5);

  return (
    <article className="recipe-card clickable-card" onClick={() => onSelect(recipe.recipe_id)}>
      {/* <div className="recipe-card-visual">
        <span className="visual-monogram">
          {recipe.name.charAt(0).toUpperCase()}
        </span>

        {recipe.rating_value != null && (
          <span className="score-badge">
            ★ {recipe.rating_value.toFixed(1)}
          </span>
        )}
      </div> */}

      <div className="recipe-card-body">
        <div className="recipe-title-row">
            <h3>{recipe.name}</h3>

            {recipe.rating_value != null && (
            <span className="score-badge">
                ★ {recipe.rating_value.toFixed(1)}
            </span>
            )}
        </div>

        {matchedIngredients.length > 0 ? (
            <p className="recipe-description">
                Uses ingredients you have: {matchedIngredients.join(", ")}.
            </p>
            ) : ingredientPreview.length > 0 ? (
            <p className="recipe-description">
                Ingredients: {ingredientPreview.join(", ")}
                {recipe.normalized_ingredients.length > 5 ? ", ..." : "."}
            </p>
        ) : null}

        <div className="recipe-meta">
          {recipe.total_time_minutes != null &&
            recipe.total_time_minutes > 0 && (
              <span>{recipe.total_time_minutes} min</span>
            )}

          {recipe.servings != null && (
            <span>{recipe.servings} servings</span>
          )}

          {recipe.nutrition?.calories != null && (
            <span>{Math.round(recipe.nutrition.calories)} cal</span>
          )}
        </div>

        {recipe.cuisines.length > 0 && (
        <p className="recipe-match">
            {recipe.cuisines
            .map(
                (cuisine) =>
                cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
            )
            .join(", ")}
        </p>
        )}

        {recipe.source_url && (
          <a
            href={recipe.source_url} target="_blank"
            rel="noreferrer" className="recipe-link" 
            onClick={(event) => event.stopPropagation()}
          >
            View recipe →
          </a>
        )}
      </div>
    </article>
  );
}