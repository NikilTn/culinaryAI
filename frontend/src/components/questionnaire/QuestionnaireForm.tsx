import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { preferenceAPI } from '../../services/api';
import './QuestionnaireStyles.css';

// Define the cuisine options
const CUISINE_OPTIONS = [
  'Italian', 'Mexican', 'Chinese', 'Japanese', 'Indian', 
  'Thai', 'Mediterranean', 'French', 'Spanish', 'Greek',
  'American', 'Korean', 'Vietnamese', 'Middle Eastern'
];

// Define the dietary restriction options
const DIETARY_RESTRICTIONS = [
  'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'nut-free'
];

// Define health goals
const HEALTH_GOALS = [
  'weight_loss', 'muscle_gain', 'heart_health', 'diabetes_management',
  'energy_boost', 'better_digestion', 'general_wellness'
];

// Define common allergies
const ALLERGIES = [
  'peanuts', 'tree_nuts', 'dairy', 'eggs', 'fish', 'shellfish',
  'soy', 'wheat', 'sesame'
];

// Define the skill levels
const SKILL_LEVELS = [
  'beginner', 'intermediate', 'advanced'
];

const QuestionnaireForm: React.FC = () => {
  const navigate = useNavigate();
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form data state updated to match new preference model
  const [formData, setFormData] = useState({
    favorite_cuisines: [] as string[],
    dietary_restrictions: [] as string[],
    cooking_skill_level: 'intermediate',
    health_goals: [] as string[],
    allergies: [] as string[],
    additional_preferences: {}
  });
  
  // Handle checkbox changes
  const handleCheckboxChange = (category: 'favorite_cuisines' | 'dietary_restrictions' | 'health_goals' | 'allergies', value: string) => {
    setFormData(prev => {
      const currentValues = [...prev[category]];
      
      if (currentValues.includes(value)) {
        return {
          ...prev,
          [category]: currentValues.filter(item => item !== value)
        };
      } else {
        return {
          ...prev,
          [category]: [...currentValues, value]
        };
      }
    });
  };
  
  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      console.log('Submitting preferences:', formData);
      await preferenceAPI.submitQuestionnaire(formData);
      navigate('/recommendations');
    } catch (err: any) {
      console.error('Error submitting questionnaire:', err);
      setError(err.response?.data?.detail || 'Failed to submit the questionnaire. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Go to next step
  const nextStep = () => {
    setStep(step + 1);
  };
  
  // Go to previous step
  const prevStep = () => {
    setStep(step - 1);
  };
  
  // Render step 1 - Cuisines and Dietary Restrictions
  const renderStep1 = () => (
    <div className="step-container">
      <h2>Step 1: Cuisine & Dietary Preferences</h2>
      
      <div className="form-section">
        <h3>What cuisines do you enjoy the most?</h3>
        <div className="checkbox-grid">
          {CUISINE_OPTIONS.map(cuisine => (
            <div key={cuisine} className="checkbox-item">
              <input
                type="checkbox"
                id={`fav-${cuisine}`}
                checked={formData.favorite_cuisines.includes(cuisine)}
                onChange={() => handleCheckboxChange('favorite_cuisines', cuisine)}
              />
              <label htmlFor={`fav-${cuisine}`}>{cuisine}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="form-section">
        <h3>Do you have any dietary restrictions?</h3>
        <div className="checkbox-grid">
          {DIETARY_RESTRICTIONS.map(restriction => (
            <div key={restriction} className="checkbox-item">
              <input
                type="checkbox"
                id={`diet-${restriction}`}
                checked={formData.dietary_restrictions.includes(restriction)}
                onChange={() => handleCheckboxChange('dietary_restrictions', restriction)}
              />
              <label htmlFor={`diet-${restriction}`}>{restriction}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="nav-buttons">
        <button type="button" onClick={nextStep}>Next</button>
      </div>
    </div>
  );
  
  // Render step 2 - Health Goals and Allergies
  const renderStep2 = () => (
    <div className="step-container">
      <h2>Step 2: Health Goals & Allergies</h2>
      
      <div className="form-section">
        <h3>What are your health goals?</h3>
        <div className="checkbox-grid">
          {HEALTH_GOALS.map(goal => (
            <div key={goal} className="checkbox-item">
              <input
                type="checkbox"
                id={`goal-${goal}`}
                checked={formData.health_goals.includes(goal)}
                onChange={() => handleCheckboxChange('health_goals', goal)}
              />
              <label htmlFor={`goal-${goal}`}>{goal.replace('_', ' ')}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="form-section">
        <h3>Do you have any allergies?</h3>
        <div className="checkbox-grid">
          {ALLERGIES.map(allergy => (
            <div key={allergy} className="checkbox-item">
              <input
                type="checkbox"
                id={`allergy-${allergy}`}
                checked={formData.allergies.includes(allergy)}
                onChange={() => handleCheckboxChange('allergies', allergy)}
              />
              <label htmlFor={`allergy-${allergy}`}>{allergy.replace('_', ' ')}</label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="nav-buttons">
        <button type="button" onClick={prevStep}>Previous</button>
        <button type="button" onClick={nextStep}>Next</button>
      </div>
    </div>
  );
  
  // Render step 3 - Cooking Skill Level
  const renderStep3 = () => (
    <div className="step-container">
      <h2>Step 3: Cooking Details</h2>
      
      <div className="form-section">
        <h3>Cooking Skill Level</h3>
        <div className="select-input">
          <label htmlFor="cooking_skill_level">What is your cooking skill level?</label>
          <select
            id="cooking_skill_level"
            name="cooking_skill_level"
            value={formData.cooking_skill_level}
            onChange={handleInputChange}
          >
            {SKILL_LEVELS.map(level => (
              <option key={level} value={level}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="nav-buttons">
        <button type="button" onClick={prevStep}>Previous</button>
        <button type="submit" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Preferences'}
        </button>
      </div>
    </div>
  );
  
  return (
    <div className="questionnaire-container">
      <h1>Culinary Preferences Questionnaire</h1>
      <p className="subtitle">Help us understand your taste preferences so we can recommend the perfect dishes for you.</p>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="progress-bar">
        <div 
          className="progress" 
          style={{ width: `${(step / 3) * 100}%` }}
        ></div>
      </div>
      
      <form onSubmit={handleSubmit}>
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
        {step === 3 && renderStep3()}
      </form>
    </div>
  );
};

export default QuestionnaireForm; 