import axios from 'axios';

// Use REACT_APP_API_BASE_URL from environment or default to GCP Run URL
const API_URL = process.env.REACT_APP_API_BASE_URL || 'https://culinaryai-backend-428343023990.us-central1.run.app';

// Create an axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to add the auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Log responses for debugging
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response || error);
    return Promise.reject(error);
  }
);

// API Authentication functions
export const authAPI = {
  login: async (identifier: string, password: string) => {
    try {
      // Log the request details (without password)
      console.log('Login request with identifier:', identifier);
      
      // Use our custom login endpoint that accepts identifier (username or email)
      const response = await axios.post(`${API_URL}/auth/login`, {
        identifier,
        password,
      });
      
      console.log('Login response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Login request failed:', error);
      throw error;
    }
  },
  
  signup: async (email: string, username: string, password: string) => {
    try {
      console.log('Signup request for:', email, username);
      const response = await api.post('/auth/signup', {
        email,
        username,
        password,
      });
      console.log('Signup response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Signup request failed:', error);
      throw error;
    }
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// API Preference functions
export const preferenceAPI = {
  getPreferences: async () => {
    const response = await api.get('/preferences');
    return response.data;
  },
  
  updatePreferences: async (preferences: any) => {
    const response = await api.put('/preferences', preferences);
    return response.data;
  },
  
  submitQuestionnaire: async (questionnaireData: any) => {
    const response = await api.post('/preferences/questionnaire', questionnaireData);
    return response.data;
  },
};

export default api; 