import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { exploreCuisines, CuisineRecommendation } from '../services/recipeService';
import '../styles/Explore.css';

const Explore: React.FC = () => {
  const { user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  
  // Genome-based exploration state
  const [exploreQuery, setExploreQuery] = useState('');
  const [cuisineRecommendations, setCuisineRecommendations] = useState<CuisineRecommendation[]>([]);
  const [exploring, setExploring] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);

  const handleExploreQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setExploreQuery(e.target.value);
  };
  
  const handleExploreSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exploreQuery.trim()) return;
    
    try {
      setExploring(true);
      setError(null);
      setDebugInfo(null);
      
      console.log("Submitting exploration query:", exploreQuery);
      const recommendations = await exploreCuisines(exploreQuery, 5);
      console.log("Received recommendations:", recommendations);
      
      // Save debug info
      setDebugInfo({
        timestamp: new Date().toISOString(),
        query: exploreQuery,
        resultCount: recommendations?.length || 0,
        success: Boolean(recommendations && recommendations.length > 0)
      });
      
      setCuisineRecommendations(recommendations || []);
      
      if (!recommendations || recommendations.length === 0) {
        setError('No cuisine recommendations were found. This could be due to an error processing your request.');
      }
    } catch (err: any) {
      console.error("Error during exploration:", err);
      setError(err?.response?.data?.detail || 'Failed to explore cuisines. Please try again.');
      setDebugInfo({
        timestamp: new Date().toISOString(),
        query: exploreQuery,
        error: err?.message || 'Unknown error',
        status: err?.response?.status || 'No status'
      });
    } finally {
      setExploring(false);
    }
  };

  // Add effect to log state changes for debugging
  useEffect(() => {
    console.log("CuisineRecommendations state updated:", cuisineRecommendations);
  }, [cuisineRecommendations]);

  return (
    <div className="explore-container">
      <h1 style={{color: 'white'}}>Genome-based Cuisine Search</h1>

      {error && <div className="error-message">{error}</div>}
      
      <div className="explore-intro">
        <p style={{color: 'white'}} >
          Discover cuisines and dishes similar to your favorite foods using our advanced genome-based search technology.
          Enter any cuisine or dish you enjoy to find related culinary options from around the world.
        </p>
      </div>
      
      <div className="explore-search">
        <form onSubmit={handleExploreSubmit} className="explore-form">
          <input
            type="text"
            placeholder="Describe what you want to eat... (e.g., 'I want to eat biryani')"
            value={exploreQuery}
            onChange={handleExploreQueryChange}
            className="explore-input"
          />
          <button 
            type="submit" 
            className="explore-btn" 
            disabled={exploring || !exploreQuery.trim()}
          >
            {exploring ? 'Exploring...' : 'Explore'}
          </button>
        </form>
        <p className="explore-info" style={{color: 'white'}}>
          Genome-based: Describe what you're in the mood for and discover cuisines with similar flavor profiles!
        </p>
      </div>

      <div className="cuisine-recommendations">
        {exploring ? (
          <div className="exploring-message">
            <p>Finding similar cuisines...</p>
          </div>
        ) : cuisineRecommendations && cuisineRecommendations.length > 0 ? (
          <>
            <h2 style={{color: 'white'}}>Cuisines Similar to "{exploreQuery}"</h2>
            <div className="recommendations-list">
              {cuisineRecommendations.map((cuisine, index) => (
                <div key={index} className="cuisine-card">
                  <h3 className="cuisine-name">{cuisine.name}</h3>
                  <p className="cuisine-description">{cuisine.description}</p>
                  <div className="cuisine-details">
                    <div className="cuisine-section">
                      <h4>Key Ingredients</h4>
                      <ul className="ingredients-list">
                        {Array.isArray(cuisine.key_ingredients) && cuisine.key_ingredients.map((ingredient, i) => (
                          <li key={i}>{ingredient}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="cuisine-section">
                      <h4>Flavor Profile</h4>
                      <p>{cuisine.flavor_profile}</p>
                    </div>
                  </div>
                  <div className="cuisine-similarity">
                    <h4>Why it's similar</h4>
                    <p>{cuisine.similarity_reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : !exploring && exploreQuery ? (
          <div className="no-results">
            <p>No recommendations found. Try a different query.</p>
            {debugInfo && (
              <details className="debug-info">
                <summary>Debug Info (click to expand)</summary>
                <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
              </details>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default Explore; 