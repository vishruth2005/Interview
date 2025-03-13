import { Link } from 'react-router-dom';
import { FaFileAlt, FaUserTie } from 'react-icons/fa';

function Welcome() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">
          AI Interview System
        </h1>
        
        <div className="max-w-4xl mx-auto bg-secondary rounded-lg p-8">
          <h2 className="text-2xl font-semibold text-center text-gray-700 mb-8">
            Get Started with AI Interview System...
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="flex justify-center mb-4">
                <FaUserTie className="text-6xl text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-4">AI Interview Prep</h3>
              <p className="text-gray-600 mb-6">
                Prepare for your interviews with our latest AI Interview Prep
              </p>
              <Link to="/interview-system" className="btn-primary inline-block">
                Proceed
              </Link>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="flex justify-center mb-4">
                <FaFileAlt className="text-6xl text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-4">Resume Builder</h3>
              <p className="text-gray-600 mb-6">
                Generate Resume with our latest AI Resume Builder
              </p>
              <Link to="/resume-builder" className="btn-primary inline-block">
                Proceed
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Welcome;