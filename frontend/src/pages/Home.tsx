import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import '../styles/Home.css';

const Home: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="home-container">  
      <div className="hero-section">
        <div className="hero-content">
          <h1 style={{color: 'white'}}>Welcome to CulinaryAI</h1>
          <p className="tagline" style={{color: 'white'}}>Your personal AI chef for delicious recipe recommendations</p>
        </div>
      </div>
      
      {user ? (
        <div className="user-welcome">
          <h2>Hello, {user.username}!</h2>
          <p>You are now logged in. You can start exploring culinary recommendations.</p>
          <div className="home-actions">
            <Link to="/recommendations" className="home-button primary">
              View Recommendations
            </Link>
            <Link to="/preferences" className="home-button secondary">
              Update Preferences
            </Link>
            <button onClick={logout} className="home-button logout">
              Logout
            </button>
          </div>
        </div>
      ) : (
        <div className="guest-welcome">
          <p>Please log in to get personalized culinary recommendations.</p>
        </div>
      )}

      <div className="features-section">
        <h2>Why Choose CulinaryAI?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🍳</div>
            <h3>Personalized Recommendations</h3>
            <p>Get recipe suggestions tailored to your unique taste preferences and dietary needs.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI-Powered</h3>
            <p>Our advanced AI analyzes your preferences to recommend dishes you'll love.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Smart Search</h3>
            <p>Find recipes based on ingredients, cuisine type, or cooking time.</p>
          </div>
        </div>
      </div>

      <div className="testimonial-section">
        <blockquote>
          "CulinaryAI transformed how I cook at home. The personalized recommendations are spot on!"
        </blockquote>
        <cite>- Maria Johnson, Food Enthusiast</cite>
        <div className="testimonial-image"></div>
      </div>
    </div>
  );
};

export default Home; 