export type ResultState =
  | "success"
  | "clarification_required"
  | "no_results"
  | "failure";

export interface ChatRequest {
  message: string;
}

export interface ParsedIntent {
  intent: "meal_recommendation" | "recipe_search";
  recipe_query?: string | null;

  ingredients_available: string[];
  ingredients_required: string[];
  ingredients_excluded: string[];

  meal_type?: string | null;
  dietary_preferences: string[];
  allergies: string[];
  cuisine_preferences: string[];
  nutrition_goals: string[];

  max_prep_minutes?: number | null;
  servings?: number | null;

  taste_preferences: string[];
  equipment_available: string[];

  budget_level?: string | null;
  skill_level?: string | null;
  allow_substitutions?: boolean | null;

  needs_clarification: boolean;
  clarification_question?: string | null;
}

export interface MealRecommendation {
  recipe_id: string;
  name: string;
  score: number;
  rating_value?: number | null;

  total_time_minutes?: number | null;
  calories?: number | null;
  protein_g?: number | null;

  matched_ingredients: string[];
  missing_ingredients: string[];

  reason?: string | null;
  source_url?: string | null;
}

export interface Ingredient {
  name: string;
  quantity?: string | null;
  unit?: string | null;
  misc?: string | null;
}

export interface Nutrition {
  calories?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  saturated_fat_g?: number | null;
  fiber_g?: number | null;
  sugar_g?: number | null;
  sodium_mg?: number | null;
  cholesterol_mg?: number | null;
}

export interface Recipe {
  recipe_id: string;
  name: string;

  description?: string | null;

  ingredients: Ingredient[];
  ingredients_raw: string[];
  normalized_ingredients: string[];

  instructions: string[];

  prep_time_minutes?: number | null;
  cook_time_minutes?: number | null;
  total_time_minutes?: number | null;

  servings?: number | null;
  serving_description?: string | null;

  categories: string[];
  cuisines: string[];
  cooking_methods: string[];
  equipment: string[];

  nutrition: Nutrition;

  rating_value?: number | null;
  rating_count?: number | null;

  source_url?: string | null;
}

export interface ChatResponse {
  result_state: ResultState;
  message?: string | null;

  parsed_intent: ParsedIntent;

  recommendations: MealRecommendation[];
  recipes: Recipe[];
}