import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  getUserRecommendations, 
  generateRecipe, 
  findSimilarRecipes, 
  getFeaturedRecipes,
  checkRecipeGenerationStatus 
} from '../services/recipeService';
import { preferenceAPI } from '../services/api';
import { Recipe, RecipeBrief, RecipeGenerationRequest, RecipeSimilarityRequest } from '../types/recipe';
import RecipeSearch from '../components/RecipeSearch';
import RecipeCard from '../components/RecipeCard';
import './Recommendations.css';

// Number of recipes to show
const MAX_RECIPES_TO_SHOW = 12; // Show 12 recipes total (a good number between 7-15)
const RECIPES_PER_PAGE = 12;

// Progress polling interval in milliseconds
const PROGRESS_CHECK_INTERVAL = 3000;

const Recommendations: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<RecipeBrief[]>([]);
  const [searchResults, setSearchResults] = useState<RecipeBrief[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedRecipe, setGeneratedRecipe] = useState<Recipe | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [isSearchMode, setIsSearchMode] = useState<boolean>(false);
  const [page, setPage] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false); // Set to false as we're limiting the total number
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  
  // Recipe generation progress tracking
  const [isGeneratingPreferenceRecipes, setIsGeneratingPreferenceRecipes] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const progressCheckInterval = useRef<NodeJS.Timeout | null>(null);
  
  const observer = useRef<IntersectionObserver | null>(null);
  const lastRecipeRef = useCallback((node: HTMLDivElement | null) => {
    if (loading || loadingMore) return;
    if (observer.current) observer.current.disconnect();
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore && !isSearchMode) {
        loadMoreRecommendations();
      }
    });
    
    if (node) observer.current.observe(node);
  }, [loading, loadingMore, hasMore, isSearchMode]);

  useEffect(() => {
    if (!user) {
      console.log("useEffect: No user, navigating to auth.");
      navigate('/auth');
      return;
    }
    
    console.log("useEffect: Running initial data fetch and setup.");

    const fetchData = async () => {
      try {
        setLoading(true);
        
        console.log("useEffect/fetchData: Checking generation status...");
        const generationStatus = await checkRecipeGenerationStatus(user.id);
        console.log("useEffect/fetchData: Generation status:", generationStatus);
        
        // If user has preferences and recipes are being generated or not complete, show loading state
        if (generationStatus.has_preferences) {
          if (generationStatus.is_generating || !generationStatus.generation_complete) {
            console.log("useEffect/fetchData: Generation in progress or incomplete, starting progress check.");
            // Recipes are still being generated
            setIsGeneratingPreferenceRecipes(true);
            setGenerationProgress(
              generationStatus.recipes_count >= 6 ? 100 : 
              Math.round((generationStatus.recipes_count / 6) * 100)
            );
            
            // Start polling for progress
            startProgressChecking();
          }
        }
        
        // Fetch recommendations even if they're still being generated (we'll show what we have so far)
        const [userRecs, featuredRecs] = await Promise.all([
          getUserRecommendations(RECIPES_PER_PAGE, 0),
          getFeaturedRecipes(4) // Fetch fewer featured recipes to stay within our limit
        ]);
        
        // Mark featured recipes
        const markedFeatured = featuredRecs.map(recipe => ({
          ...recipe,
          featured: true
        }));
        
        // Combine both types of recommendations and limit the total
        const allRecommendations = [...userRecs, ...markedFeatured].slice(0, MAX_RECIPES_TO_SHOW);
        
        setRecommendations(allRecommendations);
        setHasMore(false); // Disable "load more" as we're limiting the total
        setPage(1);
      } catch (err) {
        setError('Failed to fetch recommendations. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Cleanup function
    return () => {
      console.log("useEffect: Cleanup - Clearing progress interval if it exists.");
      if (progressCheckInterval.current) {
        clearInterval(progressCheckInterval.current);
        progressCheckInterval.current = null;
      }
    };
  }, [user, navigate]);
  
  // Function to start checking progress
  const startProgressChecking = () => {
    console.log("startProgressChecking: Attempting to start polling...");
    // Clear any existing interval FIRST to prevent duplicates
    if (progressCheckInterval.current) {
      console.log("startProgressChecking: Clearing existing interval before starting new one.");
      clearInterval(progressCheckInterval.current);
      progressCheckInterval.current = null; // Explicitly nullify
    }
    
    console.log(`startProgressChecking: Setting new interval (${PROGRESS_CHECK_INTERVAL}ms).`);
    // Start a new interval
    progressCheckInterval.current = setInterval(async () => {
      if (!user) {
        console.log("Polling Interval: No user, skipping check.");
        // Consider clearing interval if user logs out during polling
        // if (progressCheckInterval.current) clearInterval(progressCheckInterval.current);
        return;
      } 
      
      try {
        // console.log("Polling Interval: Checking status..."); // Can be noisy
        const status = await checkRecipeGenerationStatus(user.id);
        // console.log("Polling Interval: Status:", status); // Can be noisy
        
        // Update progress
        setGenerationProgress(
          status.recipes_count >= 6 ? 100 : 
          Math.round((status.recipes_count / 6) * 100)
        );
        
        // If generation is complete, stop polling and refresh recommendations
        if (!status.is_generating && status.generation_complete) {
          setIsGeneratingPreferenceRecipes(false); // Hide progress bar
          console.log("Polling Interval: Generation complete. Clearing interval.");
          clearInterval(progressCheckInterval.current!); 
          progressCheckInterval.current = null; // Explicitly nullify
          
          console.log("Recipe generation complete according to status check. Refreshing recommendations.");
          
          // Refresh recommendations - Show loading indicator during fetch
          setLoading(true); 
          setError(null); // Clear previous errors
          try {
            const freshRecs = await getUserRecommendations(RECIPES_PER_PAGE, 0);
            setRecommendations(prevRecs => {
              // Keep the featured recipes, replace the user recommendations
              const featured = prevRecs.filter(r => r.featured);
              const updatedRecs = [...freshRecs, ...featured].slice(0, MAX_RECIPES_TO_SHOW);
              console.log(`Refreshed recommendations: ${updatedRecs.length} recipes loaded.`);
              return updatedRecs;
            });
          } catch (err) {
              console.error('Error refreshing recommendations after generation:', err);
              setError('Failed to refresh recommendations after generation.');
              // Optionally keep existing recommendations or clear them
              // setRecommendations([]); 
          } finally {
              setLoading(false); // Hide general loading spinner AFTER fetch completes/fails
          }
        }
      } catch (err) {
        console.error('Error checking generation progress:', err);
      }
    }, PROGRESS_CHECK_INTERVAL);
  };

  const loadMoreRecommendations = async () => {
    // Not needed as we're limiting the total number, but kept for future use
    if (loadingMore || !hasMore || isSearchMode) return;
    
    try {
      setLoadingMore(true);
      const offset = page * RECIPES_PER_PAGE;
      const newData = await getUserRecommendations(RECIPES_PER_PAGE, offset);
      
      if (newData.length > 0) {
        // Limit the total number of recipes shown
        const updatedRecommendations = [...recommendations, ...newData].slice(0, MAX_RECIPES_TO_SHOW);
        setRecommendations(updatedRecommendations);
        setPage(prevPage => prevPage + 1);
        setHasMore(updatedRecommendations.length < MAX_RECIPES_TO_SHOW && newData.length === RECIPES_PER_PAGE);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error('Error loading more recommendations:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSearch = async (searchParams: RecipeSimilarityRequest) => {
    try {
      setSearching(true);
      setError(null);
      setIsSearchMode(true);
      
      const results = await findSimilarRecipes(searchParams);
      // Limit search results too
      setSearchResults(results.slice(0, MAX_RECIPES_TO_SHOW));
    } catch (err) {
      setError('Failed to search recipes. Please try again later.');
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setIsSearchMode(false);
    setSearchResults([]);
  };

  const handleGenerateRecipe = async () => {
    try {
      setGenerating(true);
      setError(null);
      
      // First try to get user preferences to use for recipe generation
      let cuisinePreferences = ['Italian', 'Mediterranean']; // Default values
      let dietaryRestrictions: string[] = [];
      let flavorPreferences = {
        'spicy': 3,
        'sweet': 2,
        'savory': 4,
        'bitter': 1,
        'sour': 2
      };
      let mealType = 'dinner';
      let skillLevel = 'intermediate';
      let maxCookingTime = 60;
      
      try {
        // Try to fetch user preferences
        const preferences = await preferenceAPI.getPreferences();
        
        // Use user preferences if available
        if (preferences) {
          console.log("Using user preferences for recipe generation:", preferences);
          
          // Use user's favorite cuisines
          if (preferences.favorite_cuisines && preferences.favorite_cuisines.length > 0) {
            cuisinePreferences = preferences.favorite_cuisines;
          }
          
          // Use user's dietary restrictions
          if (preferences.dietary_restrictions && preferences.dietary_restrictions.length > 0) {
            dietaryRestrictions = preferences.dietary_restrictions;
          }
          
          // Set skill level based on user preference
          if (preferences.cooking_skill_level) {
            skillLevel = preferences.cooking_skill_level;
          }
          
          // Add any allergies to dietary restrictions
          if (preferences.allergies && preferences.allergies.length > 0) {
            // For each allergy, add "no X" to dietary restrictions
            const allergyRestrictions = preferences.allergies.map((a: string) => `no ${a}`);
            dietaryRestrictions = [...dietaryRestrictions, ...allergyRestrictions];
          }
        }
      } catch (err) {
        console.error('Error fetching user preferences:', err);
        // Continue with defaults if preferences fetch fails
      }
      
      // Generate recipe with user preferences or defaults
      const request: RecipeGenerationRequest = {
        cuisine_preferences: cuisinePreferences,
        dietary_restrictions: dietaryRestrictions,
        flavor_preferences: flavorPreferences,
        meal_type: mealType,
        skill_level: skillLevel,
        max_cooking_time: maxCookingTime
      };
      
      console.log("Sending recipe generation request:", request);
      const recipe = await generateRecipe(request);
      setGeneratedRecipe(recipe);
      
      // Add the new recipe to recommendations
      if (!isSearchMode) {
        // Add the new recipe and maintain our limit
        setRecommendations(prev => [recipe, ...prev].slice(0, MAX_RECIPES_TO_SHOW));
      }
    } catch (err) {
      setError('Failed to generate recipe. Please try again later.');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="recommendations-container">
      <h1 style={{ color: 'white' }}>Your Culinary Recommendations</h1>
      
      {isGeneratingPreferenceRecipes && (
        <div className="generation-progress">
          <h3>Generating New Recommendations...</h3>
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${generationProgress}%` }}
            ></div>
          </div>
          <p className="progress-text">{generationProgress}% Complete</p>
          <p className="progress-message">
            We're creating personalized recipes based on your preferences. This may take a minute...
          </p>
        </div>
      )}
      
      <RecipeSearch 
        onSearch={handleSearch}
        isSearching={searching}
      />
      
      <div className="recommendation-actions">
        <button 
          onClick={handleGenerateRecipe}
          disabled={generating || isGeneratingPreferenceRecipes}
          className="generate-button"
        >
          {generating ? 'Generating...' : 'Generate a New Recipe'}
        </button>
        
        {isSearchMode && (
          <button 
            onClick={handleClearSearch}
            className="clear-search-button"
          >
            Back to Recommendations
          </button>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {generatedRecipe && (
        <div className="generated-recipe">
          <h2>Freshly Generated Recipe</h2>
          <div className="featured-recipe-wrapper">
            <RecipeCard recipe={generatedRecipe} featured={true} />
            <div className="recipe-content">
              <h4>Ingredients</h4>
              <pre className="recipe-ingredients">{generatedRecipe.ingredients}</pre>
              <h4>Instructions</h4>
              <pre className="recipe-instructions">{generatedRecipe.instructions}</pre>
            </div>
          </div>
        </div>
      )}
      
      <div className="recommendations-list">
        {isSearchMode ? (
          <>
            <h2>Search Results</h2>
            {searching ? (
              <p className="loading-text">Searching for recipes...</p>
            ) : searchResults.length > 0 ? (
              <div className="recipe-grid with-animation">
                {/* Limit search results */} 
                {searchResults.slice(0, 9).map((recipe, index) => (
                  <RecipeCard 
                    key={recipe.id} 
                    recipe={recipe} 
                    style={{ "--i": index } as React.CSSProperties}
                  />
                ))}
              </div>
            ) : (
              <p className="no-results">No recipes found matching your search criteria.</p>
            )}
          </>
        ) : (
          <>
            <h2>Explore Our Recipes</h2>
            <p className="section-description">
              A collection of delicious recipes and culinary highlights from around the world for you to explore.
            </p>
            {loading ? (
              <p className="loading-text">Loading recipes...</p>
            ) : recommendations.length > 0 ? (
              <>
                <div className="recipe-grid with-animation">
                  {/* Limit recommendations */} 
                  {recommendations.slice(0, 9).map((recipe, index) => (
                    <RecipeCard 
                      key={recipe.id} 
                      recipe={recipe} 
                      featured={recipe.featured}
                      style={{ "--i": index } as React.CSSProperties}
                    />
                  ))}
                </div>
                {/* Remove loading more indicator since we are limiting to 9 */}
                {/* {loadingMore && (
                  <div className="loading-more">
                    <p>Loading more recipes...</p>
                  </div>
                )} */}
              </>
            ) : (
              <p className="no-results">No recipes found. Try generating a new recipe or check back later for more options.</p>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Recommendations;