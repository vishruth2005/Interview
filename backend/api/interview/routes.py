from fastapi import APIRouter, Body, HTTPException, Depends, Path, Query
import json
import random
from typing import Dict, List
import os
from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
from phi.storage.agent.sqlite import SqlAgentStorage
from dotenv import load_dotenv
from Agents.QuestionGenerator import QuestionGenerator
from pydantic import BaseModel

load_dotenv()

router = APIRouter()

#moved QuestionSelector to global scope
question_selector = None
current_agent = None # Global agent instance
questions = [] #Global list of questions

def to_json(data_string):
    json_data = json.loads('[' + data_string.replace('}\n{', '}, {') + ']')
    return json.dumps(json_data, indent=4)

# Global QuestionGenerator instance
builder = None

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
            selected_question = random.choice(available_questions)

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
        instructions=[
            "If the candidate's response does not meet expectations or lacks key details, provide gentle guidance with very small hints that steer them toward the correct answer. "
            "Avoid giving away the answer directly; instead, ask probing questions or suggest areas they might elaborate on. "
            "In cases where a candidate appears to misunderstand the question, clarify it without leading them too much. "
            "If a candidate provides an answer that is partially correct but missing critical elements, acknowledge what they did well while encouraging them to expand on their response. "
            "Once you determine that a candidate's answer meets the necessary criteria—demonstrating sufficient understanding, relevance, and detail—respond with 'correct' without any unnecessary text. "
            "Do not include any unnecessary text or commentary in your response; keep it concise and focused solely on the evaluation outcome."
            "If a satisfactory answer is provided, respond with 'correct' without any unnecessary text. "
            "If a satisfactory answer is not provided within 3 attempts, respond with 'wrong' without any unnecessary text."
        ],
        debug_mode=True
    )

def load_questions():
    global questions
    try:
        with open('questions.json', 'r') as f:
            data = json.load(f)
            questions = data['questions']
            return questions
    except FileNotFoundError:
        print("Questions file not found. Please make sure questions.json exists in the backend directory.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON format in questions file.")
        return []

async def select_and_initialize_next_question():
    """Select and initialize the next question."""
    global question_selector, current_agent, questions

    if not questions:
        questions = load_questions()

    if not question_selector:
         question_selector = QuestionSelector()

    question_categories = {q['id']: q['category'] for q in questions}
    next_question = question_selector.select_next_question(questions, question_categories)

    if next_question:
        #If agent doesnt exist, create it, otherwise, keep using the same one
        if current_agent is None:
            current_agent = initialize_agent(
                next_question['question'],
                next_question['template'],
                next_question['criteria']
            )

        return {"question": next_question}
    else:
        return None

def generate_questions(role: str, company: str, resume_content: str):
    """Generate questions based on the resume, role, and company."""
    global builder  # Use the global builder instance
    builder = QuestionGenerator(
        resume_content,
        role,
        company
    )

    # Generate interview questions in batches
    interview_questions = builder.generate_interview_questions()
    theoretical_questions = builder.generate_theoretical_interview_questions()
    skill_questions = builder.generate_skill_questions()
    situational_questions = builder.Generate_Situations()
    builder.save_questions_to_json(
        interview_questions,
        theoretical_questions,
        skill_questions,
        situational_questions
    )

class InterviewData(BaseModel):
    role: str
    company: str
    resume_content: str  # Assuming you're getting pre-parsed PDF content

@router.post("/generate_interview_questions/")
async def generate_interview_questions_endpoint(interview_data: InterviewData):
    """
    Endpoint to generate interview questions based on role, company, and resume content.
    """
    global builder

    try:
        generate_questions(interview_data.role, interview_data.company, interview_data.resume_content)
        return {"message": "Interview questions generated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/next_question/")
async def get_next_question():
    """
    Endpoint to get the next interview question and its associated agent.
    """
    next_question_data = await select_and_initialize_next_question()
    if next_question_data:
        return next_question_data
    else:
        raise HTTPException(status_code=404, detail="No more questions available.")

@router.post("/evaluate_answer/{question_id}")
async def evaluate_answer(question_id: str, answer: str = Body(...)):
    """
    Endpoint to evaluate a candidate's answer.
    """
    global current_agent

    if not current_agent:
        raise HTTPException(status_code=404, detail="No active agent session.")

    # Run the agent to evaluate the answer
    response: RunResponse = current_agent.run(answer)

    # Record the result
    global question_selector
    if question_selector:
        if "correct" in response.content.lower():
            question_selector.record_result(question_id, "correct")
        elif "wrong" in response.content.lower():
            question_selector.record_result(question_id, "wrong")

    return {"evaluation": response.content}