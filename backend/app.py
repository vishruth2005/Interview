import streamlit as st
import json
import random
from typing import Dict, List
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests

import PyPDF2
import os
from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
from phi.storage.agent.sqlite import SqlAgentStorage
from dotenv import load_dotenv
from streamlit import session_state
from Agents.QuestionGenerator import QuestionGenerator
from Agents.ResumeBuilder import ResumeBuilder
import time
from utils.voice_utils import text_to_speech_elevenlabs, speech_to_text_assemblyai, cleanup_audio_file, text_to_speech_gemini, speech_to_text_groq
from fpdf import FPDF
from datetime import datetime
import base64
import io
from Agents.document import CheatsheetGenerator
from utils.auth_utils import verify_google_token, save_user_to_firebase, check_session_validity, init_session, clear_session

load_dotenv()

# Configure Streamlit page
st.set_page_config(

    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 100%;
        margin: 0 auto;
        background-color: #ffffff;
    }
    /* Navigation bar styling */
    .css-1d391kg {
        background-color: #ffffff !important;
    }
    .css-1d391kg .st-emotion-cache-1v0mbdj {
        background-color: #ffffff !important;
    }
    /* Top header bar styling (contains Deploy) */
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
    }
    .st-emotion-cache-19rxjzo {
        background-color: #ffffff !important;
    }
    .st-emotion-cache-1dp5vir {
        background-color: #ffffff !important;
    }
    .st-emotion-cache-1erivf3 {
        background-color: #ffffff !important;
    }
    /* Change text color in header to ensure visibility */
    header[data-testid="stHeader"] button, 
    header[data-testid="stHeader"] span, 
    header[data-testid="stHeader"] a, 
    header[data-testid="stHeader"] div {
        color: #4f46e5 !important;
    }
    /* Center all text */
    .stMarkdown {
        text-align: center;
        color: #000000;
    }
    .stTitle {
        text-align: center;
    }
    .stTextInput > div > div > input {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 16px !important;
        height: 48px;
        background-color: #ffffff;
        color: #000000;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4f46e5;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
        outline: none;
    }
    .stTextInput > div > div > input:hover {
        border-color: #4f46e5;
    }
    .stFileUploader > div {
        width: 100%;
    }
    .stFileUploader > div > div {
        border: 2px solid #000000;
        border-radius: 8px;
        padding: 20px;
        background-color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 80px;
    }
    .stFileUploader > div > div:hover {
        border-color: #4f46e5;
    }
    .stFileUploader > div > div > div {
        color: #000000 !important;
        font-size: 20px;
    }
    .stFileUploader > div > div > button {
        background-color: #4f46e5 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-left: 15px !important;
    }
    .stFileUploader > div > div > button:hover {
        background: linear-gradient(90deg, #4338ca, #6d28d9);
    }
    .stFileUploader > div > div > div > div:first-child {
        color: #000000;
    }
    .voice-input-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .feature-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 40px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 2px solid #e6e9ef;
        position: relative;
        overflow: hidden;
        text-align: center;
    }
    .feature-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 6px;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
    }
    .feature-box:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        border-color: #4f46e5;
    }
    .feature-title {
        color: #000000;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 15px;
        text-align: center;
    }
    .feature-description {
        color: #000000;
        font-size: 16px;
        line-height: 1.6;
        flex-grow: 1;
        text-align: center;
    }
    .feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
        color: #4f46e5;
        text-align: center;
    }
    .stButton > button {
        background-color: #4f46e5 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 15px 30px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        width: 100%;
        max-width: 300px;
        margin: 10px auto;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #4338ca !important;
        transform: translateY(-2px);
    }
    /* Override Streamlit's default background */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 20px;
    }
    /* Custom header styling */
    .custom-header {
        text-align: center;
        color:rgb(255, 253, 253);
        margin-bottom: 60px;
        font-size: 36px;
        font-weight: 800;
        position: relative;
    }
    .custom-header::after {
        content: '';
        display: block;
        width: 60px;
        height: 4px;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        margin: 15px auto;
        border-radius: 2px;
    }
    .subtitle {
        text-align: center;
        color: #000000;
        font-size: 18px;
        margin-bottom: 40px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    /* Center all content */
    .element-container {
        text-align: center;
    }
    /* Center the title */
    .stTitle h1 {
        text-align: center;
        color: #000000;
    }
    /* Form labels */
    .stTextInput > label {
        color: #000000;
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    /* Section headers */
    .section-header {
        color: #000000;
        font-size: 32px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 40px;
    }
    /* Spacing between form elements */
    .stTextInput {
        margin-bottom: 20px;
    }
    /* Form container */
    .form-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 30px;
    }
    /* Remove default Streamlit button styling */
    .stButton > button[data-baseweb="button"] {
        background-color: #4f46e5 !important;
    }
    /* Modern file upload container */
    .upload-container {
        background: linear-gradient(145deg, #ffffff, #f5f7ff);
        border-radius: 16px;
        padding: 40px;
        margin: 30px 0;
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.1);
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .upload-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #4f46e5, #6366f1);
    }

    /* File uploader styling */
    .stFileUploader > div {
        width: 100%;
    }
    
    .stFileUploader > div > div {
        border: 2px solid #000000;
        border-radius: 8px;
        padding: 20px;
        background-color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 80px;
    }

    /* Change all text inside file uploader to black */
    .stFileUploader > div > div > div {
        color: #000000 !important;
        font-size: 18px;
    }

    /* Make sure the file size limit text is black */
    .stFileUploader > div > div > div small {
        color: #000000 !important;
    }

    /* Make sure the "Drag and drop" text is black */
    .stFileUploader > div > div > div:first-child {
        color: #000000 !important;
    }

    /* Make sure the filename text is black */
    .stFileUploader > div > div > div:last-child {
        color: #000000 !important;
    }

    /* Style the browse files button */
    .stFileUploader > div > div > button {
        background-color: #4f46e5 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-left: 15px !important;
    }

    .stFileUploader > div > div > button:hover {
        background-color: #4338ca !important;
    }

    /* Uploaded file name styling */
    .stFileUploader > div > div > div:last-child {
        color: #000000 !important;
        font-weight: 600;
    }

    /* Upload instructions */
    .upload-instructions {
        color: #6b7280;
        font-size: 14px;
        margin-top: 12px;
        font-weight: 500;
    }

    /* Target all text elements within the file uploader */
    .stFileUploader p,
    .stFileUploader span,
    .stFileUploader div {
        color: #000000 !important;
    }

    /* Target the drag and drop text specifically */
    .stFileUploader [data-testid="stFileUploadDropzone"] {
        color: #000000 !important;
    }

    /* Target the filename text */
    .stFileUploader [data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }

    /* Chat input styling */
    .stChatInput > div > div > input {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 16px !important;
        height: 48px;
        background-color: #ffffff;
        color: #000000;
        width: 100%;
        transition: all 0.2s ease;
    }

    .stChatInput > div > div > input:focus {
        border-color: #4f46e5;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
        outline: none;
    }

    .stChatInput > div > div > input:hover {
        border-color: #4f46e5;
    }

    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 20px 80px 20px;
        display: flex;
        flex-direction: column;
        position: relative;
        min-height: 80vh;
        background-color: #ffffff;
    }
    
    /* Question box at the top */
    .question-container {
        position: sticky;
        top: 0;
        background-color: #ffffff;
        padding: 15px 0 15px 0;
        z-index: 100;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 10px;
    }
    
    .question-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        text-align: left;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        width: 100%;
    }
    
    .question-text {
        color: #000000;
        font-size: 16px;
        font-weight: 500;
        line-height: 1.5;
        margin: 0;
    }
    
    .audio-player-container {
        width: 100%;
        margin: 10px 0 10px 0;
    }
    
    /* Chat message styling */
    .chat-messages {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-bottom: 20px;
        width: 100%;
    }
    
    .message-group {
        display: flex;
        flex-direction: column;
        width: 100%;
    }
    
    .message {
        padding: 12px 16px;
        border-radius: 12px;
        max-width: 80%;
        margin-bottom: 5px;
        font-size: 15px;
        line-height: 1.5;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin: 8px 0;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        color: #000000;
        text-align: left;
    }
    
    .assistant-message-container {
        display: flex;
        justify-content: flex-start;
        width: 100%;
        margin: 8px 0;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        border: 1px solid #e0e0e0;
        color: #000000;
        text-align: left;
    }
    
    .assistant-audio-container {
        margin: 5px 0 15px 0;
        max-width: 80%;
    }
    
    /* Input section styling */
    .input-container {
        position: sticky;
        bottom: 0;
        background-color: #ffffff;
        padding: 15px 0;
        border-top: 1px solid #e5e7eb;
        margin-top: auto;
        width: 100%;
    }
    
    .input-tabs {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .tab-content {
        padding: 10px;
    }
    
    .voice-input-section {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    
    /* Exit button styling */
    .exit-button-container {
        position: absolute;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    
    .exit-button-container button {
        background-color: #4f46e5 !important;
        color: white !important;
    }
    
    .exit-button-container button:hover {
        background-color: #4338ca !important;
    }
    
    /* Override Streamlit's default styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        color: #000000 !important;
    }
    
    .stAudio > div {
        margin: 0 auto;
    }
    
    .stMarkdown, .stText, p {
        color: #000000 !important;
    }
    
    /* Chat input styling */
    .stChatInput {
        margin-bottom: 10px;
    }

    /* Timer styling */
    .timer-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #ffffff;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 600;
        border: 2px solid #e5e7eb;
    }

    .timer-warning {
        color: #ef4444;
        animation: pulse 2s infinite;
    }

    .timer-normal {
        color: #1f2937;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

def to_json(data_string):
    # Format the string with normal string methods instead of f-string
    formatted_string = '[' + data_string.replace('}\n{', '}, {') + ']'
    json_data = json.loads(formatted_string)
    return json.dumps(json_data, indent=4)

def extract_text_from_pdf(pdf_content):
    """Extract text from a PDF file content."""
    reader = PyPDF2.PdfReader(pdf_content)
    text = ''.join([page.extract_text() for page in reader.pages])
    return text

class QuestionSelector:
    def __init__(self):
        self.asked_questions = {}  # Format: {question_id: result}
        self.question_attempts = {}  # Format: {question_id: number_of_attempts}
        self.questions_by_category = {}  # Format: {category: [question_ids]}
        self.question_selector_agent = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv('GEMINI_API_KEY')),
            storage=SqlAgentStorage(table_name="selector_sessions", db_file="tmp/selector_storage.db"),
            add_history_to_messages=True,
            num_history_responses=3,
            description=(
                "You are an intelligent interview question selector. Your role is to analyze the candidate's "
                "performance and select the most appropriate next question based on their strengths and weaknesses."
            ),
            instructions=(
                "Analyze the candidate's performance history and select the next question that will best evaluate "
                "their knowledge while avoiding topics they've struggled with recently. Consider:\n"
                "1. Previous question performance\n"
                "2. Category performance\n"
                "3. Question difficulty progression\n"
                "4. Knowledge area coverage"
            ),
            debug_mode=True
        )
        
    def select_next_question(self, questions: List[Dict], question_categories: Dict) -> Dict:
        # Filter out previously asked questions
        available_questions = [q for q in questions if q['id'] not in self.asked_questions]
        
        if not available_questions:
            return None
            
        # Prepare performance history for the agent
        performance_history = {
            "asked_questions": self.asked_questions,
            "categories_performance": self._get_category_performance(questions, question_categories),
            "available_questions": [{"id": q["id"], "category": q["category"]} for q in available_questions]
        }
        
        # Ask the agent to select the next question
        response: RunResponse = self.question_selector_agent.run(
            f"Based on this performance history: {json.dumps(performance_history, indent=2)}, "
            "select the ID of the next question to ask. Only respond with the question ID, nothing else."
        )
        
        selected_id = response.content.strip()
        
        # Find the selected question
        selected_question = next((q for q in available_questions if q['id'] == selected_id), None)
        
        # If agent's selection is invalid, fall back to random selection
        if not selected_question:
            return random.choice(available_questions)
            
        return selected_question

    def _get_category_performance(self, questions: List[Dict], question_categories: Dict) -> Dict[str, Dict]:
        category_stats = {}
        for q_id, result in self.asked_questions.items():
            question = next((q for q in questions if q['id'] == q_id), None)
            if question:
                category = question['category']
                if category not in category_stats:
                    category_stats[category] = {"correct": 0, "wrong": 0}
                if result == "correct":
                    category_stats[category]["correct"] += 1
                else:
                    category_stats[category]["wrong"] += 1
        return category_stats

    def record_result(self, question_id: str, result: str):
        self.asked_questions[question_id] = result
        
    def record_attempt(self, question_id: str):
        if question_id not in self.question_attempts:
            self.question_attempts[question_id] = 1
        else:
            self.question_attempts[question_id] += 1

def initialize_agent(question: str, template: str, criteria: str) -> Agent:
    return Agent(
        model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv('GEMINI_API_KEY')),
        storage=SqlAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
        # memory=AgentMemory(db=vector_db, create_session_summary=True, create_user_memories=True),
        add_history_to_messages=True,
        num_history_responses=3,
        description=(
            "You are a professional interviewer tasked with evaluating candidates based on their resumes. "
            f"The question asked is: '{question}'. "
            f"The expected approach for the answer should follow this template: '{template}'. "
            f"The criteria for judging the answer includes: '{criteria}'. "
            "Consider factors such as relevance, clarity, completeness, and how well the candidate's experience aligns with the question. "
            "Be mindful of potential misunderstandings or misinterpretations of the question by the candidate. "
            "Your goal is to assess their ability to articulate their qualifications effectively while providing constructive feedback."
        ),
        instructions=(
            "If the candidate's response does not meet expectations or lacks key details, provide gentle guidance with very small hints that steer them toward the correct answer. "
            "Avoid giving away the answer directly; instead, ask probing questions or suggest areas they might elaborate on. "
            "In cases where a candidate appears to misunderstand the question, clarify it without leading them too much. "
            "If a candidate provides an answer that is partially correct but missing critical elements, acknowledge what they did well while encouraging them to expand on their response. "
            "Once you determine that a candidate's answer meets the necessary criteria—demonstrating sufficient understanding, relevance, and detail—respond with 'correct' without any unnecessary text. "
            "Do not include any unnecessary text or commentary in your response; keep it concise and focused solely on the evaluation outcome."
            "If a satisfactory answer is provided, respond with 'correct' without any unnecessary text. "
            "Dont be very strict on your evaluation. if the user touches even 60% of the expected answer, respond with 'correct' without any unnecessary text. "
            "If a satisfactory answer is not provided within 3 attempts, respond with 'wrong' without any unnecessary text."
        ),
        debug_mode=True
    )

def load_questions():
    try:
        with open('questions.json', 'r') as f:
            data = json.load(f)
            return data['questions']
    except FileNotFoundError:
        st.error("Questions file not found. Please make sure questions.json exists in the backend directory.")
        return []
    except json.JSONDecodeError:
        st.error("Invalid JSON format in questions file.")
        return []

def check_interview_time():
    """Check if interview time limit is reached."""
    if st.session_state.interview_start_time:
        elapsed_time = time.time() - st.session_state.interview_start_time
        minutes_remaining = 30 - (elapsed_time / 60)
        
        if minutes_remaining <= 5 and not st.session_state.interview_ended:
            st.session_state.interview_ended = True
            return True
    return False

def handle_interview_end():
    """Handle the end of interview transition."""
    end_message = "Thank you for completing the interview! Let's proceed to your performance report."
    st.session_state.messages.append({"role": "assistant", "content": end_message})
    
    # Generate and play end message audio
    audio_file = text_to_speech_gemini(end_message)
    if audio_file:
        message_id = f"msg_{hash(end_message)}"
        if 'audio_messages' not in st.session_state:
            st.session_state.audio_messages = {}
        st.session_state.audio_messages[message_id] = audio_file
    
    # Wait for 3 seconds before transitioning to report page
    time.sleep(3)
    st.session_state.page = 'report'
    st.rerun()

def select_and_initialize_next_question():
    """Select and initialize the next question."""
    # Start the timer when first question is selected
    if st.session_state.interview_start_time is None:
        st.session_state.interview_start_time = time.time()
        
    # Check if interview time limit is reached
    if check_interview_time():
        return None
        
    questions = load_questions()
    question_categories = {q['id']: q['category'] for q in questions}
    next_question = st.session_state.question_selector.select_next_question(
        questions, question_categories
    )
    
    if next_question:
        st.session_state.current_question = next_question
        st.session_state.agent = initialize_agent(
            next_question['question'],
            next_question['template'],
            next_question['criteria']
        )
        return next_question
    else:
        st.session_state.current_question = None
        return None

def generate_questions(role, company, resume_content):
    """Generate questions based on the resume, role, and company."""
    builder = QuestionGenerator(
        resume_content,
        role,
        company
    )
    
    # Generate interview questions in batches
    interview_questions = []
    for _ in range(2):  # Adjust the range for the number of batches you want
        questions = builder.generate_interview_questions()
        interview_questions.append(questions)

    # Generate theoretical questions in batches
    theoretical_questions = []
    for _ in range(2):  # Adjust the range for the number of batches you want
        theory_questions = builder.generate_theoretical_interview_questions()
        theoretical_questions.append(theory_questions)

    # Generate skill questions in batches
    skill_questions = []
    for _ in range(2):  # Adjust the range for the number of batches you want
        skill_qs = builder.generate_skill_questions()
        skill_questions.append(skill_qs)

    # Generate situational questions in batches
    situational_questions = []
    for _ in range(2):  # Adjust the range for the number of batches you want
        situation_qs = builder.Generate_Situations()
        situational_questions.append(situation_qs)

    # Save all questions to questions.json
    builder.save_questions_to_json(
        interview_questions[0],
        theoretical_questions[0],
        skill_questions[0],
        situational_questions[0]
    )

def display_resume_data(resume_result, skills_result, linked_in):
    """Display the resume data in markdown format."""
    # Clear previous output
    st.markdown(linked_in)  # Display LinkedIn profile data

    st.markdown("##  Skills")
    st.markdown(skills_result)  # Display skills in a clean format

    st.markdown(resume_result)  # Display the concatenated string as markdown

def format_time_remaining(elapsed_time):
    """Format the remaining time in MM:SS format."""
    total_seconds = max(1800 - int(elapsed_time), 0)  # 30 minutes = 1800 seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def main():
    # Initialize session state variables if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    # Check login status and session validity
    if not st.session_state.logged_in or not check_session_validity():
        display_login_page()
        return

    # Rest of your existing main function code
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'questions_generated' not in st.session_state:
        st.session_state.questions_generated = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'question_selector' not in st.session_state:
        st.session_state.question_selector = QuestionSelector()
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'transition_message' not in st.session_state:
        st.session_state.transition_message = None
    if 'preparing_interview' not in st.session_state:
        st.session_state.preparing_interview = False
    if 'interview_ready' not in st.session_state:
        st.session_state.interview_ready = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'role': None,
            'company': None,
            'resume_file': None
        }
    if 'question_history' not in st.session_state:
        st.session_state.question_history = []
    if 'all_messages' not in st.session_state:
        st.session_state.all_messages = {}
    if 'interview_start_time' not in st.session_state:
        st.session_state.interview_start_time = None
    if 'interview_ended' not in st.session_state:
        st.session_state.interview_ended = False
    if 'timer_visible' not in st.session_state:
        st.session_state.timer_visible = False

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # st.title("🤖 AI Interview System")
        st.markdown("---")

        # Home page with two buttons
        if st.session_state.page == 'home':
            st.markdown("<h1 class='custom-header'>Welcome to AI Interview System</h1>", unsafe_allow_html=True)
            st.markdown("<p class='subtitle'>Your personal AI-powered interview preparation platform</p>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                st.markdown("""
                    <div class="feature-box">
                        <div>
                            <div class="feature-icon">📝</div>
                            <div class="feature-title">Build Resume</div>
                            <div class="feature-description">
                                Create a professional resume by analyzing your LinkedIn profile and GitHub repositories. 
                            </div>
                        </div>
                        <div class="button-container">
                            <button onclick="document.getElementById('build_resume_btn').click()">Get Started</button>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Build Resume", key="build_resume_btn", type="primary"):
                    st.session_state.page = 'resume'
                    st.rerun()

            with col2:
                st.markdown("""
                    <div class="feature-box">
                        <div>
                            <div class="feature-icon">🎯</div>
                            <div class="feature-title">Start Interview</div>
                            <div class="feature-description">
                                Experience an AI-powered interview simulation.
                            </div>
                        </div>
                    
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Start Interview", key="start_interview_btn", type="primary"):
                    st.session_state.page = 'interview'
                    st.rerun()

            st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

        # Resume builder page
        elif st.session_state.page == 'resume':
            st.header("Resume Builder")
            
            # Separate input fields for LinkedIn profile data
            linkedin_name = st.text_input("Enter your full name:")
            linkedin_occupation = st.text_input("Enter your occupation:")
            
            # Initialize session state for experiences and education if not already done
            if 'experiences' not in st.session_state:
                st.session_state.experiences = []
            if 'educations' not in st.session_state:
                st.session_state.educations = []

            # Input fields for experiences
            st.markdown("### Experiences")
            for i, experience in enumerate(st.session_state.experiences):
                st.markdown(f"**Experience {i + 1}**")
                company = st.text_input(f"Company Name {i + 1}:", value=experience.get('company', ''), key=f"company_{i}")
                title = st.text_input(f"Title {i + 1}:", value=experience.get('title', ''), key=f"title_{i}")
                description = st.text_area(f"Description {i + 1}:", value=experience.get('description', ''), key=f"description_{i}")
                st.session_state.experiences[i] = {
                    "company": company,
                    "title": title,
                    "description": description
                }
            
            # Button to add more experiences
            if st.button("Add Experience"):
                st.session_state.experiences.append({"company": "", "title": "", "description": ""})
                st.rerun()  # Rerun to display new fields

            # Input fields for education
            st.markdown("### Education")
            for i, education in enumerate(st.session_state.educations):
                st.markdown(f"**Education {i + 1}**")
                degree = st.text_input(f"Degree {i + 1}:", value=education.get('degree', ''), key=f"degree_{i}")
                institution = st.text_input(f"Institution {i + 1}:", value=education.get('institution', ''), key=f"institution_{i}")
                start_date = st.text_input(f"Start Date {i + 1}:", value=education.get('start_date', ''), key=f"start_date_{i}")
                end_date = st.text_input(f"End Date {i + 1}:", value=education.get('end_date', ''), key=f"end_date_{i}")
                st.session_state.educations[i] = {
                    "degree": degree,
                    "institution": institution,
                    "start_date": start_date,
                    "end_date": end_date
                }
            
            # Button to add more education
            if st.button("Add Education"):
                st.session_state.educations.append({"degree": "", "institution": "", "start_date": "", "end_date": ""})
                st.rerun()  # Rerun to display new fields
            
            role = st.text_input("Enter the role you're targeting:")
            
            # Multiple GitHub repos input
            st.markdown("### GitHub Repositories")
            st.markdown("Enter the repositories in format: username/repository")
            
            if 'num_repos' not in st.session_state:
                st.session_state.num_repos = 1
            
            repos = []
            for i in range(st.session_state.num_repos):
                repo = st.text_input(f"Repository {i+1}", key=f"repo_{i}")
                if repo:
                    repos.append(repo)
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("Add Repo"):
                    st.session_state.num_repos += 1
                    st.rerun()
            
            if st.button("Generate Resume"):
                if linkedin_name and linkedin_occupation and st.session_state.experiences and st.session_state.educations and role and repos:
                    linkedin_profile_data = {
                        "full_name": linkedin_name,
                        "occupation": linkedin_occupation,
                        "experiences": st.session_state.experiences,
                        "education": st.session_state.educations
                    }
                    with st.spinner("Building your resume..."):
                        resume_builder = ResumeBuilder(repos, linkedin_profile_data, role)
                        resume_result, skills_result, linked_in = resume_builder.build()
                        display_resume_data(resume_result, skills_result, linked_in)
                        st.success("Resume generated successfully!")
                else:
                    st.error("Please fill in all fields")
            
            if st.button("Back to Home"):
                st.session_state.page = 'home'
                st.rerun()

        # Interview page
        elif st.session_state.page == 'interview':
            if not st.session_state.interview_ready:
                # Create a container for the form
                form_container = st.container()
                
                with form_container:
                    st.markdown("<h2 class='section-header'>Generate Interview Questions</h2>", unsafe_allow_html=True)
                    
                    # Create a centered form container
                    st.markdown('<div class="form-container">', unsafe_allow_html=True)
                    
                    # Form fields with increased size and better styling
                    role = st.text_input("Enter the role you are applying for:", key="role_input")
                    company = st.text_input("Enter the company you are applying to:", key="company_input")
                    
                    # Simple file uploader without container
                    resume_file = st.file_uploader("Upload your resume (PDF format):", type=["pdf"], key="resume_uploader")
                    
                    # Button container with centered buttons
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col2:
                        if st.button("Prepare Interview", key="prepare_interview_btn", type="primary"):
                            if role and company and resume_file:
                                st.session_state.form_data = {
                                    'role': role,
                                    'company': company,
                                    'resume_file': resume_file
                                }
                                st.session_state.preparing_interview = True
                                st.session_state.interview_ready = True
                                st.rerun()
                            else:
                                st.error("Please enter role, company, and upload your resume.")
                        
                        if st.button("Prepare Cheatsheet", key="prepare_cheatsheet_btn", type="primary"):
                            if role and company and resume_file:
                                # Show progress bar
                                progress_bar = st.progress(0)
                                st.write("Generating your interview cheatsheet...")
                                
                                # Extract resume content
                                resume_content = extract_text_from_pdf(resume_file)
                                
                                # Initialize cheatsheet generator
                                cheatsheet_gen = CheatsheetGenerator(resume_content, role, company)
                                
                                # Update progress
                                progress_bar.progress(30)
                                st.write("Analyzing resume and generating Q&A pairs...")
                                
                                # Generate cheatsheet data
                                cheatsheet_data = cheatsheet_gen.generate_cheatsheet()
                                
                                # Update progress
                                progress_bar.progress(70)
                                st.write("Creating PDF document...")
                                
                                # Generate PDF
                                pdf_buffer = cheatsheet_gen.generate_pdf(cheatsheet_data)
                                
                                # Update progress
                                progress_bar.progress(100)
                                st.write("Cheatsheet ready!")
                                
                                # Provide download button
                                st.download_button(
                                    label="Download Interview Cheatsheet",
                                    data=pdf_buffer,
                                    file_name="interview_cheatsheet.pdf",
                                    mime="application/pdf"
                                )
                            else:
                                st.error("Please enter role, company, and upload your resume.")
                        
                        if st.button("Back to Home", key="back_home_btn", type="primary"):
                            st.session_state.page = 'home'
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            elif st.session_state.preparing_interview:
                # Clear everything and show only the progress section
                st.empty()
                st.markdown("""
                    <style>
                        /* Hide all other elements */
                        .block-container > div:not(:last-child) {
                            display: none !important;
                        }
                        /* Center the progress content */
                        .progress-content {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            min-height: 60vh;
                            padding: 2rem;
                        }
                    </style>
                """, unsafe_allow_html=True)
                
                # Progress content in a centered container
                st.markdown("""
                    <div class="progress-content">
                        <div style='text-align: center; max-width: 600px;'>
                            <h2 style='color: #4f46e5; margin-bottom: 20px; font-size: 28px;'>🎯 Analyzing Your Resume</h2>
                            <p style='font-size: 18px; color: #4b5563; line-height: 1.6; margin-bottom: 30px;'>
                                Please wait while we analyze your resume and prepare personalized interview questions...
                            </p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show a progress animation
                progress_placeholder = st.empty()
                progress_bar = progress_placeholder.progress(0)
                for i in range(100):
                    progress_bar.progress(i + 1)
                    time.sleep(0.02)
                
                # Generate questions after progress bar using stored form data
                resume_content = extract_text_from_pdf(st.session_state.form_data['resume_file'])
                generate_questions(
                    st.session_state.form_data['role'],
                    st.session_state.form_data['company'],
                    resume_content
                )
                st.session_state.questions_generated = True
                st.session_state.interview_started = True  # Changed to True to skip confirmation
                st.session_state.preparing_interview = False
                select_and_initialize_next_question()
                st.rerun()

            elif st.session_state.interview_started:
                # Set interview start time if not set
                if st.session_state.interview_start_time is None:
                    st.session_state.interview_start_time = time.time()
                
                # Interview in progress
                if st.session_state.current_question:
                    # Check if interview should end after current question
                    if st.session_state.interview_ended and not st.session_state.messages:
                        handle_interview_end()
                    
                    # Container for all content except chat input
                    content_container = st.container()
                    
                    if 'ready_to_start' not in st.session_state:
                        # Show welcome screen with ready button
                        st.markdown("""
                            <style>
                                .welcome-container {
                                    display: flex;
                                    flex-direction: column;
                                    align-items: center;
                                    justify-content: center;
                                    min-height: 70vh;
                                    text-align: center;
                                    padding: 2rem;
                                }
                                .welcome-box {
                                    background: white;
                                    padding: 40px;
                                    border-radius: 16px;
                                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                                    max-width: 800px;
                                    margin: 0 auto;
                                }
                                .welcome-title {
                                    color: #4f46e5;
                                    font-size: 32px;
                                    font-weight: 700;
                                    margin-bottom: 24px;
                                }
                            </style>
                            <div class="welcome-container">
                                <div class="welcome-box">
                                    <h1 class="welcome-title">👋 Welcome to your AI Interview!</h1>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Generate welcome audio with compact player
                        if 'welcome_played' not in st.session_state:
                            welcome_text = """Welcome to your AI Interview!"""
                            audio_file = text_to_speech_gemini(welcome_text)
                            if audio_file:
                                col1, col2, col3 = st.columns([4, 4, 4])
                                with col2:
                                    st.audio(audio_file, format='audio/mp3')
                                cleanup_audio_file(audio_file)
                            st.session_state.welcome_played = True
                        
                        # Center the ready button
                        col1, col2, col3 = st.columns([4, 4, 4])
                        with col2:
                            if st.button("I am Ready", type="primary"):
                                st.session_state.ready_to_start = True
                                st.rerun()
                    
                    else:
                        st.markdown("""
                            <style>
                                .chat-container {
                                    max-width: 900px;
                                    margin: 0 auto;
                                    padding: 0 20px 80px 20px;
                                    display: flex;
                                    flex-direction: column;
                                    position: relative;
                                    min-height: 80vh;
                                    background-color: #ffffff;
                                }
                                .timer-container {
                                    position: fixed;
                                    top: 20px;
                                    right: 20px;
                                    background-color: #ffffff;
                                    padding: 10px 15px;
                                    border-radius: 8px;
                                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                                    z-index: 1000;
                                    display: flex;
                                    align-items: center;
                                    gap: 5px;
                                }
                                .timer-warning {
                                    color: #ef4444;
                                }
                                .timer-normal {
                                    color: #1f2937;
                                }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        # Add timer display
                        elapsed_time = time.time() - st.session_state.interview_start_time
                        time_remaining = format_time_remaining(elapsed_time)
                        minutes_remaining = (1800 - int(elapsed_time)) / 60
                        
                        timer_class = "timer-warning" if minutes_remaining <= 5 else "timer-normal"
                        st.markdown(
                            f"""
                            <div class="timer-container">
                                <span>⏱️</span>
                                <span class="{timer_class}">{time_remaining}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                        
                        # Question container (sticky at top)
                        st.markdown('<div class="question-container">', unsafe_allow_html=True)
                        
                        # Question box
                        st.markdown('<div class="question-box">', unsafe_allow_html=True)
                        current_question = st.session_state.current_question['question']
                        st.markdown(f'<div class="question-text">{current_question}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Audio player for the question
                        if 'last_question' not in st.session_state or st.session_state.last_question != current_question:
                            audio_file = text_to_speech_gemini(current_question)
                            if audio_file:
                                st.markdown('<div class="audio-player-container">', unsafe_allow_html=True)
                                st.audio(audio_file, format='audio/mp3')
                                st.markdown('</div>', unsafe_allow_html=True)
                                cleanup_audio_file(audio_file)
                            st.session_state.last_question = current_question
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Chat messages section
                        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
                        
                        # Display chat history
                        for message in st.session_state.messages:
                            if message["role"] == "user":
                                # User message (right-aligned)
                                st.markdown(
                                    f'<div class="user-message-container"><div class="message user-message">{message["content"]}</div></div>',
                                    unsafe_allow_html=True
                                )
                            else:
                                # Assistant message (left-aligned) with audio below
                                message_id = f"msg_{hash(message['content'])}"
                                st.markdown(
                                    f'<div class="assistant-message-container"><div class="message assistant-message">{message["content"]}</div></div>',
                                    unsafe_allow_html=True
                                )
                                
                                # If we have audio for this message, add it below
                                if 'audio_messages' not in st.session_state:
                                    st.session_state.audio_messages = {}
                                
                                if message_id not in st.session_state.audio_messages:
                                    audio_file = text_to_speech_gemini(message["content"])
                                    if audio_file:
                                        st.session_state.audio_messages[message_id] = audio_file
                                
                                if message_id in st.session_state.audio_messages:
                                    st.markdown('<div class="assistant-audio-container">', unsafe_allow_html=True)
                                    st.audio(st.session_state.audio_messages[message_id], format='audio/mp3')
                                    st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Input container (sticky at bottom)
                        st.markdown('<div class="input-container">', unsafe_allow_html=True)
                        
                        # Tabs for text and voice input
                        st.markdown('<div class="input-tabs">', unsafe_allow_html=True)
                        tab1, tab2 = st.tabs(["💬 Text Input", "🎤 Voice Input"])
                        
                        with tab1:
                            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
                            if prompt := st.chat_input("Type your answer here..."):
                                st.session_state.messages.append({"role": "user", "content": prompt})
                                process_response(prompt, content_container)
                                st.rerun()  # Rerun to display the new message
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with tab2:
                            st.markdown('<div class="voice-input-section">', unsafe_allow_html=True)
                            
                            # Create a custom record button that only starts recording when clicked
                            st.markdown("""
                                <style>
                                    .record-button {
                                        background-color: #4f46e5;
                                        color: white;
                                        border: none;
                                        border-radius: 8px;
                                        padding: 10px 20px;
                                        font-size: 16px;
                                        font-weight: 600;
                                        margin: 10px 0;
                                        cursor: pointer;
                                        transition: all 0.3s ease;
                                        display: inline-flex;
                                        align-items: center;
                                        justify-content: center;
                                    }
                                    .record-button:hover {
                                        background-color: #4338ca;
                                        transform: translateY(-2px);
                                    }
                                    .record-button-icon {
                                        margin-right: 8px;
                                        font-size: 18px;
                                    }
                                </style>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("<p>Click the button below to record your answer:</p>", unsafe_allow_html=True)
                            
                            # Only show the actual recording input when the user clicks to record
                            if 'show_recorder' not in st.session_state:
                                st.session_state.show_recorder = False
                                
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                if not st.session_state.show_recorder:
                                    if st.button("🎤 Record Answer", key="start_recording"):
                                        st.session_state.show_recorder = True
                                        st.rerun()
                                else:
                                    # Show recording interface
                                    audio_bytes = st.audio_input("Record your answer")
                                    
                                    # Add a cancel button
                                    if st.button("Cancel Recording", key="cancel_recording"):
                                        st.session_state.show_recorder = False
                                        st.rerun()
                                    
                                    if audio_bytes:
                                        with st.spinner("Transcribing your answer..."):
                                            transcribed_text = speech_to_text_groq(audio_bytes)
                                            if transcribed_text:
                                                st.session_state.messages.append({"role": "user", "content": transcribed_text})
                                                st.session_state.show_recorder = False  # Reset recorder state
                                                process_response(transcribed_text, content_container)
                                                st.rerun()  # Rerun to display the new message
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Exit button
                        st.markdown('<div class="exit-button-container">', unsafe_allow_html=True)
                        if st.button("Exit Interview", type="primary", key="exit_btn", help="Click to exit the interview"):
                            st.session_state.page = 'report'
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        # Report page
        elif st.session_state.page == 'report':
            if 'report_data' not in st.session_state:
                # Show progress indicator while generating the report
                st.markdown("""
                    <style>
                        .report-loading {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            min-height: 60vh;
                            text-align: center;
                        }
                    </style>
                    <div class="report-loading">
                        <h2 style="color: #4f46e5; margin-bottom: 20px;">Generating Your Performance Report</h2>
                        <p style="margin-bottom: 30px; font-size: 16px;">Please wait while we analyze your interview performance...</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show a progress animation
                progress_placeholder = st.empty()
                progress_bar = progress_placeholder.progress(0)
                for i in range(100):
                    progress_bar.progress(i + 1)
                    time.sleep(0.02)
                
                # Generate the report
                st.session_state.report_data = generate_report()
                st.rerun()
            else:
                # Display the report
                display_report()

def display_login_page():
    """Display the custom login page with Google OAuth."""
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 40px;
            text-align: center;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("Welcome to AI Interview System")
    st.markdown("Please sign in with your NITK email to continue")

    # Create OAuth flow with increased time tolerance
    if 'oauth_state' not in st.session_state:
        client_secrets_file = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email'],
            redirect_uri=st.secrets["REDIRECT_URI"]
        )
        
        # Generate authorization URL with increased tolerance
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='select_account'
        )
        st.session_state.oauth_state = state

        st.markdown(f"""
            <a href="{auth_url}" class="login-button">
                <img src="https://www.google.com/favicon.ico" width="20" height="20"/>
                Sign in with Google
            </a>
        """, unsafe_allow_html=True)

    # Handle OAuth callback using new st.query_params
    query_params = st.query_params
    if 'code' in query_params:
        try:
            flow = Flow.from_client_secrets_file(
                client_secrets_file,
                scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email'],
                state=st.session_state.oauth_state,
                redirect_uri=st.secrets["REDIRECT_URI"]
            )
            
            flow.fetch_token(code=query_params['code'])
            credentials = flow.credentials

            # Verify token with increased time tolerance
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                st.secrets["GOOGLE_CLIENT_ID"],
                clock_skew_in_seconds=900  # 15 minutes tolerance
            )

            # Verify NITK email domain
            if not id_info['email'].endswith('@nitk.edu.in'):
                st.error("Please use your NITK email address")
                return

            # Initialize session
            st.session_state.user_info = id_info
            st.session_state.logged_in = True
            st.session_state.login_time = time.time()

            # Clear OAuth state and redirect
            del st.session_state.oauth_state
            st.rerun()

        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            if "Token used too early" in str(e):
                st.info("System clock synchronization issue detected. Please wait a moment...")
                time.sleep(2)  # Add small delay
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
def handle_logout():
    clear_session()
    st.rerun()

def process_response(user_input: str, content_container):
    """Process user response and generate AI response with voice."""
    # Record an attempt for the current question
    question_id = st.session_state.current_question['id']
    st.session_state.question_selector.record_attempt(question_id)
    
    with st.spinner("Evaluating your answer..."):
        response: RunResponse = st.session_state.agent.run(user_input)
        response_text = response.content.strip()
        
        # Handle non-terminal responses (not correct/wrong)
        if response_text.lower() not in ["correct", "wrong"]:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Generate audio for the response
            message_id = f"msg_{hash(response_text)}"
            if 'audio_messages' not in st.session_state:
                st.session_state.audio_messages = {}
            
            audio_file = text_to_speech_gemini(response_text)
            if audio_file:
                st.session_state.audio_messages[message_id] = audio_file
        
        # Handle terminal responses (correct/wrong)
        if response_text.lower() == "correct":
            handle_correct_answer(content_container)
        elif response_text.lower() == "wrong":
            handle_wrong_answer(content_container)

def handle_correct_answer(content_container):
    """Handle correct answer response."""
    # Record the result for the current question
    st.session_state.question_selector.record_result(
        st.session_state.current_question['id'], "correct"
    )
    
    # Show balloons for celebration
   
    
    # Store question details in history
    question_data = {
        'id': st.session_state.current_question['id'],
        'question': st.session_state.current_question['question'],
        'category': st.session_state.current_question['category'],
        'result': 'correct',
        'attempts': st.session_state.question_selector.question_attempts.get(st.session_state.current_question['id'], 1)
    }
    st.session_state.question_history.append(question_data)
    
    # Store conversation for this question
    st.session_state.all_messages[st.session_state.current_question['id']] = st.session_state.messages.copy()
    
    transition_messages = [
        "Great answer! Let's move on to another interesting topic...",
        "Excellent! Now, I'd like to explore a different area with you...",
        "Well explained! Let's shift our discussion to another aspect...",
        "Very good! Moving on to our next topic of discussion...",
        "That's exactly what we were looking for! Let's continue our conversation with..."
    ]
    transition_msg = random.choice(transition_messages)
    
    # Clear previous messages before adding transition
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": transition_msg})
    
    # Generate and play transition audio
    audio_file = text_to_speech_gemini(transition_msg)
    if audio_file:
        with content_container.chat_message("assistant"):
            st.markdown(transition_msg)
            st.audio(audio_file, format='audio/mp3')
        cleanup_audio_file(audio_file)
    
    # Select next question and clear agent state
    next_question = select_and_initialize_next_question()
    if next_question:
        # Clear all relevant state
        st.session_state.messages = []  # Clear messages again for fresh start
        st.session_state.last_question = None  # Reset last question tracking
        if 'last_response' in st.session_state:
            del st.session_state.last_response  # Clear last response
        
        # Clear any other stored responses or states
        if 'agent' in st.session_state:
            st.session_state.agent = initialize_agent(
                next_question['question'],
                next_question['template'],
                next_question['criteria']
            )
    
    # Force a rerun with a small delay to ensure state updates are processed
    time.sleep(0.5)
    st.rerun()

def handle_wrong_answer(content_container):
    """Handle wrong answer response."""
    # Record the result for the current question
    st.session_state.question_selector.record_result(
        st.session_state.current_question['id'], "wrong"
    )
    
    # Store question details in history
    question_data = {
        'id': st.session_state.current_question['id'],
        'question': st.session_state.current_question['question'],
        'category': st.session_state.current_question['category'],
        'result': 'wrong',
        'attempts': st.session_state.question_selector.question_attempts.get(st.session_state.current_question['id'], 1)
    }
    st.session_state.question_history.append(question_data)
    
    # Store conversation for this question
    st.session_state.all_messages[st.session_state.current_question['id']] = st.session_state.messages.copy()
    
    transition_messages = [
        "Thank you for your effort. Let's move on to a different topic...",
        "That's a challenging one. Let's explore another area...",
        "Let's shift our focus to another interesting topic...",
        "Moving on to our next discussion point..."
    ]
    transition_msg = random.choice(transition_messages)
    
    # Clear previous messages before adding transition
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": transition_msg})
    
    # Generate and play transition audio
    audio_file = text_to_speech_gemini(transition_msg)
    if audio_file:
        with content_container.chat_message("assistant"):
            st.markdown(transition_msg)
            st.audio(audio_file, format='audio/mp3')
        cleanup_audio_file(audio_file)
    
    # Select next question and clear agent state
    next_question = select_and_initialize_next_question()
    if next_question:
        # Clear all relevant state
        st.session_state.messages = []  # Clear messages again for fresh start
        st.session_state.last_question = None  # Reset last question tracking
        if 'last_response' in st.session_state:
            del st.session_state.last_response  # Clear last response
        
        # Clear any other stored responses or states
        if 'agent' in st.session_state:
            st.session_state.agent = initialize_agent(
                next_question['question'],
                next_question['template'],
                next_question['criteria']
            )
    
    # Force a rerun with a small delay to ensure state updates are processed
    time.sleep(0.5)
    st.rerun()

def generate_report():
    """Generate a comprehensive report of the interview performance."""
    # Get the question history
    question_history = st.session_state.question_history
    
    if not question_history:
        return {
            "quantitative_analysis": {
                "correct_first_attempt": 0,
                "correct_multiple_attempts": 0,
                "wrong": 0,
                "total": 0
            },
            "detailed_analysis": "No questions were answered during this interview session.",
            "areas_to_improve": ["N/A"]
        }
    
    # 1. Quantitative Analysis
    correct_first_attempt = sum(1 for q in question_history if q['result'] == 'correct' and q['attempts'] == 1)
    correct_multiple_attempts = sum(1 for q in question_history if q['result'] == 'correct' and q['attempts'] > 1)
    wrong_answers = sum(1 for q in question_history if q['result'] == 'wrong')
    total_questions = len(question_history)
    
    quantitative_analysis = {
        "correct_first_attempt": correct_first_attempt,
        "correct_multiple_attempts": correct_multiple_attempts,
        "wrong": wrong_answers,
        "total": total_questions
    }
    
    # Prepare topic analysis data for the detailed summary
    by_category = {}
    for q in question_history:
        category = q['category']
        if category not in by_category:
            by_category[category] = {
                "total": 0,
                "correct_first_attempt": 0,
                "correct_multiple_attempts": 0,
                "wrong": 0,
                "questions": []
            }
        
        by_category[category]["total"] += 1
        by_category[category]["questions"].append({
            "question": q["question"],
            "result": q["result"],
            "attempts": q["attempts"]
        })
        
        if q['result'] == 'correct':
            if q['attempts'] == 1:
                by_category[category]["correct_first_attempt"] += 1
            else:
                by_category[category]["correct_multiple_attempts"] += 1
        else:
            by_category[category]["wrong"] += 1
    
    # Calculate strength and weakness scores by category
    for category, stats in by_category.items():
        total = stats["total"]
        if total > 0:
            # Weighted score: first attempt correct is best, multiple attempts is okay, wrong is worst
            score = (stats["correct_first_attempt"] * 1.0 + stats["correct_multiple_attempts"] * 0.5) / total
            stats["performance_score"] = score
    
    # Sort categories by performance score
    sorted_categories = sorted(by_category.items(), key=lambda x: x[1]["performance_score"], reverse=True)
    strong_categories = [cat for cat, stats in sorted_categories[:2] if stats["performance_score"] > 0.5]
    weak_categories = [cat for cat, stats in sorted_categories[-2:] if stats["performance_score"] < 0.7]
    
    # Prepare conversation data
    all_conversations = {}
    for q_id, messages in st.session_state.all_messages.items():
        question = next((q["question"] for q in question_history if q["id"] == q_id), "Unknown question")
        category = next((q["category"] for q in question_history if q["id"] == q_id), "Unknown category")
        all_conversations[q_id] = {
            "question": question,
            "category": category,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages]
        }
    
    # 3 & 4. Generate Detailed Analysis and Areas to Improve
    # Create a prompt for the AI to generate these sections
    prompt = f"""
    I need to generate a comprehensive performance report for an interview candidate. Here are the details:
    
    Quantitative Analysis:
    - Total Questions: {total_questions}
    - Correct on First Attempt: {correct_first_attempt} ({int(correct_first_attempt/total_questions*100) if total_questions > 0 else 0}%)
    - Correct after Multiple Attempts: {correct_multiple_attempts} ({int(correct_multiple_attempts/total_questions*100) if total_questions > 0 else 0}%)
    - Could Not Answer Correctly: {wrong_answers} ({int(wrong_answers/total_questions*100) if total_questions > 0 else 0}%)
    
    Performance by Topics:
    {json.dumps({category: {"performance_score": stats["performance_score"], "total_questions": stats["total"], 
                           "correct_first": stats["correct_first_attempt"], 
                           "correct_with_hints": stats["correct_multiple_attempts"], 
                           "wrong": stats["wrong"]} 
                 for category, stats in by_category.items()}, indent=2)}
    
    Questions and Results:
    {json.dumps({q["id"]: {"question": q["question"], "category": q["category"], "result": q["result"], "attempts": q["attempts"]} 
                for q in question_history}, indent=2)}
    
    Strong Categories: {', '.join(strong_categories) if strong_categories else 'None identified'}
    Weak Categories: {', '.join(weak_categories) if weak_categories else 'None identified'}
    
    Based on this information, please provide:
    
    1. A detailed analysis (around 4-6 paragraphs) pointwise that:
       - Analyzes the candidate's overall performance
       - Identifies strong points in specific topics with examples where possible
       - Points out weak areas and potential knowledge gaps
       - Evaluates the quality of answers based on number of attempts needed
       - Provides context on how the candidate performed across different categories
    
    2. A concise list of 3-5 specific areas to improve with actionable recommendations
    
    Format your response exactly as follows:
    {{
      "detailed_analysis": "Your detailed analysis here...",
      "areas_to_improve": ["Area 1", "Area 2", "Area 3"]
    }}
    
    Make sure your response is properly formatted as valid JSON. Only include the above fields. Do not include any explanations, introductions, or extra text outside the JSON structure.
    """
    
    # Use the Gemini model to generate the summary and areas to improve
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv('GEMINI_API_KEY')),
        add_history_to_messages=False,
        num_history_responses=0
    )
    
    try:
        response = agent.run(prompt)
        response_text = response.content.strip()
        
        # Try to extract valid JSON from the response if it contains extra text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = json.loads(response_text)
            
        detailed_analysis = result.get("detailed_analysis", "")
        areas_to_improve = result.get("areas_to_improve", [])
        
        # Validate the response
        if not detailed_analysis or not areas_to_improve:
            raise ValueError("Missing required fields in the response")
            
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Raw response: {response.content if hasattr(response, 'content') else 'No response'}")
        
        # Fallback with more useful information
        strong_categories_text = ", ".join(strong_categories) if strong_categories else "none identified"
        weak_categories_text = ", ".join(weak_categories) if weak_categories else "none identified"
        
        # Generate a reasonable fallback based on the data we have
        correct_percent = int((correct_first_attempt + correct_multiple_attempts) / total_questions * 100) if total_questions > 0 else 0
        
        if correct_percent >= 80:
            performance_level = "excellent"
        elif correct_percent >= 60:
            performance_level = "good"
        elif correct_percent >= 40:
            performance_level = "moderate"
        else:
            performance_level = "needs improvement"
            
        detailed_analysis = f"""
        The candidate demonstrated {performance_level} performance overall, correctly answering {correct_first_attempt + correct_multiple_attempts} out of {total_questions} questions ({correct_percent}%).
        
        Strong performance was observed in the following topics: {strong_categories_text}. The candidate was able to answer questions in these areas with fewer attempts, demonstrating solid knowledge.
        
        Areas requiring improvement include: {weak_categories_text}. In these topics, the candidate either needed multiple attempts to arrive at correct answers or was unable to answer correctly.
        
        Of note, {correct_first_attempt} questions ({int(correct_first_attempt/total_questions*100) if total_questions > 0 else 0}%) were answered correctly on the first attempt, showing areas of strong immediate recall and understanding. {correct_multiple_attempts} questions required additional hints or multiple attempts, indicating areas where knowledge exists but may need reinforcement. {wrong_answers} questions ({int(wrong_answers/total_questions*100) if total_questions > 0 else 0}%) could not be answered correctly, suggesting knowledge gaps that should be addressed.
        """
        
        # Generate fallback areas to improve
        areas_to_improve = []
        
        if weak_categories:
            areas_to_improve.append(f"Focus on strengthening knowledge in {', '.join(weak_categories)}")
            
        if wrong_answers > 0:
            areas_to_improve.append("Review core concepts in areas where questions couldn't be answered correctly")
            
        if correct_multiple_attempts > 0:
            areas_to_improve.append("Practice explaining concepts more clearly to reduce the need for hints")
            
        # Add a general recommendation
        areas_to_improve.append("Engage in more practice interviews to improve response quality and confidence")
    
    return {
        "quantitative_analysis": quantitative_analysis,
        "detailed_analysis": detailed_analysis,
        "areas_to_improve": areas_to_improve
    }

def generate_pdf_report():
    """Generate a PDF version of the interview report using FPDF."""
    if 'report_data' not in st.session_state:
        return None
    
    try:
        report = st.session_state.report_data
        quant = report["quantitative_analysis"]
        total = quant["total"]
        
        # Calculate percentages
        correct_first_percent = int((quant["correct_first_attempt"] / total * 100) if total > 0 else 0)
        correct_multiple_percent = int((quant["correct_multiple_attempts"] / total * 100) if total > 0 else 0)
        wrong_percent = int((quant["wrong"] / total * 100) if total > 0 else 0)
        
        # Create a PDF object
        pdf = FPDF()
        # Use UTF-8 encoding
        pdf.add_page()
        
        # Set up the PDF
        pdf.set_author("AI Interview System")
        pdf.set_title("Interview Performance Report")
        
        # Add logo and header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Interview Performance Report", 0, 1, "C")
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 0, 1, "C")
        pdf.ln(10)
        
        # Section: Quantitative Analysis
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "Quantitative Analysis", 1, 1, "L", 1)
        pdf.ln(5)
        
        # Create a table for the stats
        pdf.set_font("Arial", "", 10)
        
        # Headers
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(50, 10, "Metric", 1, 0, "L", 1)
        pdf.cell(30, 10, "Count", 1, 0, "C", 1)
        pdf.cell(30, 10, "Percentage", 1, 0, "C", 1)
        pdf.cell(80, 10, "Performance", 1, 1, "C", 1)
        
        # Total questions
        pdf.cell(50, 10, "Total Questions", 1, 0, "L")
        pdf.cell(30, 10, str(total), 1, 0, "C")
        pdf.cell(30, 10, "100%", 1, 0, "C")
        pdf.cell(80, 10, "", 0, 1, "C")
        
        # Correct on first attempt
        pdf.cell(50, 10, "Correct on First Try", 1, 0, "L")
        pdf.cell(30, 10, str(quant['correct_first_attempt']), 1, 0, "C")
        pdf.cell(30, 10, f"{correct_first_percent}%", 1, 0, "C")
        
        # Simple progress bar visualization
        progress_cell_width = 80
        bar_width = int(progress_cell_width * correct_first_percent / 100)
        pdf.set_fill_color(16, 185, 129)  # Green color
        pdf.cell(bar_width, 10, "", 0, 0, "L", 1)
        pdf.cell(progress_cell_width - bar_width, 10, "", 0, 1, "L", 0)
        
        # Correct after hints
        pdf.cell(50, 10, "Correct After Hints", 1, 0, "L")
        pdf.cell(30, 10, str(quant['correct_multiple_attempts']), 1, 0, "C")
        pdf.cell(30, 10, f"{correct_multiple_percent}%", 1, 0, "C")
        
        # Progress bar for correct after hints
        bar_width = int(progress_cell_width * correct_multiple_percent / 100)
        pdf.set_fill_color(245, 158, 11)  # Orange color
        pdf.cell(bar_width, 10, "", 0, 0, "L", 1)
        pdf.cell(progress_cell_width - bar_width, 10, "", 0, 1, "L", 0)
        
        # Wrong answers
        pdf.cell(50, 10, "Could Not Answer", 1, 0, "L")
        pdf.cell(30, 10, str(quant['wrong']), 1, 0, "C")
        pdf.cell(30, 10, f"{wrong_percent}%", 1, 0, "C")
        
        # Progress bar for wrong answers
        bar_width = int(progress_cell_width * wrong_percent / 100)
        pdf.set_fill_color(239, 68, 68)  # Red color
        pdf.cell(bar_width, 10, "", 0, 0, "L", 1)
        pdf.cell(progress_cell_width - bar_width, 10, "", 0, 1, "L", 0)
        
        pdf.ln(10)
        
        # Section: Detailed Analysis
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "Detailed Performance Analysis", 1, 1, "L", 1)
        pdf.ln(5)
        
        # Format the analysis text with proper spacing and line breaks
        pdf.set_font("Arial", "", 10)
        
        # Make sure we handle special characters properly
        analysis_text = report["detailed_analysis"].strip()
        
        # Process text in smaller chunks to avoid encoding issues
        try:
            # Split long text into paragraphs and print each
            paragraphs = analysis_text.split('\n\n')
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if paragraph:
                    # Remove any non-standard characters that might cause issues
                    safe_paragraph = ''.join(c if ord(c) < 128 else ' ' for c in paragraph)
                    pdf.multi_cell(0, 5, safe_paragraph)
                    pdf.ln(3)
        except Exception as text_error:
            st.error(f"Error processing text: {text_error}")
            pdf.multi_cell(0, 5, "Error displaying detailed analysis text.")
        
        pdf.ln(5)
        
        # Section: Areas to Improve
        pdf.set_font("Arial", "B", 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, "Areas to Improve", 1, 1, "L", 1)
        pdf.ln(5)
        
        # List areas to improve
        pdf.set_font("Arial", "", 10)
        for i, area in enumerate(report["areas_to_improve"], 1):
            try:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(10, 10, f"{i}.", 0, 0)
                pdf.set_font("Arial", "", 10)
                # Remove any non-standard characters that might cause issues
                safe_area = ''.join(c if ord(c) < 128 else ' ' for c in area)
                pdf.multi_cell(0, 10, safe_area)
            except Exception as area_error:
                st.error(f"Error processing improvement area: {area_error}")
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "Generated by AI Interview System", 0, 0, "C")
        
        # Return the PDF as bytes 
        try:
            # Try with latin1 encoding first (FPDF default)
            return pdf.output(dest='S').encode('latin1')
        except UnicodeEncodeError:
            # If that fails, try a different approach with a BytesIO buffer
            buffer = io.BytesIO()
            pdf.output(buffer)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None

def get_pdf_download_link(pdf_data, filename="Interview_Report.pdf"):
    """Generate a download link for the PDF report."""
    if pdf_data is None:
        return None
    
    # Encode PDF binary data to base64
    b64 = base64.b64encode(pdf_data).decode()
    
    # Create a styled download link
    href = f'''
    <a href="data:application/pdf;base64,{b64}" download="{filename}" 
       style="display: inline-block; 
              background-color: #10b981; 
              color: white; 
              text-decoration: none; 
              padding: 12px 24px; 
              border-radius: 8px; 
              font-weight: 600; 
              transition: all 0.3s ease;
              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
              margin: 10px 0;">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" style="vertical-align: text-bottom; margin-right: 8px;" viewBox="0 0 16 16">
            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
            <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
        </svg>
        Download PDF Report
    </a>
    '''
    return href

def display_report():
    """Display the interview performance report."""
    st.markdown("""
        <style>
            .report-container {
                max-width: 900px;
                margin: 0 auto;
                padding: 40px;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }
            .report-header {
                margin-bottom: 30px;
                text-align: center;
            }
            .report-section {
                margin-bottom: 40px;
                padding: 20px;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            .report-section-title {
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #4f46e5;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 10px;
            }
            .stat-box {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .stat-label {
                font-size: 14px;
                color: #6b7280;
            }
            .stat-value {
                font-size: 24px;
                font-weight: 700;
                color: #1f2937;
            }
            .progress-bar-container {
                height: 10px;
                background-color: #e5e7eb;
                border-radius: 5px;
                margin-top: 5px;
                overflow: hidden;
            }
            .progress-bar {
                height: 100%;
                border-radius: 5px;
            }
            .good-progress {
                background-color: #10b981;
            }
            .medium-progress {
                background-color: #f59e0b;
            }
            .poor-progress {
                background-color: #ef4444;
            }
            .analysis-text {
                line-height: 1.8;
                font-size: 16px;
                color: #111827;
                padding: 10px;
                white-space: pre-line;
            }
            .analysis-text p {
                margin-bottom: 15px;
            }
            .improve-item {
                background-color: #ffffff;
                border-left: 4px solid #4f46e5;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 0 8px 8px 0;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            .home-button-container {
                text-align: center;
                margin-top: 40px;
            }
            .button-row {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 40px;
            }
            .download-btn {
                background-color: #10b981 !important;
                color: white !important;
            }
            .pdf-download-link {
                text-align: center;
                margin-top: 20px;
            }
            .pdf-download-link a {
                display: inline-block;
                background-color: #10b981;
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .pdf-download-link a:hover {
                background-color: #059669;
                transform: translateY(-2px);
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='report-header'>Interview Performance Report</h1>", unsafe_allow_html=True)
    
    if 'report_data' not in st.session_state:
        st.session_state.report_data = generate_report()
    
    report = st.session_state.report_data
    quant = report["quantitative_analysis"]
    total = quant["total"]
    
    # 1. Quantitative Analysis Section
    st.markdown("<div class='report-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='report-section-title'>Quantitative Analysis</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Total Questions</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-value'>{quant['total']}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        correct_first_percent = int((quant["correct_first_attempt"] / total * 100) if total > 0 else 0)
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Correct on First Try</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-value'>{quant['correct_first_attempt']} ({correct_first_percent}%)</div>", unsafe_allow_html=True)
        st.markdown("<div class='progress-bar-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='progress-bar good-progress' style='width: {correct_first_percent}%'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        correct_multiple_percent = int((quant["correct_multiple_attempts"] / total * 100) if total > 0 else 0)
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Correct After Hints</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-value'>{quant['correct_multiple_attempts']} ({correct_multiple_percent}%)</div>", unsafe_allow_html=True)
        st.markdown("<div class='progress-bar-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='progress-bar medium-progress' style='width: {correct_multiple_percent}%'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        wrong_percent = int((quant["wrong"] / total * 100) if total > 0 else 0)
        st.markdown("<div class='stat-box'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Could Not Answer</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='stat-value'>{quant['wrong']} ({wrong_percent}%)</div>", unsafe_allow_html=True)
        st.markdown("<div class='progress-bar-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='progress-bar poor-progress' style='width: {wrong_percent}%'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. Detailed Analysis (formerly section 3)
    st.markdown("<div class='report-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='report-section-title'>Detailed Performance Analysis</h2>", unsafe_allow_html=True)
    
    # Format the analysis text with proper spacing and line breaks
    analysis_text = report["detailed_analysis"].strip()
    st.markdown(f"<div class='analysis-text'>{analysis_text}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 3. Areas to Improve (formerly section 4)
    st.markdown("<div class='report-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='report-section-title'>Areas to Improve</h2>", unsafe_allow_html=True)
    
    for area in report["areas_to_improve"]:
        st.markdown(f"<div class='improve-item'>{area}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Generate PDF when button is clicked
    if st.button("Export to PDF", type="primary", key="export_pdf_btn"):
        with st.spinner("Generating PDF report..."):
            pdf_data = generate_pdf_report()
            if pdf_data:
                # Generate download link
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                download_link = get_pdf_download_link(pdf_data, f"Interview_Report_{timestamp}.pdf")
                st.success("PDF generated successfully!")
                st.markdown(f"<div class='pdf-download-link'>{download_link}</div>", unsafe_allow_html=True)
                
                # Add instructions
                st.markdown("""
                    <div style="margin-top: 10px; font-size: 14px; color: #6b7280; text-align: center;">
                        Click the button above to download your interview report as a PDF file.
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Failed to generate PDF. We're using a simpler PDF generation approach that might have limitations.")
                st.info("Try again or contact support if the issue persists.")
    
    # Button to go back to home
    st.markdown("<div class='home-button-container'>", unsafe_allow_html=True)
    if st.button("Return to Home", type="primary", key="report_home_btn"):
        # Reset session state for a fresh start
        for key in ['question_history', 'all_messages', 'current_question', 'messages', 'report_data']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Initialize a new question selector
        st.session_state.question_selector = QuestionSelector()
        st.session_state.page = 'home'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()