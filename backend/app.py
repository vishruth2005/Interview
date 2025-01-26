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
        st.session_state.messages = []
    else:
        st.session_state.current_question = None

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
            st.header("Generate Interview Questions")
            role = st.text_input("Enter the role you are applying for:")
            company = st.text_input("Enter the company you are applying to:")
            resume_file = st.file_uploader("Upload your resume (PDF format):", type=["pdf"])
            
            if st.button("Generate Questions"):
                if role and company and resume_file:
                    resume_content = extract_text_from_pdf(resume_file)
                    generate_questions(role, company, resume_content)
                    st.session_state.questions_generated = True
                    st.success("Questions generated successfully! You can now start the interview.")
                    select_and_initialize_next_question()
                else:
                    st.error("Please enter role, company, and upload your resume.")
            
            if st.button("Back to Home"):
                st.session_state.page = 'home'
                st.rerun()

            # Sidebar with statistics
            with st.sidebar:
                st.header("Interview Progress")
                total_questions = len(load_questions())
                answered_questions = len(st.session_state.question_selector.asked_questions)
                correct_answers = sum(1 for result in st.session_state.question_selector.asked_questions.values() if result == "correct")
                
                st.metric("Questions Answered", f"{answered_questions}/{total_questions}")
                st.metric("Correct Answers", correct_answers)
                
                st.markdown("---")
                st.markdown("### Categories Completed")
                categories_seen = set()
                for q_id in st.session_state.question_selector.asked_questions:
                    question = next((q for q in load_questions() if q['id'] == q_id), None)
                    if question:
                        categories_seen.add(question['category'])
                for category in categories_seen:
                    st.markdown(f"- {category}")
            
            if st.session_state.current_question:
                st.markdown("### Current Question:")
                st.info(st.session_state.current_question['question'])
                st.markdown("---")
                
                # Chat interface
                if 'messages' not in st.session_state:
                    st.session_state.messages = []

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if prompt := st.chat_input("Type your answer here..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.spinner("Evaluating your answer..."):
                        response: RunResponse = st.session_state.agent.run(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response.content})
                    with st.chat_message("assistant"):
                        st.markdown(response.content)
                    
                    # Check if the response indicates end of current question
                    if response.content.strip().lower() == "correct":
                        st.session_state.question_selector.record_result(
                            st.session_state.current_question['id'], "correct"
                        )
                        st.balloons()
                        st.success("🎉 Correct answer!")
                        select_and_initialize_next_question()
                        st.rerun()
                    elif "wrong" in response.content.lower():
                        st.session_state.question_selector.record_result(
                            st.session_state.current_question['id'], "wrong"
                        )
                        st.error("❌ Incorrect answer.")
                        select_and_initialize_next_question()
                        st.rerun()
        else:
            st.markdown("## 🎓 Interview Completed!")
            st.markdown("You have completed all available questions. Here's your performance summary:")
            
            col1, col2 = st.columns(2)
            with col1:
                total_questions = len(load_questions())
                answered_questions = len(st.session_state.question_selector.asked_questions)
                correct_answers = sum(1 for result in st.session_state.question_selector.asked_questions.values() if result == "correct")
                
                st.metric("Total Questions Attempted", answered_questions)
                st.metric("Correct Answers", correct_answers)
            
            with col2:
                st.markdown("### Performance by Category")
                categories = {}
                for q_id, result in st.session_state.question_selector.asked_questions.items():
                    question = next((q for q in load_questions() if q['id'] == q_id), None)
                    if question:
                        category = question['category']
                        if category not in categories:
                            categories[category] = {"correct": 0, "total": 0}
                        categories[category]["total"] += 1
                        if result == "correct":
                            categories[category]["correct"] += 1
                
                for category, stats in categories.items():
                    success_rate = (stats["correct"] / stats["total"]) * 100
                    st.markdown(f"- **{category}**: {success_rate:.1f}% ({stats['correct']}/{stats['total']})")

if __name__ == "__main__":
    main() 