import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import QuestionnaireForm from '../components/questionnaire/QuestionnaireForm';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import '../styles/Questionnaire.css';

const Questionnaire: React.FC = () => {
  const { isAuthenticated } = useAuth();

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return (
    <div className="questionnaire-page">
      <QuestionnaireForm />
    </div>
  );
};

export default Questionnaire; 