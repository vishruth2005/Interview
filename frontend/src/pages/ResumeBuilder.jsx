import React, { useState, useRef } from "react";
import { FileText, Building2, Briefcase, Download, Upload, X } from "lucide-react";

function ResumeBuilder() {
  const [formData, setFormData] = useState({
    role: "",
    company: "",
  });
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const requestBody = {
      resume_content: "Good experience in software development", // Modify this if you extract content from PDF
      role: formData.role,
      company: formData.company,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/cheatsheet/generate-pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error("Failed to generate PDF");

      // Convert response into Blob (PDF File)
      const blob = await response.blob();
      const pdfUrl = window.URL.createObjectURL(blob);

      // Create a temporary link & trigger download
      const link = document.createElement("a");
      link.href = pdfUrl;
      link.download = "cheat-sheet.pdf";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fd]">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            Cheat Sheet Generator
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Transform your resume into a concise interview cheat sheet in seconds
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
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
                        Drop your PDF here or <span className="text-blue-600">browse</span>
                      </p>
                      <p className="text-sm text-gray-500">Supported format: PDF</p>
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
                  <input type="file" id="resume_upload" ref={fileInputRef} className="hidden" accept=".pdf" onChange={handleFileChange} />
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
                disabled={loading}
              >
                {loading ? "Generating..." : (
                  <>
                    <Download className="w-5 h-5 mr-2" />
                    Generate Cheat Sheet
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

export default ResumeBuilder;
