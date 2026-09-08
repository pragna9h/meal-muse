from sqlalchemy import text

from backend.app.config.settings import get_settings
from backend.app.database.connection import engine
from backend.app.services.llm import client
from backend.app.models.chat import ParsedIntent

from backend.app.models.recipe import Ingredient, Nutrition, Recipe

DEFAULT_SEMANTIC_LIMIT = 50
DEFAULT_STRUCTURED_LIMIT = 50
DEFAULT_RECIPE_NAME_LIMIT = 20


def vector_to_string(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"

def row_to_recipe(row: dict) -> Recipe:
    return Recipe(
        recipe_id=row["recipe_id"],
        name=row["name"],
        description=row.get("description"),
        ingredients=[
            Ingredient(**item)
            for item in row.get("ingredients", [])
        ],
        ingredients_raw=row.get("ingredients_raw", []),
        normalized_ingredients=row.get("normalized_ingredients", []),
        instructions=row.get("instructions", []),
        prep_time_minutes=row.get("prep_time_minutes"),
        cook_time_minutes=row.get("cook_time_minutes"),
        total_time_minutes=row.get("total_time_minutes"),
        servings=row.get("servings"),
        serving_description=row.get("serving_description"),
        categories=row.get("categories", []),
        cuisines=row.get("cuisines", []),
        cooking_methods=row.get("cooking_methods", []),
        equipment=row.get("equipment", []),
        nutrition=Nutrition(
            calories=row.get("calories"),
            protein_g=row.get("protein_g"),
            carbs_g=row.get("carbs_g"),
            fat_g=row.get("fat_g"),
            saturated_fat_g=row.get("saturated_fat_g"),
            fiber_g=row.get("fiber_g"),
            sugar_g=row.get("sugar_g"),
            sodium_mg=row.get("sodium_mg"),
            cholesterol_mg=row.get("cholesterol_mg"),
        ),
        rating_value=row.get("rating_value"),
        rating_count=row.get("rating_count"),
        source_url=row.get("source_url"),
    )
    

def get_recipes_by_ids(recipe_ids: list[str]) -> list[Recipe]:
    if not recipe_ids:
        return []

    sql = text(
        """
        SELECT
            recipe_id, name, description, ingredients,
            ingredients_raw, normalized_ingredients, instructions,
            prep_time_minutes, cook_time_minutes, total_time_minutes,
            servings, serving_description, categories,
            cuisines, cooking_methods, equipment,
            calories, protein_g, carbs_g,
            fat_g, saturated_fat_g, fiber_g,
            sugar_g, sodium_mg, cholesterol_mg,
            rating_value, rating_count, source_url
        FROM recipes
        WHERE recipe_id = ANY(CAST(:recipe_ids AS text[]))
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"recipe_ids": recipe_ids},
        ).mappings().all()

    recipes_by_id = {
        row["recipe_id"]: row_to_recipe(dict(row))
        for row in rows
    }

    return [
        recipes_by_id[recipe_id]
        for recipe_id in recipe_ids
        if recipe_id in recipes_by_id
    ]
    
def search_recipes_by_name(recipe_query: str, limit: int = DEFAULT_RECIPE_NAME_LIMIT) -> list[dict]:
    sql = text(
        """
        SELECT
            recipe_id,
            name,
            normalized_ingredients,
            prep_time_minutes,
            cook_time_minutes,
            total_time_minutes,
            calories,
            protein_g,
            cuisines,
            categories,
            equipment,
            rating_value,
            rating_count,
            source_url
        FROM recipes
        WHERE name ILIKE :contains_pattern
        ORDER BY
            CASE
                WHEN LOWER(name) = LOWER(:exact_name) THEN 0
                WHEN LOWER(name) LIKE LOWER(:prefix_pattern) THEN 1
                ELSE 2
            END,
            rating_value DESC NULLS LAST,
            rating_count DESC NULLS LAST
        LIMIT :limit
        """
    )

    parameters = {
        "contains_pattern": f"%{recipe_query}%",
        "exact_name": recipe_query,
        "prefix_pattern": f"{recipe_query}%",
        "limit": limit,
    }

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            parameters,
        ).mappings().all()

    return [dict(row) for row in rows]


def semantic_search( query: str, limit: int = DEFAULT_SEMANTIC_LIMIT, ) -> list[dict]:
    
    settings = get_settings()

    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=query,
    )

    query_embedding = vector_to_string(response.data[0].embedding)
    
    # embedding <=> query_embedding is pgvector cosine distance
    # cosine distance = 1 - cosine similarity

    sql = text(
        """
        SELECT recipe_id, name, normalized_ingredients,
            prep_time_minutes, cook_time_minutes, total_time_minutes,
            calories, protein_g, cuisines, categories,
            equipment, rating_value, rating_count,
            source_url, embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM recipes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "query_embedding": query_embedding,
                "limit": limit,
            },
        ).mappings().all()

    return [dict(row) for row in rows]


def structured_search( intent: ParsedIntent, limit: int = DEFAULT_STRUCTURED_LIMIT, ) -> list[dict]: 
    
    conditions = []
    parameters = { "limit": limit, }

    ingredient_terms = list(
    dict.fromkeys(
        intent.ingredients_available + intent.ingredients_required
        )
    )

    if ingredient_terms:
        parameters["ingredients"] = ingredient_terms

        conditions.append(
            "normalized_ingredients && CAST(:ingredients AS text[])"
        )
        
    if intent.cuisine_preferences:
        parameters["cuisines"] = intent.cuisine_preferences
        conditions.append(
            "cuisines && CAST(:cuisines AS text[])"
        )

    if intent.meal_type:
        parameters["meal_type"] = f"%{intent.meal_type}%"
        conditions.append(
            """
            EXISTS (
                SELECT 1
                FROM unnest(categories) AS category
                WHERE category ILIKE :meal_type
            )
            """
        )

    if intent.equipment_available:
        parameters["equipment"] = intent.equipment_available
        conditions.append(
            "equipment && CAST(:equipment AS text[])"
        )

    if intent.max_prep_minutes is not None:
        parameters["max_minutes"] = intent.max_prep_minutes

        conditions.append(
            """
            CASE
                WHEN prep_time_minutes > 0
                    AND cook_time_minutes > 0
                THEN prep_time_minutes + cook_time_minutes

                WHEN total_time_minutes > 0
                THEN total_time_minutes

                ELSE NULL
            END <= :max_minutes
            """
        )

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = text(
        f"""
        SELECT recipe_id, name, normalized_ingredients,
            prep_time_minutes, cook_time_minutes, total_time_minutes,
            calories, protein_g, cuisines,
            categories, equipment, rating_value,
            rating_count, source_url
        FROM recipes
        {where_clause}
        ORDER BY rating_value DESC NULLS LAST, 
                rating_count DESC NULLS LAST
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            parameters,
        ).mappings().all()

    return [dict(row) for row in rows]
