import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Building2, Briefcase, Download, Upload, X } from "lucide-react";

function InterviewSystem() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    role: "",
    company: "",
    resume_content: "",
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      
      // Read the file content
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        setFormData(prev => ({
          ...prev,
          resume_content: text
        }));
      };
      reader.readAsText(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setFormData(prev => ({
      ...prev,
      resume_content: ""
    }));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.resume_content) {
      setError("Please upload a resume file");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/interview/generate_interview_questions/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          resume_content: formData.resume_content,
          role: formData.role,
          company: formData.company,
        }),
      });

      const data = await response.json();

      if (data.message === "Interview questions generated successfully.") {
        navigate("/interview-questions", { state: formData });
      } else {
        setError("Failed to generate questions. Please try again.");
      }
    } catch (error) {
      console.error("Error:", error);
      setError("Failed to generate questions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fd]">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            AI Interview System
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Practice your interview with our AI Interview System
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="space-y-6">
              <div>
                <label htmlFor="resume_upload" className="flex items-center text-base font-medium text-gray-900 mb-3">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Resume Upload
                </label>
                <div className="relative">
                  {!selectedFile ? (
                    <div
                      className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="w-8 h-8 mx-auto mb-4 text-gray-400" />
                      <p className="text-gray-600 mb-2">
                        Drop your file here or <span className="text-blue-600">browse</span>
                      </p>
                      <p className="text-sm text-gray-500">Supported formats: TXT, DOC, DOCX</p>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between bg-blue-50 rounded-xl p-4">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-blue-600 mr-3" />
                        <span className="text-gray-900 font-medium">{selectedFile.name}</span>
                      </div>
                      <button type="button" onClick={removeFile} className="text-gray-500 hover:text-gray-700">
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  )}
                  <input 
                    type="file" 
                    id="resume_upload" 
                    ref={fileInputRef} 
                    className="hidden" 
                    accept=".txt,.doc,.docx" 
                    onChange={handleFileChange}
                    required 
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="role" className="flex items-center text-base font-medium text-gray-900 mb-3">
                    <Briefcase className="w-5 h-5 mr-2 text-blue-600" />
                    Role
                  </label>
                  <input
                    type="text"
                    id="role"
                    name="role"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="e.g. Senior Frontend Developer"
                    value={formData.role}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="company" className="flex items-center text-base font-medium text-gray-900 mb-3">
                    <Building2 className="w-5 h-5 mr-2 text-blue-600" />
                    Company
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="e.g. Google"
                    value={formData.company}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </div>

            <div>
              <button
                type="submit"
                className={`w-full flex items-center justify-center px-6 py-4 border border-transparent text-lg font-medium rounded-xl text-white ${
                  loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
                } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200`}
                disabled={loading || !selectedFile}
              >
                {loading ? "Generating..." : (
                  <>
                    <Download className="w-5 h-5 mr-2" />
                    Generate Questions
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          Your data is processed locally and never stored or shared
        </div>
      </div>
    </div>
  );
}

export default InterviewSystem;