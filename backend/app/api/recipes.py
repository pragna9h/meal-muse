from fastapi import APIRouter, HTTPException, status

from backend.app.models.recipe import Recipe
from backend.app.repositories.recipe_repository import get_recipes_by_ids

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: str):
    recipes = get_recipes_by_ids([recipe_id])

    if not recipes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found.",
        )

    return recipes[0]