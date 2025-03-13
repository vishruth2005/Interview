import { Routes, Route, Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import InterviewPrep from './pages/InterviewPrep';
import Interview from './pages/Interview';
import ResumeBuilder from './pages/ResumeBuilder';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="container mx-auto px-4 py-8"
      >
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/interview-prep" element={<InterviewPrep />} />
          <Route path="/interview" element={<Interview />} />
          <Route path="/resume-builder" element={<ResumeBuilder />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </div>
  );
}

export default App;
