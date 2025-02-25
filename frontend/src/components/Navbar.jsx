import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, FileText } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <motion.div
              whileHover={{ scale: 1.1 }}
              className="text-primary font-bold text-xl"
            >
              InterviewPro
            </motion.div>
          </Link>
          
          <div className="flex space-x-4">
            <Link
              to="/interview-prep"
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                isActive('/interview-prep')
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Brain size={20} />
              <span>AI Interview Prep</span>
            </Link>
            
            <Link
              to="/resume-builder"
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                isActive('/resume-builder')
                  ? 'bg-primary text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <FileText size={20} />
              <span>Resume Builder</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 