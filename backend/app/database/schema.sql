CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    ingredients JSONB NOT NULL DEFAULT '[]'::jsonb,
    ingredients_raw JSONB NOT NULL DEFAULT '[]'::jsonb,
    normalized_ingredients TEXT[] NOT NULL DEFAULT '{}',
    instructions JSONB NOT NULL DEFAULT '[]'::jsonb,

    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    total_time_minutes INTEGER,

    servings INTEGER,
    serving_description TEXT,

    categories TEXT[] NOT NULL DEFAULT '{}',
    cuisines TEXT[] NOT NULL DEFAULT '{}',
    cooking_methods TEXT[] NOT NULL DEFAULT '{}',
    equipment TEXT[] NOT NULL DEFAULT '{}',

    calories DOUBLE PRECISION,
    protein_g DOUBLE PRECISION,
    carbs_g DOUBLE PRECISION,
    fat_g DOUBLE PRECISION,
    saturated_fat_g DOUBLE PRECISION,
    fiber_g DOUBLE PRECISION,
    sugar_g DOUBLE PRECISION,
    sodium_mg DOUBLE PRECISION,
    cholesterol_mg DOUBLE PRECISION,

    rating_value DOUBLE PRECISION,
    rating_count INTEGER,

    source_url TEXT,

    search_text TEXT,

    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_recipes_normalized_ingredients
ON recipes
USING GIN (normalized_ingredients);

CREATE INDEX IF NOT EXISTS idx_recipes_cuisines
ON recipes
USING GIN (cuisines);

CREATE INDEX IF NOT EXISTS idx_recipes_categories
ON recipes
USING GIN (categories);

CREATE INDEX IF NOT EXISTS idx_recipes_equipment
ON recipes
USING GIN (equipment);