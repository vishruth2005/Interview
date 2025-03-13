import React, { useState } from 'react';
import { submitAnswer, getNextQuestion } from '../services/api';
import './Question.css';

const Question = ({ currentQuestion, userInfo, onNextQuestion }) => {
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await submitAnswer(
        userInfo.role,
        userInfo.company,
        userInfo.resumeContent,
        answer
      );
      setFeedback(response);
    } catch (error) {
      console.error('Error submitting answer:', error);
      alert('Failed to submit answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNextQuestion = async () => {
    setLoading(true);
    try {
      const nextQuestion = await getNextQuestion();
      setAnswer('');
      setFeedback(null);
      onNextQuestion(nextQuestion);
    } catch (error) {
      console.error('Error getting next question:', error);
      alert('Failed to get next question. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="question-container">
      <div className="question-header">
        <h2>Interview Question</h2>
        <div className="interview-info">
          <span>Role: {userInfo.role}</span>
          <span>Company: {userInfo.company}</span>
        </div>
      </div>

      <div className="question-content">
        <p>{currentQuestion}</p>
      </div>

      <form onSubmit={handleSubmit} className="answer-form">
        <div className="form-group">
          <label htmlFor="answer">Your Answer:</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer here..."
            rows={6}
            required
            disabled={loading || feedback}
          />
        </div>

        {!feedback && (
          <button type="submit" disabled={loading || !answer.trim()}>
            {loading ? 'Submitting...' : 'Submit Answer'}
          </button>
        )}
      </form>

      {feedback && (
        <div className="feedback-section">
          <h3>Feedback</h3>
          <div className="feedback-content">
            {feedback}
          </div>
          <button
            onClick={handleNextQuestion}
            disabled={loading}
            className="next-question-btn"
          >
            {loading ? 'Loading...' : 'Next Question'}
          </button>
        </div>
      )}
    </div>
  );
};

export default Question; 