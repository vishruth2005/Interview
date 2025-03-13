import React, { useState } from 'react';
import { generateQuestions } from '../services/api';
import './Welcome.css';

const Welcome = ({ onQuestionsGenerated }) => {
  const [formData, setFormData] = useState({
    role: '',
    company: '',
    resumeContent: '',
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const questions = await generateQuestions(
        formData.role,
        formData.company,
        formData.resumeContent
      );
      onQuestionsGenerated(questions, formData);
    } catch (error) {
      console.error('Error generating questions:', error);
      alert('Failed to generate questions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="welcome-container">
      <h1>Welcome to AI Interview</h1>
      <form onSubmit={handleSubmit} className="welcome-form">
        <div className="form-group">
          <label htmlFor="role">Role:</label>
          <input
            type="text"
            id="role"
            name="role"
            value={formData.role}
            onChange={handleChange}
            placeholder="e.g., Software Developer"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="company">Company:</label>
          <input
            type="text"
            id="company"
            name="company"
            value={formData.company}
            onChange={handleChange}
            placeholder="e.g., Amazon"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="resumeContent">Resume Content:</label>
          <textarea
            id="resumeContent"
            name="resumeContent"
            value={formData.resumeContent}
            onChange={handleChange}
            placeholder="Paste your resume content here..."
            required
            rows={6}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Generating Questions...' : 'Generate Questions'}
        </button>
      </form>
    </div>
  );
};

export default Welcome; 