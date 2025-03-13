import React, { useState } from 'react'
import Welcome from './components/Welcome'
import Question from './components/Question'
import './App.css'

function App() {
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [userInfo, setUserInfo] = useState(null)

  const handleQuestionsGenerated = (questions, formData) => {
    setCurrentQuestion(questions)
    setUserInfo(formData)
  }

  const handleNextQuestion = (nextQuestion) => {
    setCurrentQuestion(nextQuestion)
  }

  return (
    <div className="app">
      {!currentQuestion ? (
        <Welcome onQuestionsGenerated={handleQuestionsGenerated} />
      ) : (
        <Question
          currentQuestion={currentQuestion}
          userInfo={userInfo}
          onNextQuestion={handleNextQuestion}
        />
      )}
    </div>
  )
}

export default App
