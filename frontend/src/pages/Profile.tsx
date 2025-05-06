import React, { useState, useEffect } from 'react';
// Remove direct axios import, use centralized API service
// import axios from 'axios'; 
import { useAuth } from '../context/AuthContext';
// Import the centralized API service
import { preferenceAPI } from '../services/api'; 
// Import the full Preference type if it exists, or expand the interface here
// Assuming a type like this exists based on UserPreferences.tsx and backend
// import { Preference } from '../types'; // Comment out for now as path/export is unclear

import '../styles/Profile.css';

// Remove direct API_URL usage if preferenceAPI handles it
// const API_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

// Use the imported Preference type or define a more complete one here
// Keeping UserPreferences for now, but ideally replace with shared Preference type
interface UserPreferences {
  user_id?: number; // Add user_id if needed by update call
  dietary_restrictions: string[];
  favorite_cuisines: string[];
  cooking_skill_level: string;
  health_goals: string[];
  allergies: string[];
  // Add potentially missing fields (based on backend model)
  vegetarian?: boolean; 
  vegan?: boolean;
  gluten_free?: boolean;
  dairy_free?: boolean;
  nut_free?: boolean;
  spicy_level?: number;
  sweet_level?: number;
  savory_level?: number;
  bitter_level?: number;
  sour_level?: number;
  breakfast?: boolean;
  lunch?: boolean;
  dinner?: boolean;
  snacks?: boolean;
  desserts?: boolean;
  cooking_time_max?: number;
  additional_notes?: string; // Example if this exists
}

type PreferenceListCategory = 'dietary_restrictions' | 'favorite_cuisines' | 'health_goals' | 'allergies';

const Profile: React.FC = () => {
  const { user } = useAuth();
  // Initialize with a more complete structure, matching the backend/questionnaire
  const [preferences, setPreferences] = useState<UserPreferences>({
    dietary_restrictions: [],
    favorite_cuisines: [],
    cooking_skill_level: 'beginner',
    health_goals: [],
    allergies: [],
    // Initialize potentially missing fields
    vegetarian: false, 
    vegan: false,
    gluten_free: false,
    dairy_free: false,
    nut_free: false,
    spicy_level: 3,
    sweet_level: 3,
    savory_level: 3,
    bitter_level: 3,
    sour_level: 3,
    breakfast: true,
    lunch: true,
    dinner: true,
    snacks: true,
    desserts: true,
    cooking_time_max: 60,
    additional_notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        setLoading(true);
        setError(null);
        // Use the centralized API call
        const fetchedPrefs = await preferenceAPI.getPreferences(); 
        // Merge fetched data with initial state to ensure all fields are present
        setPreferences(prev => ({ ...prev, ...fetchedPrefs }));
      } catch (err: any) {
        // Handle 404 gracefully (user hasn't set prefs yet)
        if (err.response && err.response.status === 404) {
          console.log("No preferences found for user, using defaults.");
        } else {
          console.error('Failed to fetch preferences:', err);
          setError('Failed to fetch preferences. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    // User ID check is implicitly handled by useAuth usually
      fetchPreferences();

  }, []); // Removed user?.id dependency if API call handles auth internally

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      setLoading(true);
      // Use the centralized API call for updating
      // Ensure the payload matches what the API expects (may need adjustments)
      // The current 'preferences' state should align if the interface/type is correct
      await preferenceAPI.updatePreferences(preferences); 
      setSuccess('Preferences updated successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to update preferences:', err);
      setError('Failed to update preferences. Please check your inputs and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Update handler for list-based preferences (checkbox groups)
  const handleCheckboxChange = (category: PreferenceListCategory, value: string) => {
    setPreferences(prev => {
      const currentArray = prev[category] as string[] | undefined || [];
      const newArray = currentArray.includes(value)
        ? currentArray.filter(item => item !== value)
        : [...currentArray, value];
      return {
        ...prev,
        [category]: newArray
      };
    });
  };
  
  // Update handler for simple boolean preferences (single checkboxes)
  const handleBooleanChange = (field: keyof UserPreferences) => {
    setPreferences(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };
  
  // Update handler for number preferences (sliders/number inputs)
  const handleNumberChange = (field: keyof UserPreferences, value: string) => {
     const num = parseInt(value, 10);
     if (!isNaN(num)) {
        setPreferences(prev => ({
           ...prev,
           [field]: num
        }));
     }
  };

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPreferences(prev => ({
      ...prev,
      cooking_skill_level: e.target.value
    }));
  };

  if (loading) {
    return <div className="profile-container">Loading...</div>;
  }

  return (
    <div className="profile-container">
      <div className="user-details-section">
        <h1 style={{color: 'white'}}>Your Profile</h1>
        
        <div className="user-card">
          <div className="user-avatar">
            {user?.username.charAt(0).toUpperCase()}
          </div>
          <div className="user-info">
            <h2>{user?.username}</h2>
            <p className="user-email">{user?.email}</p>
            <p className="user-id">Account ID: {user?.id}</p>
          </div>
        </div>
      </div>
      
      <h1 style={{color: 'white'}}>Edit Your Preferences</h1>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit} className="preferences-form">
        <div className="form-section">
          <h2>Dietary Restrictions</h2>
          <div className="checkbox-group">
            {['vegetarian', 'vegan', 'gluten-free', 'dairy-free'].map(restriction => (
              <label key={restriction} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.dietary_restrictions.includes(restriction)}
                  onChange={() => handleCheckboxChange('dietary_restrictions', restriction)}
                />
                {restriction}
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h2>Favorite Cuisines</h2>
          <div className="checkbox-group">
            {['italian', 'mexican', 'indian', 'chinese', 'japanese', 'mediterranean'].map(cuisine => (
              <label key={cuisine} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.favorite_cuisines.includes(cuisine)}
                  onChange={() => handleCheckboxChange('favorite_cuisines', cuisine)}
                />
                {cuisine}
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h2>Cooking Skill Level</h2>
          <select
            value={preferences.cooking_skill_level}
            onChange={handleSelectChange}
            className="skill-select"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <div className="form-section">
          <h2>Health Goals</h2>
          <div className="checkbox-group">
            {['weight_loss', 'muscle_gain', 'heart_health', 'diabetes_management'].map(goal => (
              <label key={goal} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.health_goals.includes(goal)}
                  onChange={() => handleCheckboxChange('health_goals', goal)}
                />
                {goal.replace('_', ' ')}
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h2>Allergies</h2>
          <div className="checkbox-group">
            {['nuts', 'shellfish', 'eggs', 'soy'].map(allergy => (
              <label key={allergy} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={preferences.allergies.includes(allergy)}
                  onChange={() => handleCheckboxChange('allergies', allergy)}
                />
                {allergy}
              </label>
            ))}
          </div>
        </div>

        <button type="submit" className="save-button">Save Preferences</button>
      </form>
    </div>
  );
};

export default Profile; 