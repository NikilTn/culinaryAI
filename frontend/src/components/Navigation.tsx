import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Navigation.css';

const Navigation: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="logo">
        <Link to="/">CulinaryAI</Link>
      </div>
      <div className="nav-links">
        {isAuthenticated ? (
          <>
            <Link to="/">Home</Link>
            <Link to="/recommendations">Recommendations</Link>
            <Link to="/preferences">My Preferences</Link>
            <Link to="/profile">Profile</Link>
            <Link to="/explore">Explore</Link>
            <button onClick={logout} className="nav-button">Logout</button>
          </>
        ) : (
          <Link to="/auth">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navigation; 