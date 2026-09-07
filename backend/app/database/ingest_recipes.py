import json

from sqlalchemy import text

from backend.app.database.connection import engine
from backend.app.services.recipe_store import load_recipes


INSERT_RECIPE_SQL = text(
    """
    INSERT INTO recipes (
        recipe_id, name, description, ingredients, ingredients_raw,
        normalized_ingredients, instructions, prep_time_minutes,
        cook_time_minutes, total_time_minutes, servings, serving_description,
        categories, cuisines, cooking_methods, equipment,
        calories, protein_g, carbs_g, fat_g, saturated_fat_g, 
        fiber_g, sugar_g, sodium_mg,cholesterol_mg, rating_value, 
        rating_count, source_url, search_text
    )
    VALUES (
        :recipe_id, :name, :description, CAST(:ingredients AS JSONB),
        CAST(:ingredients_raw AS JSONB), :normalized_ingredients, CAST(:instructions AS JSONB),
        :prep_time_minutes, :cook_time_minutes, :total_time_minutes, :servings,
        :serving_description, :categories, :cuisines, :cooking_methods,
        :equipment, :calories, :protein_g, :carbs_g, :fat_g, :saturated_fat_g,
        :fiber_g, :sugar_g, :sodium_mg, :cholesterol_mg, :rating_value, :rating_count, 
        :source_url, :search_text
    )
    ON CONFLICT (recipe_id) DO NOTHING
    """
)


def build_search_text(recipe) -> str:
    parts = [
        recipe.name,
        " ".join(recipe.normalized_ingredients),
        " ".join(recipe.categories),
        " ".join(recipe.cuisines),
        " ".join(recipe.cooking_methods),
    ]

    return " | ".join(part for part in parts if part)


def recipe_to_row(recipe) -> dict:
    return {
        "recipe_id": recipe.recipe_id,
        "name": recipe.name,
        "description": recipe.description,
        "ingredients": json.dumps(
            [ingredient.model_dump() for ingredient in recipe.ingredients]
        ),
        "ingredients_raw": json.dumps(recipe.ingredients_raw),
        "normalized_ingredients": recipe.normalized_ingredients,
        "instructions": json.dumps(recipe.instructions),
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "total_time_minutes": recipe.total_time_minutes,
        "servings": recipe.servings,
        "serving_description": recipe.serving_description,
        "categories": recipe.categories,
        "cuisines": recipe.cuisines,
        "cooking_methods": recipe.cooking_methods,
        "equipment": recipe.equipment,
        "calories": recipe.nutrition.calories,
        "protein_g": recipe.nutrition.protein_g,
        "carbs_g": recipe.nutrition.carbs_g,
        "fat_g": recipe.nutrition.fat_g,
        "saturated_fat_g": recipe.nutrition.saturated_fat_g,
        "fiber_g": recipe.nutrition.fiber_g,
        "sugar_g": recipe.nutrition.sugar_g,
        "sodium_mg": recipe.nutrition.sodium_mg,
        "cholesterol_mg": recipe.nutrition.cholesterol_mg,
        "rating_value": recipe.rating_value,
        "rating_count": recipe.rating_count,
        "source_url": str(recipe.source_url) if recipe.source_url else None,
        "search_text": build_search_text(recipe),
    }


def ingest_recipes() -> None:
    recipes = load_recipes()
    rows = [recipe_to_row(recipe) for recipe in recipes]

    print(f"Loaded {len(rows):,} recipes for ingestion.")

    with engine.begin() as connection:
        connection.execute(INSERT_RECIPE_SQL, rows)

    print("Recipe ingestion completed.")


if __name__ == "__main__":
    ingest_recipes()