from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Natural-language meal recommendation request from the user",
    )


class ParsedIntent(BaseModel):
    
    ingredients_available: List[str] = []
    ingredients_required: List[str] = []
    ingredients_excluded: List[str] = []

    meal_type: Optional[str] = None

    dietary_preferences: List[str] = []
    allergies: List[str] = []
    cuisine_preferences: List[str] = []
    nutrition_goals: List[str] = []

    max_prep_minutes: Optional[int] = None
    servings: Optional[int] = None

    taste_preferences: List[str] = []
    equipment_available: List[str] = []

    budget_level: Optional[str] = None
    skill_level: Optional[str] = None

    allow_substitutions: Optional[bool] = None

    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    
    @field_validator(
        "ingredients_available",
        "ingredients_required",
        "ingredients_excluded",
    )
    
    @classmethod
    def normalize_ingredients(cls, ingredients: List[str]) -> List[str]:
        return [ingredient.strip().lower() for ingredient in ingredients]


class MealRecommendation(BaseModel):
    recipe_id: str
    name: str

    score: float

    total_time_minutes: Optional[int] = None

    calories: Optional[float] = None
    protein_g: Optional[float] = None

    matched_ingredients: List[str] = []
    missing_ingredients: List[str] = []

    reason: str

    source_url: Optional[str] = None


class ChatResponse(BaseModel):
    parsed_intent: ParsedIntent
    recommendations: List[MealRecommendation]