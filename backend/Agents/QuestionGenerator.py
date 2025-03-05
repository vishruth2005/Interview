from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
import PyPDF2
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, Field
from typing import List
load_dotenv()
class FinalQuestion(BaseModel):
    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="Question text")
    template: str = Field(..., description="Expected approach to solve the problem")
    criteria: str = Field(..., description="Criteria to judge the answer")
    category: str = Field(..., description="Category of the question")

class SkillAnalysis(BaseModel):
    aligned:List[str] = Field(..., description="Skills aligned with both.")
    relevant:List[str] = Field(..., description="Skill present but less relevant")
    acquire:List[str] = Field(..., description="Skills to be acquired.")

class Keyword(BaseModel):
    keyword:str = Field(..., description="Name of the keyword.")
    subtopics:List[str] = Field(..., description="List of the subtopics after depth analysis for given keyword.")

class Question(BaseModel):
    question: str = Field(..., description="Question should be inserted here.")
    expected_approach: str = Field(..., description="The expected approach to solve the problem should be inserted here.")
    criteria: str = Field(..., description="The criteria to judge the answer for the question should be inserted here.")

class KeywordAnalysis(BaseModel):
    project_name:str = Field(..., description="Name of the project")
    keywords:List[str] = Field(..., description="List of keywords identified.")

class DepthAnalysis(BaseModel):
    project_name:str = Field(..., description="Name of the project.")
    analysis: List[Keyword] = Field(..., description="A list of depth analysis for each keyword.")

class Questions(BaseModel):
    questions:List[Question] = Field(..., description="List of questions generated.")

def to_json(data_string):  
    # Debugging statement to check the input string
    print("Debug: Raw data_string before processing:", data_string)  # Add this line for debugging
    json_data = json.loads(f'[{data_string.replace("}\n{", "}, {")}]')
    return json.dumps(json_data, indent=4)

class QuestionGenerator:
    def __init__(self, resume_content, role, company):
        """Initialize with resume content, role, and company."""
        self.resume = resume_content  # Extract text from the PDF content
        self.role = role
        self.company = company
        self.agent1 = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")), response_model=Question)
        self.agent2 = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")))
        self.keyword_analyser = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are a highly skilled and experienced keyword analysis expert specializing in resumes and professional documents."
                "You are provided with a resume."
                "Do a thorough keyword analysis of it."
            ),
            instructions = [
                "Analyze the 'Projects' section of the given resume thoroughly.",
                "Identify relevant keywords for each project, including:",
                "   - Technical terms (e.g., programming languages, frameworks, tools)",
                "   - Domain-specific jargon (e.g., finance, healthcare, AI-related terminology)",
                "   - Other significant descriptors or action verbs",
                "Format the output as follows: Project Name: [Comma-separated list of identified keywords]",
                "Ensure the output is accurate, concise, and captures the essence of the key elements from each project."
            ],
            response_model = KeywordAnalysis
        )
        self.depth_analyser = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "For each of the keywords specified for every project in the input provided,"
                "Your task involves decomposing these keywords into detailed sub-concepts."
            ),
            instructions = [
                "Decompose each keyword into specific, well-defined sub-concepts or components.",
                "Include technical, functional, and contextual sub-concepts where applicable, considering domain nuances.",
                "Ensure each sub-concept is comprehensive, granular, and captures all relevant dimensions.",
                "Format the output as follows:",
                "   Project1:",
                "       Keyword1: Sub-concept1, Sub-concept2, Sub-concept3, ...",
                "       Keyword2: Sub-concept1, Sub-concept2, Sub-concept3, ...",
                "   Project2:",
                "       Keyword1: Sub-concept1, Sub-concept2, Sub-concept3, ...",
                "       Keyword2: Sub-concept1, Sub-concept2, Sub-concept3, ...",
                "Provide examples to clarify complex sub-concepts if necessary.",
                "Ensure the decomposition is exhaustive and provides a detailed understanding of each topic."
            ],
            response_model = DepthAnalysis
        )

        self.skill_analyser = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are a highly experienced resume assistant and career advisor with expertise in tailoring resumes for specific companies and roles."
            ),
            instructions = [
                "Conduct a detailed analysis of the user's resume in relation to the target company and role.",
                "Divide your analysis into three sections focusing on skills alignment and gaps:",
                "1. **Skills aligned with both:**",
                "   - Identify and list all technical, functional, and soft skills in the resume that are directly relevant to the target role and company.",
                "   - Ensure these skills are contextually aligned with the industry, domain, and specific job responsibilities.",
                "2. **Skills present but less relevant:**",
                "   - Identify and list skills mentioned in the resume that are less critical or not directly aligned with the specific requirements.",
                "   - Focus on skills that could be peripheral or secondary in the context of the job.",
                "3. **Skills to be acquired:**",
                "   - Identify and list key skills missing from the resume that are essential or highly desirable for the role.",
                "   - Include industry-specific certifications, tools, or methodologies that are commonly expected or advantageous.",
                "   - Highlight areas for upskilling, including both technical and soft skills.",
                "Format the output as follows:",
                "   Skills aligned with both: [List of skills].",
                "   Skills present but less relevant: [List of skills].",
                "   Skills to be acquired: [List of skills].",
                "Ensure the analysis is thorough, precise, and directly tailored to the target role and company."
            ],
            response_model = SkillAnalysis
        )

        self.interview_questions_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are an experienced question creator."
                "Based pn the given details, generate good interview questions."
            ),
            instructions = [
                "Generate 5 well-structured interview questions based on the provided insights.",
                "Ensure question depth as follows:",
                "   - First two questions: Medium-level, focusing on moderately detailed subtopics.",
                "   - Remaining questions: In-depth, highly specific, focusing on niche subtopics critical to the role.",
                "Focus exclusively on subtopics derived from skill analysis keywords.",
                "Prioritize technical and functional skills, with minimal emphasis on soft skills unless explicitly relevant.",
                "For strongly aligned skills, create detailed questions exploring deeper subtopics.",
                "For moderately aligned skills, evaluate foundational understanding and applicability.",
                "Emphasize practical application, problem-solving, and hands-on experience.",
                "Avoid generic questions; tailor each to reflect specific role and company requirements.",
                "Format the output as follows:",
                "   questions:",
                "   1. question: [Highly specific and niche question on a critical subtopic]",
                "       expected_approach: [Expected approach to solve the problem]",
                "       criteria: [Criteria to judge the answer]",
                "   2. question: [Highly specific and niche question on a critical subtopic]",
                "       expected_approach: [Expected approach to solve the problem]",
                "       criteria: [Criteria to judge the answer]",
                "   3. question: [Highly specific and niche question on a critical subtopic]",
                "       expected_approach: [Expected approach to solve the problem]",
                "       criteria: [Criteria to judge the answer]",
                "   4. question: [Highly specific and niche question on a critical subtopic]",
                "       expected_approach: [Expected approach to solve the problem]",
                "       criteria: [Criteria to judge the answer]",
                "   5. question: [Highly specific and niche question on a critical subtopic]",
                "       expected_approach: [Expected approach to solve the problem]",
                "       criteria: [Criteria to judge the answer]",
                "Ensure the output follows the given format without unnecessary text and includes only 5 questions."
            ],
            response_model = Questions
        )
        self.theoretical_questions_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are a theoretical expert."
                "Based on the details provided generate good theoretical questions."
            ),
            instructions = [
                "Create exactly 3 explanatory interview questions that encourage candidates to articulate their understanding.",
                "Follow these guidelines:",
                "1. **Scope and Sub-concepts:**",
                "   - Focus each question on a single sub-concept or combine a maximum of two logically related sub-concepts.",
                "   - Avoid overly niche or unrelated sub-concept combinations.",
                "2. **Explanatory Focus:**",
                "   - Use explanatory question formats like 'Explain X,' 'What is the effect of X on Y,' or 'How does X relate to Y?'",
                "   - Keep phrasing simple and avoid jargon.",
                "3. **Accessibility:**",
                "   - Ensure questions are easy to understand and approachable.",
                "   - Avoid technical implementation or problem-solving questions.",
                "4. **Depth and Clarity:**",
                "   - Maintain a balance between general and moderately detailed questions.",
                "   - Provide room for thoughtful, structured responses.",
                "5. **Structured Format:**",
                "   - Provide exactly 3 questions, numbered and clearly phrased.",
                "   - Each question should explicitly mention the sub-concept(s) being addressed.",
                "   - Example format:",
                "     questions:",
                "     1. question: [Explain how sub-concept A influences sub-concept B.]",
                "         expected_approach: [Expected approach to solve the problem]",
                "         criteria: [Criteria to judge the answer]",
                "     2. question: [What is the role of sub-concept C in achieving goal D?]",
                "         expected_approach: [Expected approach to solve the problem]",
                "         criteria: [Criteria to judge the answer]",
                "     3. question: [Describe the relationship between sub-concepts Y and Z.]",
                "         expected_approach: [Expected approach to solve the problem]",
                "         criteria: [Criteria to judge the answer]",
                "6. **Example Questions:**",
                "   - For sub-concepts 'Machine Learning' and 'Data Quality,' a question might be:",
                "     'Explain how the quality of data affects the performance of machine learning models.'",
                "   - For sub-concepts 'Project Management' and 'Stakeholder Communication,' a question might be:",
                "     'What is the role of effective stakeholder communication in successful project management?'",
                "   - For a single sub-concept like 'Encryption,' a question might be:",
                "     'What is encryption, and why is it important in modern cybersecurity practices?'",
                "Ensure the output follows the given format without unnecessary text."
            ],
            response_model = Questions
        )
        self.skill_questions_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are a person speacialised in generating skill related questions."
                "Based on the given input generate skill related questions."
            ),
            instructions = [
                "Conduct an interview for the specified role by generating technical questions based on the skill analysis.",
                "Follow these steps:",
                "1. **Identify Relevant Technical Skills:**",
                "   - List all technical skills mentioned in the skill analysis relevant to the company's requirements.",
                "2. **Generate Technical Questions:**",
                "   - Create 10 well-structured and thoughtful technical questions using the identified skills.",
                "3. **Align with Example Questions:**",
                "   - Ensure questions match the style, depth, and structure of the example questions in the guide.",
                "4. **Role-Specific Focus:**",
                "   - Tailor questions to the specific requirements of the role, excluding soft skills.",
                "5. **Diverse Dimensions:**",
                "   - Each question should probe different dimensions of the technical skills required for the role.",
                "6. **Structured Format:**",
                "   - Format the output as follows:",
                "     questions:",
                "     1. question: [question]",
                "        expected_approach: [Expected approach to solve the problem]",
                "        criteria: [Criteria to judge the answer]",
                "     2. question: [question]",
                "        expected_approach: [Expected approach to solve the problem]",
                "        criteria: [Criteria to judge the answer]",
                "     ...",
                "     10. question: [question]",
                "        expected_approach: [Expected approach to solve the problem]",
                "        criteria: [Criteria to judge the answer]",
                "7. Ensure the output follows the given format without unnecessary text.",
                "8. Provide a detailed expected approach and criteria for each question.",
                "9. Generate exactly 10 questions."
            ],
            response_model = Questions
        )
        self.situations_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description = (
                "You are a highly experienced situation based questions creator."
                "Based on the given input create good situation based questions."
            ),
            instructions = [
                "Generate thoughtful, role-specific interview questions to evaluate the candidate's soft skills comprehensively.",
                "Follow these guidelines:",
                "1. **Soft Skills Identification:**",
                "   - Analyze the role's requirements and company standards to identify key soft skills.",
                "   - Consider skills highlighted in the candidate's resume.",
                "2. **Question Design:**",
                "   - Create situational questions that assess identified soft skills.",
                "   - Ensure questions are practical, realistic, and applicable to real-world scenarios.",
                "   - Use the style from reference for situation based questions as inspiration but craft unique questions.",
                "3. **Experience Integration:**",
                "   - Mix questions based on the candidate's past experiences and unrelated scenarios.",
                "   - Randomize the distribution to ensure variety.",
                "   - For experience-based questions, reference specific projects or achievements from the resume.",
                "4. **Avoid Explicit Labels:**",
                "   - Do not label questions as experience-based or not.",
                "5. **Edge Case Handling:**",
                "   - Ensure questions remain relevant to the role even if the resume lacks detailed information.",
                "   - Avoid assumptions beyond what is clearly stated in the resume.",
                "6. **Clarity and Precision:**",
                "   - Use clear and unambiguous language.",
                "   - Define necessary context within the question.",
                "   - Maintain a formal interview tone.",
                "7. **Structured Format:**",
                "   - Format the output as follows:",
                "     questions:",
                "     1. question: [question]",
                "        expected_approach: [Expected approach to solve the problem]",
                "        criteria: [Criteria to judge the answer]",
                "     2. question: [question]",
                "        expected_approach: [Expected approach to solve the problem]",
                "        criteria: [Criteria to judge the answer]",
                "8. Ensure the output follows the given format without unnecessary text.",
                "9. Provide a detailed expected approach and criteria for each question.",
                "10. Generate exactly 2 questions."
            ],
            response_model = Questions
        )
        
        with open('data/skills.json', 'r') as file:
            self.skill_guide = json.load(file)
        self.situation_guide = {
            "collaboration": [
                "Tell me about a time when you had to work closely with someone whose personality was very different from yours.",
                "Give me an example of a time you faced a conflict with a coworker. How did you handle that?",
                "Describe a time when you had to step up and demonstrate leadership skills.",
                "Tell me about a time you made a mistake and wish you'd handled a situation with a colleague differently.",
                "Tell me about a time you needed to get information from someone who wasn't very responsive. What did you do?"
            ],
            "client_focus": [
                "Describe a time when it was especially important to make a good impression on a client. How did you go about doing so?",
                "Give me an example of a time when you didn't meet a client's expectation. What happened, and how did you attempt to rectify the situation?",
                "Tell me about a time when you made sure a customer was pleased with your service.",
                "Describe a time when you had to interact with a difficult client or customer. What was the situation, and how did you handle it?",
                "When you're working with a large number of customers, it's tricky to deliver excellent service to them all. How do you go about prioritizing your customers' needs?"
            ],
            "stress_and_adaptability": [
                "Tell me about a time you were under a lot of pressure at work or at school. What was going on, and how did you get through it?",
                "Describe a time when your team or company was undergoing some change. How did that impact you, and how did you adapt?",
                "Tell me about settling into your last job. What did you do to learn the ropes?",
                "Give me an example of a time when you had to think on your feet.",
                "Tell me about a time you failed. How did you deal with the situation?"
            ],
            "time_management": [
                "Give me an example of a time you managed numerous responsibilities. How did you handle that?",
                "Describe a long-term project that you kept on track. How did you keep everything moving?",
                "Tell me about a time your responsibilities got a little overwhelming. What did you do?",
                "Tell me about a time you set a goal for yourself. How did you go about ensuring that you would meet your objective?",
                "Tell me about a time an unexpected problem derailed your planning. How did you recover?",
                "Tell me about a time when you had to establish priorities for yourself."
            ],
            "organization_and_delegation": [
                "Describe your management style. How do you successfully delegate tasks?",
                "Describe a time when being organized has helped you with a tight deadline."
            ],
            "communication": [
                "Tell me about a time when you had to rely on written communication to get your ideas across.",
                "Give me an example of a time when you were able to successfully persuade someone at work to see things your way.",
                "Describe a time when you were the resident technical expert. What did you do to make sure everyone was able to understand you?",
                "Give me an example of a time when you had to have a difficult conversation with a frustrated client or colleague. How did you handle the situation?",
                "Tell me about a successful presentation you gave and why you think it was a hit."
            ],
            "personal_accomplishments": [
                "Tell me about your proudest professional accomplishment.",
                "Describe a time when you saw a problem and took the initiative to correct it.",
                "Tell me about a time when you worked under either extremely close supervision or extremely loose supervision. How did you handle that?",
                "Give me an example of a time you were able to be creative with your work. What was exciting or difficult about it?",
                "Tell me about a time you were dissatisfied in your role. What could have been done to make it better?"
            ]
        }

    def extract_text_from_pdf(self, pdf_content):
        """Extract text from a PDF file content."""
        reader = PyPDF2.PdfReader(pdf_content)
        text = ''.join([page.extract_text() for page in reader.pages])
        return text

    def analyze_keywords(self):
        """Analyze keywords in the 'Projects' section of the resume."""
        run: RunResponse = self.keyword_analyser.run(self.resume)
        return run.content

    def analyze_depth(self, keyword_analysis):
        """Decompose keywords into detailed sub-concepts."""
        run: RunResponse = self.depth_analyser.run(keyword_analysis)
        return run.content

    def analyze_skills(self):
        """Analyze skills in the resume relative to the company and role."""
        prompt = (
            f"The user's resume content is as follows: {self.resume}."
            f"The target company is: {self.company}."
            f"The target role is: {self.role}."
        )
        run: RunResponse = self.skill_analyser.run(prompt)
        return run.content

    def generate_interview_questions(self):
        """Generate interview questions based on keyword, depth, and skill analyses."""
        self.keywords = self.analyze_keywords()
        self.depth_analysis = self.analyze_depth(self.keywords)
        self.skill_analysis = self.analyze_skills()
        prompt = (
            f"You are an experienced and highly skilled interviewer representing the company: {self.company}."
            f"The user's resume content is provided as follows: {self.resume}."
            f"The target role for the user is: {self.role}."
            f"The {self.depth_analysis} provides detailed insights into relevant concepts and sub-concepts."
            f"The {self.skill_analysis} outlines the necessity and relevance of each skill based on company and role requirements."
        )
        run: RunResponse = self.interview_questions_generator.run(prompt)
        return run.content
    
    def generate_theoretical_interview_questions(self):
        """Generate Theoretical interview questions based on keyword, depth, and skill analyses."""
        prompt = (
            f"You are an experienced and highly skilled interviewer representing the company: {self.company}."
            f"The user's resume content is provided as follows: {self.resume}."
            f"The {self.depth_analysis} provides detailed insights into relevant concepts and sub-concepts extracted from the user's resume."
        )
        run: RunResponse = self.theoretical_questions_generator.run(prompt)
        return run.content
    
    def generate_skill_questions(self):
        """Generate interview questions based on the skills."""
        prompt = (
            f"Assume you are an experienced interviewer representing the company '{self.company}'. "
            f"You are conducting an interview for a candidate applying for the role of '{self.role}'. "
            f"The skill analysis of the candidate's resume has identified the following: {self.skill_analysis}. "
            f"You also have access to a guide that outlines example topics and corresponding question formats in '{self.skill_guide}'. "
        )
        run: RunResponse = self.skill_questions_generator.run(prompt)
        return run.content

    def Generate_Situations(self):
        prompt = (
            f"Assume you are an experienced and detail-oriented interviewer representing the company '{self.company}'. "
            f"You are conducting an interview for a candidate applying for the role of '{self.role}'. "
            f"The candidate's resume is provided as follows: {self.resume}. "
            f"You are also provided with {self.situation_guide}, which serves as a reference for the style and structure of situation-based questions. "
        )
        run: RunResponse = self.situations_generator.run(prompt)
        return run.content

    def save_questions_to_json(self, interview_questions, theoretical_questions, skill_questions, situational_questions):
        """Convert all questions to FinalQuestion format and save to questions.json"""
        json_data = []
        question_id = 1

        for question in interview_questions.questions:
            json_data.append({
                "id": str(question_id),
                "question": question.question,
                "template": question.expected_approach,
                "criteria": question.criteria,
                "category": "Project Based"
            })
            question_id += 1

        for question in theoretical_questions.questions:
            json_data.append({
                "id": str(question_id),
                "question": question.question,
                "template": question.expected_approach,
                "criteria": question.criteria,
                "category": "Theory Based"
            })
            question_id += 1

        for question in skill_questions.questions:
            json_data.append({
                "id": str(question_id),
                "question": question.question,
                "template": question.expected_approach,
                "criteria": question.criteria,
                "category": "Skill Based"
            })
            question_id += 1
        
        for question in situational_questions.questions:
            json_data.append({
                "id": str(question_id),
                "question": question.question,
                "template": question.expected_approach,
                "criteria": question.criteria,
                "category": "Situation Based"
            })
            question_id += 1

        # Save to questions.json
        with open('questions.json', 'w') as f:
            json.dump({"questions": json_data}, f, indent=4)


# if __name__ == "__main__":
#     builder = QuestionGenerator(
#         "data/resume.pdf",
#         "Associate",
#         "Boston Consulting Groups"
#     )

#     # Generate interview questions in batches
#     interview_questions = builder.generate_interview_questions()
#     theoretical_questions = builder.generate_theoretical_interview_questions()
#     skill_questions = builder.generate_skill_questions()
#     situational_questions = builder.Generate_Situations()
#     builder.save_questions_to_json(
#         interview_questions,
#         theoretical_questions,
#         skill_questions,
#         situational_questions
#     )