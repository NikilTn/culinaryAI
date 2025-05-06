import React, { useState } from 'react';
import { RecipeSimilarityRequest } from '../types/recipe';
import './RecipeSearch.css';

interface RecipeSearchProps {
  onSearch: (searchParams: RecipeSimilarityRequest) => void;
  isSearching: boolean;
}

const RecipeSearch: React.FC<RecipeSearchProps> = ({ onSearch, isSearching }) => {
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(5);
  const [maxCookingTime, setMaxCookingTime] = useState<number | undefined>(undefined);
  const [vegetarian, setVegetarian] = useState(false);
  const [vegan, setVegan] = useState(false);
  const [glutenFree, setGlutenFree] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const cuisineOptions = [
    'Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 
    'Thai', 'French', 'Spanish', 'Mediterranean', 'American'
  ];

  const mealTypeOptions = [
    'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Dessert', 'Appetizer'
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const searchParams: RecipeSimilarityRequest = {
      query: query.trim(),
      max_results: maxResults,
      vegetarian,
      vegan,
      gluten_free: glutenFree,
      max_cooking_time: maxCookingTime
    };
    
    onSearch(searchParams);
  };

  const toggleAdvanced = () => {
    setShowAdvanced(!showAdvanced);
  };

  return (
    <div className="recipe-search">
      <form onSubmit={handleSubmit}>
        <div className="search-main">
          <div className="search-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for recipes, ingredients, or cuisines..."
              className="search-input"
            />
            <button 
              type="submit" 
              className="search-button"
              disabled={isSearching || !query.trim()}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>
          
          <button 
            type="button" 
            className="advanced-toggle"
            onClick={toggleAdvanced}
          >
            {showAdvanced ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>
        
        <div className={`advanced-filters ${showAdvanced ? 'show' : ''}`}>
          <div className="filter-section">
            <h4>Dietary Restrictions</h4>
            <div className="filter-options">
              <label className="filter-option">
                <input
                  type="checkbox"
                  checked={vegetarian}
                  onChange={() => setVegetarian(!vegetarian)}
                />
                Vegetarian
              </label>
              <label className="filter-option">
                <input
                  type="checkbox"
                  checked={vegan}
                  onChange={() => setVegan(!vegan)}
                />
                Vegan
              </label>
              <label className="filter-option">
                <input
                  type="checkbox"
                  checked={glutenFree}
                  onChange={() => setGlutenFree(!glutenFree)}
                />
                Gluten-Free
              </label>
            </div>
          </div>
          
          <div className="filter-section">
            <h4>Max Cooking Time</h4>
            <div className="filter-slider">
              <input
                type="range"
                min="15"
                max="180"
                step="15"
                value={maxCookingTime || 90}
                onChange={(e) => setMaxCookingTime(Number(e.target.value))}
              />
              <div className="range-value">
                {maxCookingTime ? `${maxCookingTime} minutes` : 'No limit'}
              </div>
              <button 
                type="button" 
                className="clear-button"
                onClick={() => setMaxCookingTime(undefined)}
              >
                Clear
              </button>
            </div>
          </div>
          
          <div className="filter-section">
            <h4>Max Results</h4>
            <div className="filter-slider">
              <input
                type="range"
                min="3"
                max="20"
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
              />
              <div className="range-value">{maxResults} recipes</div>
            </div>
          </div>
          
          <div className="cuisine-quick-filters">
            <h4>Quick Filters</h4>
            <div className="filter-tags">
              {cuisineOptions.map((cuisine) => (
                <button
                  key={cuisine}
                  type="button"
                  className="tag-filter"
                  onClick={() => setQuery(cuisine)}
                >
                  {cuisine}
                </button>
              ))}
            </div>
            <div className="filter-tags">
              {mealTypeOptions.map((mealType) => (
                <button
                  key={mealType}
                  type="button"
                  className="tag-filter meal-type"
                  onClick={() => setQuery(mealType)}
                >
                  {mealType}
                </button>
              ))}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default RecipeSearch; 