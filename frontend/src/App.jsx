import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Welcome from './pages/Welcome';
import ResumeBuilder from './pages/ResumeBuilder';
import InterviewSystem from './pages/InterviewSystem';
import InterviewQuestions from './pages/InterviewQuestions';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/resume-builder" element={<ResumeBuilder />} />
          <Route path="/interview-system" element={<InterviewSystem />} />
          <Route path="/interview-questions" element={<InterviewQuestions />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;