import axios from 'axios';
import { Recipe, RecipeBrief, RecipeGenerationRequest, RecipeSimilarityRequest } from '../types/recipe';

const API_URL = process.env.REACT_APP_API_BASE_URL || 'https://culinaryai-backend-428343023990.us-central1.run.app';

// Set the auth token for all requests
const setAuthHeader = () => {
  const token = localStorage.getItem('token');
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Get personalized recommendations with pagination
export const getUserRecommendations = async (limit: number = 5, offset: number = 0): Promise<RecipeBrief[]> => {
  setAuthHeader();
  const response = await axios.get(`${API_URL}/recommendations/user?limit=${limit}&offset=${offset}`);
  return response.data;
};

// Get featured recipes (shown to all users regardless of preferences)
export const getFeaturedRecipes = async (limit: number = 20): Promise<RecipeBrief[]> => {
  setAuthHeader();
  const response = await axios.get(`${API_URL}/recommendations/featured?limit=${limit}`);
  return response.data;
};

// Generate a new recipe based on preferences
export const generateRecipe = async (request: RecipeGenerationRequest): Promise<Recipe> => {
  setAuthHeader();
  const response = await axios.post(`${API_URL}/recommendations/generate`, request);
  return response.data;
};

// Find similar recipes based on search criteria
export const findSimilarRecipes = async (request: RecipeSimilarityRequest): Promise<RecipeBrief[]> => {
  setAuthHeader();
  try {
    // Construct query parameters based on search request
    const params = new URLSearchParams();
    
    // Always include the main search query and limit
    if (request.query) {
      params.append('search', request.query);
    }
    params.append('limit', request.max_results.toString());
    
    // Add optional filters
    if (request.vegetarian) {
      params.append('dietary_restriction', 'vegetarian');
    }
    if (request.vegan) {
      params.append('dietary_restriction', 'vegan');
    }
    if (request.gluten_free) {
      params.append('dietary_restriction', 'gluten-free');
    }
    if (request.max_cooking_time) {
      params.append('max_cooking_time', request.max_cooking_time.toString());
    }
    
    // Use GET request with query parameters
    const response = await axios.get(`${API_URL}/recommendations/recipes?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error searching for recipes:', error);
    throw error;
  }
};

// Get cuisine recommendations based on natural language input
export interface CuisineRecommendation {
  name: string;
  description: string;
  key_ingredients: string[];
  flavor_profile: string;
  similarity_reason: string;
}

export const exploreCuisines = async (query: string, limit: number = 5): Promise<CuisineRecommendation[]> => {
  setAuthHeader();
  try {
    console.log("Starting cuisine exploration request:", { query, limit });
    const response = await axios.post(`${API_URL}/recommendations/explore`, { query, limit });
    console.log("Exploration response received:", response.data);
    
    // Validate that the response data is an array
    if (!Array.isArray(response.data)) {
      console.error("Response is not an array:", response.data);
      return [];
    }
    
    // Validate that each item has the required fields and convert any strings to arrays if needed
    const validatedResults = response.data.map(item => {
      if (!item || typeof item !== 'object') {
        console.warn("Skipping invalid item (not an object):", item);
        return null;
      }
      
      const validatedItem = { ...item };
      
      // Ensure name field exists
      if (!validatedItem.name) {
        console.warn("Item missing name field:", item);
        validatedItem.name = "Unknown Cuisine";
      }
      
      // Ensure description field exists
      if (!validatedItem.description) {
        validatedItem.description = `A delicious dish with flavors similar to ${query}`;
      }
      
      // Ensure key_ingredients is always an array
      if (!validatedItem.key_ingredients) {
        validatedItem.key_ingredients = ["Various ingredients"];
      } else if (typeof validatedItem.key_ingredients === 'string') {
        try {
          // Try to parse if it's a JSON string
          if (validatedItem.key_ingredients.startsWith('[') && validatedItem.key_ingredients.endsWith(']')) {
            validatedItem.key_ingredients = JSON.parse(validatedItem.key_ingredients);
          } else {
            // If it's not valid JSON, split by commas or make empty array
            validatedItem.key_ingredients = validatedItem.key_ingredients.split(',').map((i: string) => i.trim());
          }
        } catch (e) {
          console.warn("Error parsing key_ingredients:", e);
          validatedItem.key_ingredients = [validatedItem.key_ingredients];
        }
      } else if (!Array.isArray(validatedItem.key_ingredients)) {
        validatedItem.key_ingredients = ["Various ingredients"];
      }
      
      // Ensure flavor_profile field exists
      if (!validatedItem.flavor_profile) {
        validatedItem.flavor_profile = "Flavorful";
      } else if (Array.isArray(validatedItem.flavor_profile)) {
        // Convert array to comma-separated string
        validatedItem.flavor_profile = validatedItem.flavor_profile.join(", ");
      }
      
      // Ensure similarity_reason field exists
      if (!validatedItem.similarity_reason) {
        validatedItem.similarity_reason = `This dish shares similar flavor profiles with ${query}`;
      }
      
      return validatedItem;
    }).filter(Boolean) as CuisineRecommendation[];
    
    console.log("Validated results:", validatedResults);
    return validatedResults;
  } catch (error) {
    console.error('Error exploring cuisines:', error);
    throw error;
  }
};

// Check recipe generation status after preference update
export const checkRecipeGenerationStatus = async (userId: number): Promise<{
  is_generating: boolean;
  recipes_count: number;
  has_preferences: boolean;
  generation_complete: boolean;
}> => {
  setAuthHeader();
  try {
    const response = await axios.get(`${API_URL}/preferences/recipe-generation-status`);
    return response.data;
  } catch (error) {
    console.error('Error checking recipe generation status:', error);
    // Return a default status in case of error
    return {
      is_generating: false,
      recipes_count: 0,
      has_preferences: false,
      generation_complete: false
    };
  }
}; 