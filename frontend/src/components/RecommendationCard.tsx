import type { MealRecommendation } from "../types/chat";

interface RecommendationCardProps {
  recommendation: MealRecommendation;
  onSelect: (recipeId: string) => void;
}

export default function RecommendationCard({
  recommendation, onSelect,
}: RecommendationCardProps) {
  return (
    <article className="recipe-card clickable-card" onClick={() => onSelect(recommendation.recipe_id)}>
      {/* <div className="recipe-card-visual">
        <span className="visual-monogram">
          {recommendation.name.charAt(0).toUpperCase()}
        </span>

        <span className="score-badge">
          ★ {recommendation.score.toFixed(1)}
        </span>
      </div> */}

      <div className="recipe-card-body">
        <div className="recipe-title-row">
            <h3>{recommendation.name}</h3>

            {recommendation.rating_value != null && (
                <span className="score-badge">
                    ★ {recommendation.rating_value.toFixed(1)}
                </span>
            )}
        </div>

        {recommendation.reason && (
          <p className="recipe-description">{recommendation.reason}</p>
        )}

        <div className="recipe-meta">
          {recommendation.total_time_minutes != null && (
            <span>{recommendation.total_time_minutes} min</span>
          )}

          {recommendation.calories != null && (
            <span>{Math.round(recommendation.calories)} cal</span>
          )}

          {recommendation.protein_g != null && (
            <span>{Math.round(recommendation.protein_g)}g protein</span>
          )}
        </div>

        {recommendation.matched_ingredients.length > 0 && (
          <p className="recipe-match">
            Matches: {recommendation.matched_ingredients.join(", ")}
          </p>
        )}

        {recommendation.source_url && (
          <a href={recommendation.source_url}
            target="_blank" rel="noreferrer"
            className="recipe-link" onClick={(event) => event.stopPropagation()}
            >
            View recipe →
          </a>
        )}
      </div>
    </article>
  );
}