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
    page_title="AI Interview System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stTextInput > div > div > input {
        min-height: 100px;
    }
    .stMarkdown {
        font-size: 18px;
    }
    .voice-input-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
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
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'role': None,
            'company': None,
            'resume_file': None
        }

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🤖 AI Interview System")
        st.markdown("---")

        # Home page with two buttons
        if st.session_state.page == 'home':
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Build Resume", use_container_width=True):
                    st.session_state.page = 'resume'
            with col2:
                if st.button("🎯 Start Interview", use_container_width=True):
                    st.session_state.page = 'interview'

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
                st.header("Generate Interview Questions")
                role = st.text_input("Enter the role you are applying for:")
                company = st.text_input("Enter the company you are applying to:")
                resume_file = st.file_uploader("Upload your resume (PDF format):", type=["pdf"])
                
                if st.button("Generate Questions"):
                    if role and company and resume_file:
                        # Store form data in session state
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
                
                if st.button("Back to Home"):
                    st.session_state.page = 'home'
                    st.rerun()

            elif st.session_state.preparing_interview:
                st.empty()  # Clear previous content
                col1, col2, col3 = st.columns([2, 3, 2])
                with col2:
                    st.markdown("""
                        <div style='text-align: center; padding: 50px 0;'>
                            <h2>🎯 Preparing Your Customized Interview</h2>
                            <p style='font-size: 18px;'>Please wait while we analyze your resume and prepare relevant questions...</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show a progress animation
                    progress_placeholder = st.empty()
                    progress_bar = progress_placeholder.progress(0)
                    for i in range(100):
                        progress_bar.progress(i + 1)
                        time.sleep(0.01)
                    
                    # Generate questions after progress bar using stored form data
                    resume_content = extract_text_from_pdf(st.session_state.form_data['resume_file'])
                    generate_questions(
                        st.session_state.form_data['role'],
                        st.session_state.form_data['company'],
                        resume_content
                    )
                    st.session_state.questions_generated = True
                    st.session_state.interview_started = False
                    st.session_state.preparing_interview = False
                    select_and_initialize_next_question()
                    st.rerun()

            else:
                # Interview in progress
                if st.session_state.current_question:
                    # Container for all content except chat input
                    content_container = st.container()
                    
                    # Exit button in the top right
                    col1, col2, col3 = st.columns([6, 1, 1])
                    with col3:
                        if st.button("Exit Interview", type="secondary"):
                            st.session_state.page = 'report'
                            st.rerun()
                    
                    with content_container:
                        if not st.session_state.interview_started:
                            welcome_text = """
                            ### Welcome to your AI Interview! 👋
                            
                            I'm here to have a conversation with you about your experience and skills. Don't worry - this is meant to be 
                            a comfortable discussion where you can showcase your expertise. Take your time with your answers, and feel free 
                            to ask for clarification if needed.
                            
                            You can choose to respond either by voice or text. For voice responses, use the microphone in the voice input section.
                            
                            Let's start with our first question...
                            """
                            st.markdown(welcome_text)
                            
                            # Generate and play welcome message
                            if 'welcome_played' not in st.session_state:
                                audio_file = text_to_speech_elevenlabs(welcome_text)
                                if audio_file:
                                    st.audio(audio_file, format='audio/mp3')
                                    cleanup_audio_file(audio_file)
                                st.session_state.welcome_played = True
                            
                            st.session_state.interview_started = True
                            if 'messages' not in st.session_state:
                                st.session_state.messages = []
                        
                        if st.session_state.transition_message:
                            st.markdown(st.session_state.transition_message)
                            st.session_state.transition_message = None
                        
                        st.markdown("### Question:")
                        current_question = st.session_state.current_question['question']
                        st.info(current_question)
                        
                        # Generate and play question audio
                        if 'last_question' not in st.session_state or st.session_state.last_question != current_question:
                            audio_file = text_to_speech_elevenlabs(current_question)
                            if audio_file:
                                st.audio(audio_file, format='audio/mp3')
                                cleanup_audio_file(audio_file)
                            st.session_state.last_question = current_question
                        
                        st.markdown("---")
                        
                        # Display chat history
                        for message in st.session_state.messages:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                        
                        # Input section with tabs for voice and text
                        tab1, tab2 = st.tabs(["💬 Text Input", "🎤 Voice Input"])
                        
                        with tab1:
                            # Text input option
                            if prompt := st.chat_input("Type your answer here..."):
                                st.session_state.messages.append({"role": "user", "content": prompt})
                                with st.chat_message("user"):
                                    st.markdown(prompt)
                                
                                process_response(prompt, content_container)
                        
                        with tab2:
                            st.markdown('<div class="voice-input-section">', unsafe_allow_html=True)
                            st.markdown("### Record Your Answer")
                            audio_bytes = st.audio_input("Record your answer")
                            
                            if audio_bytes:
                                with st.spinner("Transcribing your answer..."):
                                    transcribed_text = speech_to_text_assemblyai(audio_bytes)
                                    if transcribed_text:
                                        st.session_state.messages.append({"role": "user", "content": transcribed_text})
                                        with st.chat_message("user"):
                                            st.markdown(transcribed_text)
                                        
                                        process_response(transcribed_text, content_container)
                            st.markdown('</div>', unsafe_allow_html=True)

def process_response(user_input: str, content_container):
    """Process user response and generate AI response with voice."""
    with st.spinner("Evaluating your answer..."):
        response: RunResponse = st.session_state.agent.run(user_input)
        response_text = response.content.strip()
        
        # Handle non-terminal responses (not correct/wrong)
        if response_text.lower() not in ["correct", "wrong"]:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with content_container.chat_message("assistant"):
                st.markdown(response_text)
                audio_file = text_to_speech_elevenlabs(response_text)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3')
                    cleanup_audio_file(audio_file)
        
        # Handle terminal responses (correct/wrong)
        if response_text.lower() == "correct":
            handle_correct_answer(content_container)
        elif response_text.lower() == "wrong":
            handle_wrong_answer(content_container)

def handle_correct_answer(content_container):
    """Handle correct answer response."""
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
    st.session_state.messages.append({"role": "assistant", "content": transition_msg})
    
    audio_file = text_to_speech_elevenlabs(transition_msg)
    if audio_file:
        with content_container.chat_message("assistant"):
            st.audio(audio_file, format='audio/mp3')
        cleanup_audio_file(audio_file)
    
    next_question = select_and_initialize_next_question()
    if next_question:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"### Next Question:\n{next_question['question']}"
        })
    st.rerun()

def handle_wrong_answer(content_container):
    """Handle wrong answer response."""
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
    st.session_state.messages.append({"role": "assistant", "content": transition_msg})
    
    audio_file = text_to_speech_elevenlabs(transition_msg)
    if audio_file:
        with content_container.chat_message("assistant"):
            st.audio(audio_file, format='audio/mp3')
        cleanup_audio_file(audio_file)
    
    next_question = select_and_initialize_next_question()
    if next_question:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"### Next Question:\n{next_question['question']}"
        })
    st.rerun()

if __name__ == "__main__":
    main() 