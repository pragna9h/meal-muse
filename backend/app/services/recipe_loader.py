import ast
import json
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from backend.app.models.recipe import Ingredient, Nutrition, Recipe


RAW_DATA_PATH = Path("data/raw/recipes_heavy_dataset.xlsx")
PROCESSED_DATA_PATH = Path("data/processed/recipes.json")


def parse_literal(value: Any, default: Any):
    """
    Safely parse strings that contain Python-style lists/dictionaries.

    Example:
        "['Indian', 'Asian']"
        ->
        ['Indian', 'Asian']
    """
    if value is None:
        return default

    if isinstance(value, float) and pd.isna(value):
        return default

    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return default

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return default


def parse_float(value: Any) -> Optional[float]:
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int(value: Any) -> Optional[int]:
    if value is None or pd.isna(value):
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None

def parse_time_minutes(value: Any) -> Optional[int]:
    parsed = parse_int(value)

    if parsed is None or parsed <= 0:
        return None

    return parsed

def parse_ingredients(value: Any) -> List[Ingredient]:
    raw_ingredients = parse_literal(value, default=[])

    ingredients = []

    for item in raw_ingredients:
        if not isinstance(item, dict):
            continue

        ingredient_name = item.get("ingredient")

        if not ingredient_name:
            continue

        ingredients.append(
            Ingredient(
                name=ingredient_name,
                quantity=item.get("quantity") or None,
                unit=item.get("unit") or None,
                misc=item.get("misc") or None,
            )
        )

    return ingredients


def parse_nutrition(value: Any) -> Nutrition:
    nutrition_data = parse_literal(value, default={})

    def extract_number(field_name: str) -> Optional[float]:
        raw_value = nutrition_data.get(field_name)

        if raw_value is None:
            return None

        raw_text = str(raw_value).strip()

        if not raw_text:
            return None

        parts = raw_text.split()

        if not parts:
            return None

        try:
            return float(parts[0])
        except (ValueError, TypeError):
            return None

    return Nutrition(
        calories=extract_number("Calories"),
        protein_g=extract_number("Protein"),
        carbs_g=extract_number("Carbohydrates"),
        fat_g=extract_number("Fat"),
        saturated_fat_g=extract_number("Saturated Fat"),
        fiber_g=extract_number("Fiber"),
        sugar_g=extract_number("Sugar"),
        sodium_mg=extract_number("Sodium"),
        cholesterol_mg=extract_number("Cholesterol"),
    )


def parse_servings(value: Any) -> tuple[Optional[int], Optional[str]]:
    parsed = parse_literal(value, default=value)

    if isinstance(parsed, list):
        serving_count = parse_int(parsed[0]) if parsed else None
        serving_description = str(parsed[1]) if len(parsed) > 1 else None

        return serving_count, serving_description

    return parse_int(parsed), None


def row_to_recipe(row: pd.Series, index: int) -> Recipe:
    ingredients = parse_ingredients(row["Ingredients"])

    normalized_ingredients = [
        ingredient.name
        for ingredient in ingredients
    ]

    ingredients_raw = parse_literal(
        row["Ingredients_Raw"],
        default=[],
    )

    instructions = parse_literal(
        row["Instructions"],
        default=[],
    )

    categories = parse_literal(
        row["Category"],
        default=[],
    )

    cuisines = parse_literal(
        row["Cuisine"],
        default=[],
    )

    cooking_methods = parse_literal(
        row["Cooking Methods"],
        default=[],
    )

    equipment = parse_literal(
        row["Implements"],
        default=[],
    )

    servings, serving_description = parse_servings(
        row["Servings"]
    )

    prep_time = parse_time_minutes(row["Preparation Time"])
    cook_time = parse_time_minutes(row["Cooking Time"])
        
    total_time = None

    if prep_time is not None or cook_time is not None:
        total_time = ((prep_time or 0)+ (cook_time or 0))

    return Recipe(
        recipe_id=f"recipe_{index:06d}",
        name=str(row["Name"]).strip(),
        ingredients=ingredients,
        ingredients_raw=ingredients_raw,
        normalized_ingredients=normalized_ingredients,
        instructions=instructions,
        prep_time_minutes=prep_time,
        cook_time_minutes=cook_time,
        total_time_minutes=total_time,
        servings=servings,
        serving_description=serving_description,
        categories=categories,
        cuisines=cuisines,
        cooking_methods=cooking_methods,
        equipment=equipment,
        nutrition=parse_nutrition(row["Nutrition"]),
        rating_value=parse_float(row["Rating Value"]),
        rating_count=parse_int(row["Rating Count"]),
        source_url=row["URL"] if pd.notna(row["URL"]) else None,
    )


def load_first_recipe() -> Recipe:
    dataframe = pd.read_excel(RAW_DATA_PATH)

    first_row = dataframe.iloc[0]

    return row_to_recipe(first_row, index=1)

def load_all_recipes() -> tuple[list[Recipe], list[dict]]:
    dataframe = pd.read_excel(RAW_DATA_PATH)

    recipes: list[Recipe] = []
    errors: list[dict] = []

    for index, row in dataframe.iterrows():
        try:
            recipe = row_to_recipe(
                row,
                index=index + 1,
            )
            recipes.append(recipe)

        except Exception as exc:
            errors.append(
                {
                    "row_number": index + 2,
                    "recipe_name": row.get("Name"),
                    "error": str(exc),
                }
            )

    return recipes, errors

def save_processed_recipes(recipes: list[Recipe]) -> None:
    PROCESSED_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized_recipes = [
        recipe.model_dump(mode="json")
        for recipe in recipes
    ]

    with PROCESSED_DATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            serialized_recipes,
            file,
            indent=2,
            ensure_ascii=False,
        )

if __name__ == "__main__":
    recipes, errors = load_all_recipes()

    print(f"Successfully loaded: {len(recipes)}")
    print(f"Failed to load: {len(errors)}")

    if errors:
        print("\nFirst 10 errors:")

        for error in errors[:10]:
            print(error)
    
    save_processed_recipes(recipes)

    print(
        f"Saved processed recipes to: "
        f"{PROCESSED_DATA_PATH}"
    )