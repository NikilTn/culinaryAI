import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

// Define password requirements
const MIN_PASSWORD_LENGTH = 8;
const PASSWORD_REQUIREMENTS = [
    { regex: /[a-z]/, message: "lowercase letter" },
    { regex: /[A-Z]/, message: "uppercase letter" },
    { regex: /[0-9]/, message: "number" },
    { regex: /[^A-Za-z0-9]/, message: "special character" }, // Matches anything not alphanumeric
];

// Define username requirements
const MIN_USERNAME_LENGTH = 3;
const USERNAME_REGEX = /^[a-zA-Z0-9_-]+$/; // Alphanumeric, underscore, hyphen

const SignupForm: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newPassword = e.target.value;
    setFormData({ ...formData, password: newPassword });
    validatePassword(newPassword);
    if (formData.confirmPassword) {
        if (newPassword !== formData.confirmPassword) {
            setPasswordError('Passwords do not match');
        } else {
            validatePassword(newPassword);
        }
    }
  };
  
  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newConfirmPassword = e.target.value;
      setFormData({ ...formData, confirmPassword: newConfirmPassword });
      if (formData.password !== newConfirmPassword) {
          setPasswordError('Passwords do not match');
      } else {
          validatePassword(formData.password);
      }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setError(null);
    if (name === 'username') {
      setUsernameError(null);
      validateUsername(value);
    }
    if (name === 'email') {
      setEmailError(null);
      if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          setEmailError("Please enter a valid email address.");
      }
    }
  };

  const validatePassword = (password: string): boolean => {
      if (!password) {
          setPasswordError(null);
          return false; 
      } 
      if (password.length < MIN_PASSWORD_LENGTH) {
          setPasswordError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long.`);
          return false;
      }
      const missingRequirements = PASSWORD_REQUIREMENTS
          .filter(req => !req.regex.test(password))
          .map(req => req.message);
          
      if (missingRequirements.length > 0) {
          setPasswordError(`Password must contain at least one ${missingRequirements.join(', ')}.`);
          return false;
      }
      
      setPasswordError(null);
      return true;
  }

  const validateUsername = (username: string): boolean => {
      if (!username) {
          setUsernameError(null);
          return false;
      }
      if (username.length < MIN_USERNAME_LENGTH) {
          setUsernameError(`Username must be at least ${MIN_USERNAME_LENGTH} characters long.`);
          return false;
      }
      if (!USERNAME_REGEX.test(username)) {
          setUsernameError('Username can only contain letters, numbers, underscores (_), and hyphens (-).');
          return false;
      }
      setUsernameError(null);
      return true;
  }

  const validateEmail = (email: string): boolean => {
      if (!email) {
          setEmailError("Email is required.");
          return false;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
          setEmailError("Please enter a valid email address.");
          return false;
      }
      setEmailError(null);
      return true;
  }

  const validateForm = (): boolean => {
    const isUsernameValid = validateUsername(formData.username);
    const isEmailValid = validateEmail(formData.email);
    const isPasswordValid = validatePassword(formData.password);
    let isConfirmPasswordValid = true;
    
    if (formData.password !== formData.confirmPassword) {
      setPasswordError('Passwords do not match');
      isConfirmPasswordValid = false;
    } else if (isPasswordValid) {
       // If password is valid and they match, clear mismatch error
       // validatePassword(formData.password) // This is implicitly called by isPasswordValid check
    }
    
    setError(null);
    if (!isUsernameValid || !isEmailValid || !isPasswordValid || !isConfirmPasswordValid) {
        // Specific errors are already set by individual validators
        // Optionally set a general error message too
        // setError("Please fix the errors in the form.");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Register the user
      await authAPI.signup(
        formData.email,
        formData.username,
        formData.password
      );

      // Login after successful registration
      await login(formData.username, formData.password);
      
      // Redirect to questionnaire after successful signup
      navigate('/questionnaire');
    } catch (err: any) {
      if (err.response && err.response.data) {
        setError(err.response.data.detail || 'Registration failed. Please try again.');
      } else {
        setError('Registration failed. Please try again.');
      }
      console.error('Signup error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-form">
      <h2>Join CulinaryAI</h2>
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email address"
            required
            className={emailError ? 'input-error' : ''}
          />
          {emailError && <p className="error-message field-error">{emailError}</p>}
        </div>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="Choose a username"
            required
            aria-describedby="username-help"
            className={usernameError ? 'input-error' : ''}
          />
          <small id="username-help" className="form-text text-muted">
            Min {MIN_USERNAME_LENGTH} characters. Letters, numbers, underscores, hyphens allowed.
          </small>
          {usernameError && <p className="error-message field-error">{usernameError}</p>}
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handlePasswordChange}
            placeholder="Create a password"
            required
            aria-describedby="password-help"
            className={passwordError && passwordError !== 'Passwords do not match' ? 'input-error' : ''}
          />
          <small id="password-help" className="form-text text-muted">
            Min {MIN_PASSWORD_LENGTH} characters. Must include uppercase, lowercase, number, and special character.
          </small>
          {passwordError && passwordError !== 'Passwords do not match' && <p className="error-message field-error">{passwordError}</p>}
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleConfirmPasswordChange}
            placeholder="Confirm your password"
            required
            className={passwordError === 'Passwords do not match' ? 'input-error' : ''}
          />
          {passwordError === 'Passwords do not match' && <p className="error-message field-error">{passwordError}</p>}
        </div>
        <button type="submit" disabled={loading}>
          {loading ? (
            <span>Creating Account...</span>
          ) : (
            <span>
              <span className="button-text">Sign Up</span>
              <span className="button-icon">→</span>
            </span>
          )}
        </button>
      </form>
    </div>
  );
};

export default SignupForm; 