export interface Recipe {
  id: number;
  title: string;
  description: string;
  ingredients: string;
  instructions: string;
  cuisine: string;
  prep_time: number;
  cook_time: number;
  total_time: number;
  vegetarian: boolean;
  vegan: boolean;
  gluten_free: boolean;
  dairy_free: boolean;
  nut_free: boolean;
  spicy_level: number;
  difficulty: string;
  image_url?: string;
  is_ai_generated: boolean;
  generated_for_user_id?: number;
  tags?: string[];
}

export interface RecipeBrief {
  id: number;
  title: string;
  description: string;
  cuisine: string;
  prep_time: number;
  cook_time: number;
  total_time: number;
  difficulty: string;
  featured?: boolean;
  dietary_restrictions?: string[];
  tags?: string[];
}

export interface RecipeGenerationRequest {
  cuisine_preferences: string[];
  dietary_restrictions: string[];
  flavor_preferences: Record<string, number>;
  meal_type: string;
  skill_level: string;
  max_cooking_time: number;
  ingredients_to_include?: string[];
  ingredients_to_avoid?: string[];
}

export interface RecipeSimilarityRequest {
  query: string;
  max_results: number;
  vegetarian?: boolean;
  vegan?: boolean;
  gluten_free?: boolean;
  max_cooking_time?: number;
} 