import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

function InterviewSystem() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    role: "",
    company: "",
    resume: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/interview/generate_interview_questions/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            role: formData.role,
            company: formData.company,
            resume_content: formData.resume,
          }),
        }
      );

      const data = await response.json();

      if (data.message === "Interview questions generated successfully.") {
        navigate("/interview-questions", { state: formData });
      } else {
        setError("Failed to generate questions. Please try again.");
      }
    } catch (err) {
      setError("An error occurred. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center py-8 px-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
          Generate Interview Questions
        </h1>

        {error && <p className="text-red-500 text-center mb-4">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 mb-2">Role</label>
            <input
              type="text"
              className="w-full p-2 border border-gray-300 rounded-lg"
              value={formData.role}
              onChange={(e) => setFormData((prev) => ({ ...prev, role: e.target.value }))}
              placeholder="e.g. Senior Software Engineer"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Company</label>
            <input
              type="text"
              className="w-full p-2 border border-gray-300 rounded-lg"
              value={formData.company}
              onChange={(e) => setFormData((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="e.g. Google"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Resume</label>
            <textarea
              className="w-full p-2 border border-gray-300 rounded-lg h-32"
              value={formData.resume}
              onChange={(e) => setFormData((prev) => ({ ...prev, resume: e.target.value }))}
              placeholder="Paste your resume content here"
              required
            />
          </div>

          <div className="flex justify-between">
            <Link to="/" className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600">
              Back
            </Link>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate Questions"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default InterviewSystem;