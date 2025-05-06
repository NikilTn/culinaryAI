import React, { useState, useEffect } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { preferenceAPI } from '../services/api';
import '../styles/UserPreferences.css';

// Edit icon SVG component
const EditIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M16.4745 5.40801L18.5917 7.52524M17.8358 3.54289L11.6716 9.70711C11.2725 10.1062 11.0371 10.3032 10.842 10.5281C10.647 10.7532 10.5003 11.0022 10.206 11.5V11.5L9 15L12.5 13.794C12.9978 13.4997 13.2468 13.353 13.4719 13.158C13.6968 12.9629 13.8938 12.7275 14.2929 12.3284L20.4571 6.16421C21.232 5.38934 21.232 4.11776 20.4571 3.34289C19.6823 2.56802 18.4107 2.56802 17.6358 3.34289L17.8358 3.54289Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M19 15V18C19 19.1046 18.1046 20 17 20H7C5.89543 20 5 19.1046 5 18V8C5 6.89543 5.89543 6 7 6H10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

interface Preference {
  user_id: number;
  dietary_restrictions: string[];
  favorite_cuisines: string[];
  cooking_skill_level: string;
  health_goals: string[];
  allergies: string[];
}

const UserPreferences: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<Preference | null>(null);

  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        const data = await preferenceAPI.getPreferences();
        console.log('Fetched preferences:', data);
        setPreferences(data);
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching preferences:', err);
        // Only set error if it's not a 404 (no preferences yet)
        if (err.response && err.response.status !== 404) {
          setError('Failed to load preferences. Please try again.');
        }
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchPreferences();
    }
  }, [isAuthenticated]);

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  // Show loading state
  if (loading) {
    return <div className="loading">Loading preferences...</div>;
  }

  // Format list for display
  const formatList = (items: string[]) => {
    if (!items || items.length === 0) return 'None selected';
    return items.join(', ');
  };

  return (
    <div className="preferences-container">
      <h1 style={{color: 'white'}}>Your Culinary Preferences</h1>
      
      {error && <div className="error-message">{error}</div>}
      
      {!preferences ? (
        <div className="no-preferences">
          <p>You haven't set up your preferences yet.</p>
          <Link to="/questionnaire" className="questionnaire-link">
            Complete the Questionnaire
          </Link>
        </div>
      ) : (
        <div className="preferences-content">
          <div className="preferences-section">
            <h2>Cuisine Preferences</h2>
            <div className="preference-item">
              <strong>Favorite Cuisines:</strong> {formatList(preferences.favorite_cuisines)}
            </div>
          </div>
          
          <div className="preferences-section">
            <h2>Dietary Restrictions</h2>
            <div className="preference-item">
              {formatList(preferences.dietary_restrictions)}
            </div>
          </div>
          
          <div className="preferences-section">
            <h2>Health Goals</h2>
            <div className="preference-item">
              {formatList(preferences.health_goals)}
            </div>
          </div>
          
          <div className="preferences-section">
            <h2>Allergies</h2>
            <div className="preference-item">
              {formatList(preferences.allergies)}
            </div>
          </div>
          
          <div className="preferences-section">
            <h2>Cooking Details</h2>
            <div className="preference-item">
              <strong>Skill Level:</strong> {preferences.cooking_skill_level.charAt(0).toUpperCase() + preferences.cooking_skill_level.slice(1)}
            </div>
          </div>
          
          <div className="action-buttons">
            <Link to="/questionnaire" className="edit-button">
              <EditIcon /> Edit Preferences
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserPreferences; 