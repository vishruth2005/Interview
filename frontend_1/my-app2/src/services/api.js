const API_BASE_URL = 'http://127.0.0.1:8000/interview';

const headers = {
  'Content-Type': 'application/json',
};

export const generateQuestions = async (role, company, resumeContent) => {
  const response = await fetch(`${API_BASE_URL}/generate_interview_questions/`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      role,
      company,
      resume_content: resumeContent,
    }),
  });
  return response.json();
};

export const submitAnswer = async (role, company, resumeContent, answer) => {
  const response = await fetch(`${API_BASE_URL}/submit_answer/`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      role,
      company,
      resume_content: resumeContent,
      answer,
    }),
  });
  return response.json();
};

export const getNextQuestion = async () => {
  const response = await fetch(`${API_BASE_URL}/next_question/`, {
    method: 'GET',
    headers,
  });
  return response.json();
}; 