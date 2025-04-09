# IntervueAI

An AI-powered mock interview platform that conducts real-time, voice-based technical interviews. It parses a candidate's resume and GitHub profile to generate personalized questions, evaluates answers with an LLM-driven Q&A agent, and scores responses on clarity, relevance, and technical depth.

## Features

- **Automated Resume Parsing** — Extracts skills, experience, and project details from uploaded resumes (PDF) with 90%+ field extraction accuracy.
- **GitHub-Linked Context** — Pulls repository and profile metadata via the GitHub API to tailor interview questions to a candidate's actual projects and tech stack.
- **Context-Aware Q&A Agent** — Built on the Phidata agent framework with Google Gemini, the agent asks dynamic follow-up questions based on candidate responses rather than a fixed question bank.
- **Real-Time Voice Interaction** — Uses ElevenLabs for natural-sounding voice output, enabling a live, conversational interview experience over WebSockets.
- **Automated Scoring** — Evaluates each response on clarity, relevance, and technical depth, and surfaces structured feedback at the end of the session.
- **Interactive UI** — Streamlit-based interface combining voice input, live transcripts, and feedback in a single dashboard.

## Tech Stack

| Layer | Technologies |
|---|---|
| AI / Agent | Phidata, Google Gemini (`google-generativeai`) |
| Voice | ElevenLabs |
| Backend | FastAPI-style services with `uvicorn` + `websockets` for real-time streaming |
| Data / Parsing | PyPDF2 (resume parsing), PyGithub (GitHub metadata) |
| Storage | SQLAlchemy |
| Frontend | Streamlit, JavaScript |

## Project Structure

```
Interview/
├── backend/          # Core agent logic, resume/GitHub parsing, voice + Q&A pipeline
├── frontend/          # Streamlit / JS interface for the interview experience
└── requirements.txt   # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.10+
- API keys for Google Gemini and ElevenLabs
- A GitHub personal access token (for GitHub metadata parsing)

### Installation

```bash
git clone https://github.com/vishruth2005/Interview.git
cd Interview
pip install -r requirements.txt
```

Create a `.env` file in the project root with your credentials:

```
GOOGLE_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GITHUB_TOKEN=your_github_token
```

### Running the App

```bash
streamlit run frontend/app.py
```

> Update the entry-point path above if your Streamlit app file lives elsewhere in `frontend/`.

## How It Works

1. **Upload** — Candidate uploads a resume (and optionally links a GitHub profile).
2. **Parse** — The backend extracts skills, experience, and repository data.
3. **Interview** — The Q&A agent asks context-aware questions via voice, with dynamic follow-ups based on the candidate's answers.
4. **Score** — Responses are evaluated and a feedback summary is generated covering clarity, relevance, and technical depth.