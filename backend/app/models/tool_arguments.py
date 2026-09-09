from typing import Optional

from pydantic import BaseModel, Field


class MealRecommendationToolArguments(BaseModel):
    ingredients_available: list[str] = Field(default_factory=list)
    ingredients_required: list[str] = Field(default_factory=list)
    ingredients_excluded: list[str] = Field(default_factory=list)

    meal_type: Optional[str] = None
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    cuisine_preferences: list[str] = Field(default_factory=list)
    nutrition_goals: list[str] = Field(default_factory=list)

    max_prep_minutes: Optional[int] = None
    servings: Optional[int] = None

    taste_preferences: list[str] = Field(default_factory=list)
    equipment_available: list[str] = Field(default_factory=list)

    budget_level: Optional[str] = None
    skill_level: Optional[str] = None
    allow_substitutions: Optional[bool] = None


class RecipeSearchToolArguments(BaseModel):
    recipe_query: Optional[str] = None