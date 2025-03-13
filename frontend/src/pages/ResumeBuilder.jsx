import { motion } from 'framer-motion';
import { FileText, Download, Plus } from 'lucide-react';

const ResumeBuilder = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white p-8 rounded-xl shadow-sm"
      >
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-semibold">Resume Builder</h2>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 bg-primary text-white px-4 py-2 rounded-lg"
          >
            <Download size={20} />
            <span>Export PDF</span>
          </motion.button>
        </div>

        <div className="space-y-8">
          {/* Personal Information */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Personal Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Full Name"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <input
                type="email"
                placeholder="Email"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <input
                type="tel"
                placeholder="Phone"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
              <input
                type="text"
                placeholder="Location"
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </section>

          {/* Professional Summary */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Professional Summary</h3>
            <textarea
              rows="4"
              placeholder="Write a brief summary of your professional background and goals..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </section>

          {/* Work Experience */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Work Experience</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center space-x-2 text-primary"
              >
                <Plus size={20} />
                <span>Add Experience</span>
              </motion.button>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300 text-center text-gray-500">
              <FileText size={32} className="mx-auto mb-2" />
              <p>Click "Add Experience" to add your work history</p>
            </div>
          </section>

          {/* Education */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Education</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center space-x-2 text-primary"
              >
                <Plus size={20} />
                <span>Add Education</span>
              </motion.button>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300 text-center text-gray-500">
              <FileText size={32} className="mx-auto mb-2" />
              <p>Click "Add Education" to add your educational background</p>
            </div>
          </section>

          {/* Skills */}
          <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Skills</h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center space-x-2 text-primary"
              >
                <Plus size={20} />
                <span>Add Skill</span>
              </motion.button>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-dashed border-gray-300 text-center text-gray-500">
              <FileText size={32} className="mx-auto mb-2" />
              <p>Click "Add Skill" to add your technical and soft skills</p>
            </div>
          </section>
        </div>
      </motion.div>
    </div>
  );
};

export default ResumeBuilder; 