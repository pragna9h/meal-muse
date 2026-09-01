import json
from functools import lru_cache
from pathlib import Path

from backend.app.models.recipe import Recipe


PROCESSED_DATA_PATH = Path("data/processed/recipes.json")


@lru_cache(maxsize=1)
def load_recipes() -> list[Recipe]:
    with PROCESSED_DATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_recipes = json.load(file)

    recipes = [
        Recipe.model_validate(recipe)
        for recipe in raw_recipes
    ]

    return recipes