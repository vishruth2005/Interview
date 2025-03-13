import streamlit as st
import json
import random
from typing import Dict, List
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
from utils.voice_utils import text_to_speech_elevenlabs, speech_to_text_assemblyai, cleanup_audio_file

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
    </style>
""", unsafe_allow_html=True)

def to_json(data_string):  
    json_data = json.loads(f'[{data_string.replace("}\n{", "}, {")}]')
    return json.dumps(json_data, indent=4)

def extract_text_from_pdf(pdf_content):
    """Extract text from a PDF file content."""
    reader = PyPDF2.PdfReader(pdf_content)
    text = ''.join([page.extract_text() for page in reader.pages])
    return text

class QuestionSelector:
    def __init__(self):
        self.asked_questions = {}  # Format: {question_id: result}
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

def select_and_initialize_next_question():
    """Select and initialize the next question."""
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
    # Display the concatenated resume string in the frontend
    st.markdown(linked_in)
    st.markdown("## Skills")
    st.markdown(skills_result)
    st.markdown(resume_result)  # Display the concatenated string as markdown

def main():
    # Initialize session state variables if they don't exist
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
            
            linkedin_url = st.text_input("Enter your LinkedIn profile URL:")
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
                if linkedin_url and role and repos:
                    with st.spinner("Building your resume..."):
                        resume_builder = ResumeBuilder(repos, linkedin_url, role)
                        resume_result, skills_result, linked_in = resume_builder.build()
                        print(resume_result)
                        print(skills_result)
                        print(linked_in)
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
                        if st.button("Generate Questions", key="generate_questions_btn", type="primary"):
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
                # Interview in progress
                if st.session_state.current_question:
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
                            audio_file = text_to_speech_elevenlabs(welcome_text)
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
                            </style>
                        """, unsafe_allow_html=True)
                        
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
                            audio_file = text_to_speech_elevenlabs(current_question)
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
                                    audio_file = text_to_speech_elevenlabs(message["content"])
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
                                            transcribed_text = speech_to_text_assemblyai(audio_bytes)
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
                        
                        st.markdown('</div>', unsafe_allow_html=True)

def process_response(user_input: str, content_container):
    """Process user response and generate AI response with voice."""
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
            
            audio_file = text_to_speech_elevenlabs(response_text)
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
    st.balloons()
    
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
    audio_file = text_to_speech_elevenlabs(transition_msg)
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
    audio_file = text_to_speech_elevenlabs(transition_msg)
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

if __name__ == "__main__":
    main() 