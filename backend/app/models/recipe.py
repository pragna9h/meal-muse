from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    misc: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, name: str) -> str:
        return name.strip().lower()


class Nutrition(BaseModel):
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    cholesterol_mg: Optional[float] = None


class Recipe(BaseModel):
    recipe_id: str

    name: str
    description: Optional[str] = None

    ingredients: List[Ingredient] = Field(default_factory=list)
    ingredients_raw: List[str] = Field(default_factory=list)
    normalized_ingredients: List[str] = Field(default_factory=list)

    instructions: List[str] = Field(default_factory=list)

    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None

    servings: Optional[int] = None
    serving_description: Optional[str] = None

    categories: List[str] = Field(default_factory=list)
    cuisines: List[str] = Field(default_factory=list)

    cooking_methods: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)

    nutrition: Nutrition = Field(default_factory=Nutrition)

    rating_value: Optional[float] = None
    rating_count: Optional[int] = None

    source_url: Optional[HttpUrl] = None

    @field_validator(
        "normalized_ingredients",
        "categories",
        "cuisines",
        "cooking_methods",
        "equipment",
    )
    @classmethod
    def normalize_string_lists(cls, values: List[str]) -> List[str]:
        return [
            value.strip().lower() for value in values
            if value and value.strip()
        ]