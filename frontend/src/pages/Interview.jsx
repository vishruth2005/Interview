import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Mic } from 'lucide-react';

const Interview = () => {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: 'Welcome to your interview! I will be your interviewer today. Let\'s begin with a brief introduction about yourself.'
    }
  ]);
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setMessages(prev => [...prev, { type: 'user', content: input }]);
    setInput('');

    // Dummy response for now
    setTimeout(() => {
      setMessages(prev => [...prev, {
        type: 'bot',
        content: 'Thank you for sharing that. Now, let me ask you about your experience with...'
      }]);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)]">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-xl shadow-sm h-full flex flex-col"
      >
        <div className="p-6 border-b">
          <h2 className="text-2xl font-semibold">Interview Session</h2>
          <p className="text-gray-600">AI Interviewer is ready to help you practice</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-4 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {message.content}
              </div>
            </motion.div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="p-4 border-t">
          <div className="flex items-center space-x-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              type="button"
              className="p-2 text-gray-500 hover:text-primary"
            >
              <Mic size={24} />
            </motion.button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your response..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              type="submit"
              className="p-2 text-primary hover:text-primary-dark"
            >
              <Send size={24} />
            </motion.button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};

export default Interview; 