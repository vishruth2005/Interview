import { useState } from 'react';
import { Link } from 'react-router-dom';

// Mock questions - in a real app, these would come from an API


function InterviewQuestions() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [showWelcome, setShowWelcome] = useState(true);
  const [questionId, setQuestionId] = useState(0);

  const handleSubmitAnswer = () => {
    if (!answer) {
      setFeedback("Please enter an answer before submitting.");
      return;
    }
  
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
  
    const raw = JSON.stringify(answer); // Send the answer as a plain string
  
    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw, // Directly send the string
      redirect: "follow",
    };
  
    fetch(`http://127.0.0.1:8000/interview/evaluate_answer/${questionId}`, requestOptions)
      .then((response) => response.text()) // API returns plain text
      .then((result) => {
        console.log(result); // Log API response
        setFeedback(result); // Display response as feedback
      })
      .catch((error) => {
        console.error("Error:", error);
        setFeedback("There was an error submitting your answer.");
      });
  };
  
  
  const handleNextQuestion = () => {
    const requestOptions = {
      method: "GET",
      redirect: "follow"
    };
  
    fetch("http://127.0.0.1:8000/interview/next_question/", requestOptions)
      .then((response) => response.json()) // Expecting a JSON response
      .then((data) => {
        if (data.question && data.question.question) {
          setCurrentQuestion(data.question.question); // Store only the question text
          setQuestionId(questionId+1);
          setAnswer(''); // Reset answer input
          setFeedback(''); // Clear previous feedback
        } else {
          setFeedback("No more questions available.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        setFeedback("There was an error fetching the next question.");
      });
  };
  
  

  if (showWelcome) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8 text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">
            Welcome to the AI Interview System
          </h1>
          <p className="text-gray-600 mb-8">
            Get ready for your interview! Click the button below to start answering questions.
          </p>
          <button
            onClick={() => setShowWelcome(false)}
            
            className="btn-primary"
          >
            Start Interview
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8">
        <div className="mb-8">
  {questionId === 0 && (
    <div className="bg-blue-100 border-l-4 border-blue-500 p-4 rounded-lg shadow-md mb-4">
      <h3 className="text-lg font-semibold text-blue-800">Welcome to the AI Interview System</h3>
      <p className="text-gray-700 mt-2">
        - Answer questions clearly and concisely. <br />
        - Ensure your responses are structured and relevant to the topic. <br />
        - Good luck with your interview!
      </p>
    </div>
  )}
  {questionId!==0 && (
  <h2 className="text-2xl font-bold text-gray-800 mb-4">
    Question {questionId}: {currentQuestion}
  </h2>
  )}
  <p className="text-gray-700 text-lg"></p>
</div>

          <div className="mb-6">
            <textarea
              className="input-field h-32"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={questionId==0 ? "Please type- 'I will follow all the instructions'" : "Type your answer help"}
            />
          </div>

          {feedback && (
            <div className="mb-6 p-4 bg-green-50 text-green-700 rounded-lg">
              {feedback}
            </div>
          )}

          <div className="flex justify-between">
            <Link to="/" className="btn-primary bg-gray-500">
              Exit Interview
            </Link>
            <div className="space-x-4">
              <button
                onClick={handleSubmitAnswer}
                className="btn-primary"
                disabled={!answer}
              >
                Submit Answer
              </button>
              <button
                onClick={handleNextQuestion}
                className="btn-primary"
              >
                Next Question
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InterviewQuestions;