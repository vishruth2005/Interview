import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Brain, FileText } from 'lucide-react';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-4xl mx-auto text-center">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl font-bold text-gray-900 mb-6"
      >
        Welcome to InterviewPro
      </motion.h1>
      
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-lg text-gray-600 mb-12"
      >
        Prepare for your dream job with AI-powered interview practice and create stunning resumes
      </motion.p>

      <div className="grid md:grid-cols-2 gap-8">
        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white p-8 rounded-xl shadow-sm cursor-pointer"
          onClick={() => navigate('/interview-prep')}
        >
          <div className="flex justify-center mb-4">
            <Brain size={48} className="text-primary" />
          </div>
          <h2 className="text-2xl font-semibold mb-4">AI Interview Prep</h2>
          <p className="text-gray-600">
            Practice interviews with our AI-powered system. Get real-time feedback and improve your skills.
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          className="bg-white p-8 rounded-xl shadow-sm cursor-pointer"
          onClick={() => navigate('/resume-builder')}
        >
          <div className="flex justify-center mb-4">
            <FileText size={48} className="text-primary" />
          </div>
          <h2 className="text-2xl font-semibold mb-4">Resume Builder</h2>
          <p className="text-gray-600">
            Create professional resumes with our easy-to-use builder. Stand out from the crowd.
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default Home; 