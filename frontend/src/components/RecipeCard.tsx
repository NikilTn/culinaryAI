import React, { useState, CSSProperties } from 'react';
import { RecipeBrief } from '../types/recipe';
import './RecipeCard.css';

interface RecipeCardProps {
  recipe: RecipeBrief;
  featured?: boolean;
  style?: React.CSSProperties;
}

const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, featured = false, style }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div 
      className={`recipe-card ${featured ? 'featured' : ''} ${expanded ? 'expanded' : ''}`}
      onClick={() => setExpanded(!expanded)}
      style={style}
    >
      {featured && <div className="featured-badge">Featured</div>}
      
      <div className="recipe-card-header">
        <h3 className="recipe-title">{recipe.title}</h3>
        <span className={`difficulty-badge ${recipe.difficulty.toLowerCase()}`}>
          {recipe.difficulty}
        </span>
      </div>
      
      <p className="recipe-description">{recipe.description}</p>
      
      <div className="recipe-details">
        <div className="recipe-time">
          <span><i className="time-icon prep"></i>Prep: {recipe.prep_time} min</span>
          <span><i className="time-icon cook"></i>Cook: {recipe.cook_time} min</span>
          <span><i className="time-icon total"></i>Total: {recipe.total_time || (recipe.prep_time + recipe.cook_time)} min</span>
        </div>
      </div>
      
      <div className="recipe-tags">
        <span className="tag cuisine">{recipe.cuisine}</span>
        {recipe.dietary_restrictions && recipe.dietary_restrictions.map(restriction => (
          <span key={restriction} className="tag dietary">
            {restriction}
          </span>
        ))}
        {recipe.tags && recipe.tags.map(tag => (
          <span key={tag} className="tag general">
            {tag}
          </span>
        ))}
      </div>
      
      {expanded && (
        <div className="recipe-card-actions">
          <button className="card-action-button">
            View Full Recipe
          </button>
          <button className="card-action-button secondary">
            Save Recipe
          </button>
        </div>
      )}
    </div>
  );
};

export default RecipeCard; 