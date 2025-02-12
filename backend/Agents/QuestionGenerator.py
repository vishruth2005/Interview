from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
import PyPDF2
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, Field
load_dotenv()
class FinalQuestion(BaseModel):
    id: str = Field(..., description="Unique identifier for the question")
    question: str = Field(..., description="Question text")
    template: str = Field(..., description="Expected approach to solve the problem")
    criteria: str = Field(..., description="Criteria to judge the answer")
    category: str = Field(..., description="Category of the question")

class Question(BaseModel):
    question: str = Field(..., description="Question should be inserted here.")
    expected_approach: str = Field(..., description="The expected approach to solve the problem should be inserted here.")
    criteria: str = Field(..., description="The criteria to judge the answer for the question should be inserted here.")

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
        prompt = (
            "You are a highly skilled and experienced keyword analysis expert specializing in resumes and professional documents."
            f"You are provided with a resume. The content of the resume is as follows: {self.resume}."
            "Your task is to analyze the 'Projects' section of the given resume thoroughly."
            "For each project mentioned in the 'Projects' section, identify all relevant keywords, including but not limited to:"
            "1. Technical terms (e.g., programming languages, frameworks, tools)."
            "2. Domain-specific jargon (e.g., finance, healthcare, AI-related terminology)."
            "3. Other significant descriptors or action verbs."
            "The output should be in the following format:"
            "Project Name: [Comma-separated list of identified keywords for this project]"
            "Ensure the output is accurate, concise, and captures the essence of the key elements from each project."
        )
        run: RunResponse = self.agent2.run(prompt)
        return run.content

    def analyze_depth(self, keyword_analysis):
        """Decompose keywords into detailed sub-concepts."""
        prompt = (
            f"For each of the keywords specified for every project in {keyword_analysis},"
            "Your task is to:"
            "1. For every Keyword, decompose it into specific, detailed sub-concepts or components, ensuring each sub-concept is well-defined and clearly explains its role or significance."
            "2. Include technical, functional, and contextual sub-concepts where applicable, considering the nuances of the domain or field."
            "3. Ensure each sub-concept is comprehensive, granular, and captures all relevant dimensions."
            "The output should follow this structured format:"
            "Project1:"
            "Keyword1: Sub-concept1, Sub-concept2, Sub-concept3, ..."
            "Keyword2: Sub-concept1, Sub-concept2, Sub-concept3, ..."
            "Project2:"
            "Keyword1: Sub-concept1, Sub-concept2, Sub-concept3, ..."
            "Keyword2: Sub-concept1, Sub-concept2, Sub-concept3, ..."
            "Make sure the decomposition is exhaustive and provides a detailed understanding of each topic and its constituent elements. Include examples, if relevant, to clarify complex sub-concepts."
        )
        run: RunResponse = self.agent2.run(prompt)
        return run.content

    def analyze_skills(self):
        """Analyze skills in the resume relative to the company and role."""
        prompt = (
            "You are a highly experienced resume assistant and career advisor with expertise in tailoring resumes for specific companies and roles."
            "Your task is to conduct a detailed analysis of the user's resume in relation to the target company and role."
            f"The user's resume content is as follows: {self.resume}."
            f"The target company is: {self.company}."
            f"The target role is: {self.role}."
            "Your analysis must be divided into three clear and distinct sections, focusing on skills alignment and gaps in relation to the requirements of the specified company and role:"
            "1. Skills aligned with the company's and role's requirements:"
            "   - Identify and list all technical, functional, and soft skills currently present in the user's resume that are directly relevant to the requirements of the target role and company."
            "   - Ensure these skills are contextually aligned with the industry, domain, and specific job responsibilities."
            "2. Skills present but less relevant to the company's and role's requirements:"
            "   - Identify and list the skills mentioned in the resume that, while useful, are less critical or not directly aligned with the specific requirements of the target role and company."
            "   - Focus on skills that could be peripheral or secondary in the context of the job."
            "3. Skills to be acquired:"
            "   - Identify and list the key skills missing from the user's resume that are essential or highly desirable for excelling in the specified role and company."
            "   - Include any industry-specific certifications, tools, or methodologies that are commonly expected or advantageous for the role."
            "   - Highlight areas for upskilling, including both technical and soft skills, where applicable."
            "The output should be concise and in the following format, without any additional explanations:"
            "Skills aligned with both: [List of skills]."
            "Skills present but less relevant: [List of skills]."
            "Skills to be acquired: [List of skills]."
            "Ensure the analysis is thorough, precise, and directly tailored to the target role and company."
        )
        run: RunResponse = self.agent2.run(prompt)
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
                    f"The {self.depth_analysis} provides detailed insights into the relevant concepts and sub-concepts that need to be focused on during the interview."
                    f"The {self.skill_analysis} outlines the necessity and relevance of each skill, along with their associated subtopics, based on the requirements of the company and the target role."
                    "Your task is to generate 5 well-structured interview questions, ensuring the following:"
                    "1. *Question Depth*:"
                    "   - The first two questions should be medium-level, focusing on moderately detailed subtopics."
                    "   - All remaining questions must be in-depth, highly specific, and focus on niche subtopics critical to the role and company requirements."
                    "2. *Subtopic-Centric Questions Only*: All questions must be built exclusively on the subtopics derived from the keywords in the skill analysis. No question should directly reference the keyword itself."
                    "3. *Weightage on Technical and Functional Skills*:"
                    "   - Focus primarily on technical and functional skills, crafting detailed questions to evaluate the user's depth of knowledge, expertise, and practical application."
                    "   - Soft skills may be given minimal weightage or omitted entirely unless explicitly relevant to the role."
                    "4. *Skill-Relevance Focus*:"
                    "   - For skills strongly aligned with the role and company, prioritize creating detailed, highly specific questions exploring deeper subtopics."
                    "   - For moderately aligned skills, use subtopics to create questions that evaluate foundational understanding and applicability."
                    "5. *Practical Application Emphasis*: Frame questions to test the user's problem-solving abilities, hands-on experience, and practical application of concepts, especially for technical and functional skills."
                    "6. *Avoid Generic Questions*: Ensure each question is uniquely tailored, leveraging subtopics to reflect the specific requirements of the target role and company."
                    "7. *Structured Format*: The output should follow this structured format:"
                    "   questions:(Should not be anything else. It should be questions only)"
                    "   1. question: [Highly specific and niche question on a critical subtopic]"
                    "   expected_approach: [Expected approach to solve the problem]"
                    "   criteria: [Criteria to judge the answer]"
                    "   2. question: [Highly specific and niche question on a critical subtopic]"
                    "   expected_approach: [Expected approach to solve the problem]"
                    "   criteria: [Criteria to judge the answer]"
                    "   3. question: [Highly specific and niche question on a critical subtopic]"
                    "   expected_approach: [Expected approach to solve the problem]"
                    "   criteria: [Criteria to judge the answer]"
                    "   ..."
                    "   5. question: [Highly specific and niche question on another critical subtopic]"
                    "   expected_approach: [Expected approach to solve the problem]"
                    "   criteria: [Criteria to judge the answer]"
                    "8. Make sure it should follow given format and no unnecessary text should be present."
                    "9. Only 5 questions should be generated"
                )

        run: RunResponse = self.agent1.run(prompt)
        return run.content
    
    def generate_theoretical_interview_questions(self):
        """Generate Theoretical interview questions based on keyword, depth, and skill analyses."""
        prompt = (
                    f"You are an experienced and highly skilled interviewer representing the company: {self.company}."
                    f"The user's resume content is provided as follows: {self.resume}."
                    f"The {self.depth_analysis} provides detailed insights into the relevant concepts and sub-concepts extracted from the user's resume."
                    "Your task is to create exactly 3 explanatory interview questions. Each question should be simple, clear, and encourage the candidate to articulate their understanding in an explanatory manner. Follow these guidelines:"
                    "1. *Scope and Sub-concepts:*"
                    "   - Each question should focus on a single sub-concept or combine a maximum of two logically related sub-concepts."
                    "   - Avoid overly niche or unrelated sub-concept combinations."
                    "2. *Explanatory Focus:*"
                    "   - Questions should primarily aim for explanations, such as 'Explain X,' 'What is the effect of X on Y,' or 'How does X relate to Y?'"
                    "   - Keep the phrasing simple, avoiding jargon or intimidating language."
                    "3. *Accessibility:*"
                    "   - Ensure questions are easy to understand and approachable, designed to help candidates explain concepts without unnecessary complexity."
                    "   - Avoid technical implementation or problem-solving questions."
                    "4. *Depth and Clarity:*"
                    "   - Maintain a balance between general and moderately detailed questions."
                    "   - Ensure the questions provide room for thoughtful, structured responses."
                    "5. *Structured Format:*"
                    "   - Provide exactly 3 questions, numbered and clearly phrased."
                    "   - Each question should explicitly mention the sub-concept(s) being addressed."
                    "   - Example format:"
                    "     questions:"
                    "     1. question: [Explain how sub-concept A influences sub-concept B.]"
                    "     expected_approach: [Expected approach to solve the problem]"
                    "     criteria: [Criteria to judge the answer]"
                    "     2. question: [What is the role of sub-concept C in achieving goal D?]"
                    "     expected_approach: [Expected approach to solve the problem]"
                    "     criteria: [Criteria to judge the answer]"
                    "     ..."
                    "     5. question: [Describe the relationship between sub-concepts Y and Z.]"
                    "     expected_approach: [Expected approach to solve the problem]"
                    "     criteria: [Criteria to judge the answer]"
                    "6. *Example Questions:*"
                    "   - For sub-concepts 'Machine Learning' and 'Data Quality,' a question might be:"
                    "     'Explain how the quality of data affects the performance of machine learning models.'"
                    "   - For sub-concepts 'Project Management' and 'Stakeholder Communication,' a question might be:"
                    "     'What is the role of effective stakeholder communication in successful project management?'"
                    "   - For a single sub-concept like 'Encryption,' a question might be:"
                    "     'What is encryption, and why is it important in modern cybersecurity practices?'"
                    "Your goal is to craft 3 simple, explanatory questions that allow candidates to provide clear and thoughtful explanations, ensuring the questions are approachable, logical, and aligned with the sub-concepts provided in the depth analysis."
                    "Make sure it should follow given format and no unnecessary text should be present."
                    "After each question generated, give a detailed expected approach, the user has to take while answering the question and the criteria required to fulfill it."
                )
        run: RunResponse = self.agent1.run(prompt)
        return run.content
    
    def generate_skill_questions(self):
        """Generate interview questions based on the skills."""
        prompt = (
            f"Assume you are an experienced interviewer representing the company '{self.company}'. "
            f"You are conducting an interview for a candidate applying for the role of '{self.role}'. "
            f"The skill analysis of the candidate's resume has identified the following: {self.skill_analysis}. "
            f"You also have access to a guide that outlines example topics and corresponding question formats in '{self.skill_guide}'. "
            f"Your task is as follows: "
            f"1. Identify all technical skills mentioned in the skill analysis that are relevant to the requirements of the company, regardless of whether the applicant possesses them or not. "
            f"2. Using these identified technical skills, generate 10 well-structured and thoughtful technical questions. "
            f"3. The questions should align with the style, depth, and structure of the example questions provided in the guide, while covering diverse aspects of the relevant concepts. "
            f"4. Ensure the questions are tailored to the specific requirements of the role and exclude any focus on soft skills. "
            f"5. Each question should probe different dimensions of the technical skills required for the role."
            f"6. The format followed should be:"
            f"    questions:"
            f"    1. question: [question]"
            f"     expected_approach: [Expected approach to solve the problem]"
            f"     criteria: [Criteria to judge the answer]"
            f"    2. question: [question]"
            f"     expected_approach: [Expected approach to solve the problem]"
            f"     criteria: [Criteria to judge the answer]"
            f"    ...."
            f"    10. question: [question]"
            f"     expected_approach: [Expected approach to solve the problem]"
            f"     criteria: [Criteria to judge the answer]"
            f"7. Make sure it should follow given format and no unnecessary text should be present."
            f"8.After each question generated, give a detailed expected approach, the user has to take while answering the question and the criteria required to fulfill it."
            f"9.Only 10 questions should be generated"
        )

        run: RunResponse = self.agent1.run(prompt)
        return run.content

    def Generate_Situations(self):
        prompt = (
                    f"Assume you are an experienced and detail-oriented interviewer representing the company '{self.company}'. "
                    f"You are conducting an interview for a candidate applying for the role of '{self.role}', a position that requires a specific set of skills and attributes. "
                    f"The candidate's resume is provided as follows: {self.resume}. "
                    f"You are also provided with {self.situation_guide}, which serves as a reference for the style and structure of situation-based questions. "
                    f"Your objective is to generate thoughtful, role-specific interview questions designed to evaluate the candidate's soft skills comprehensively. "
                    f"To achieve this, adhere to the following guidelines: "
                    f"\n\n1. Soft Skills Identification: "
                    f"   - Analyze the role's requirements and the company's standards to identify the key soft skills expected of the candidate. "
                    f"   - Consider any skills explicitly or implicitly highlighted in the candidate's resume. "
                    f"\n\n2. Question Design: "
                    f"   - Create a total of 10 situational questions that thoroughly assess the identified soft skills. "
                    f"   - Ensure the questions are practical, realistic, and applicable to real-world scenarios relevant to the role. Avoid vagueness or overly generic scenarios. "
                    f"   - Use the style and approach outlined in {self.situation_guide} as inspiration, but ensure all questions are uniquely crafted. "
                    f"\n\n3. Experience Integration: "
                    f"   - Incorporate a mix of questions derived from the candidate's past experiences (as outlined in their resume) and questions that are unrelated to their experiences. "
                    f"   - Randomize the distribution of experience-based and non-experience-based questions to ensure variety, but avoid any patterns or biases. "
                    f"   - For experience-based questions, reference specific projects, roles, or achievements described in the resume. "
                    f"   - For non-experience-based questions, craft scenarios that simulate challenges or situations the candidate might face in this role. "
                    f"\n\n4. Avoid Explicit Labels: "
                    f"   - Do not explicitly label or identify which questions are experience-based and which are not. Ensure they flow naturally within the set. "
                    f"\n\n5. Edge Case Handling: "
                    f"   - Ensure all questions remain relevant to the role, even if the candidate's resume lacks detailed information or explicitly stated soft skills. Use general industry standards and context as a fallback. "
                    f"   - Avoid making assumptions about the candidate's prior experience beyond what is clearly stated in the resume. "
                    f"   - Ensure the questions are appropriate for the role's level (e.g., entry-level, mid-level, leadership) and do not introduce situations that are unrealistic for the position. "
                    f"\n\n6. Clarity and Precision: "
                    f"   - Make sure the language used in the questions is clear and unambiguous. "
                    f"   - Define any necessary context within the question to avoid misinterpretation. "
                    f"   - Use professional and neutral phrasing to maintain a formal interview tone. "
                    f" The format followed should be:"
                    f"    questions:"
                    f"    1. question: [question]"
                    f"     expected_approach: [Expected approach to solve the problem]"
                    f"     criteria: [Criteria to judge the answer]"
                    f"    2. question: [question]"
                    f"     expected_approach: [Expected approach to solve the problem]"
                    f"     criteria: [Criteria to judge the answer]"
                    f"    ...."
                    f"    10. question: [question]"
                    f"     expected_approach: [Expected approach to solve the problem]"
                    f"     criteria: [Criteria to judge the answer]"
                    f"The output should have only 2 questions "
                    f" Make sure it should follow given format and no unnecessary text should be present."
                    f"After each question generated, give a detailed expected approach, the user has to take while answering the question and the criteria required to fulfill it."
                )

        run: RunResponse = self.agent1.run(prompt)
        return run.content
    
    def save_questions_to_json(self, interview_questions, theoretical_questions, skill_questions, situational_questions):
        """Convert all questions to FinalQuestion format and save to questions.json"""
        all_questions = []
        question_id = 1

        def process_questions(questions_str, category):
            nonlocal question_id
            try:
                # First, clean up the input string to ensure it's valid JSON
                questions_str = questions_str.strip()
                if not questions_str.startswith('['):
                    questions_str = f'[{questions_str}]'
                
                data = json.loads(questions_str)
                questions = []
                
                # Handle different possible JSON structures
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            if "questions" in item:
                                questions.extend(item["questions"])
                            elif "question" in item:
                                # If the item itself is a question
                                questions.append(item)
                        elif isinstance(item, str):
                            # Parse the question string that contains "question:", "expected_approach:", etc.
                            parts = item.split('\n')
                            current_question = {}
                            for part in parts:
                                part = part.strip()
                                if part.startswith("question:"):
                                    current_question["question"] = part.replace("question:", "").strip()
                                elif part.startswith("expected_approach:"):
                                    current_question["expected_approach"] = part.replace("expected_approach:", "").strip()
                                elif part.startswith("criteria:"):
                                    current_question["criteria"] = part.replace("criteria:", "").strip()
                            if current_question:
                                questions.append(current_question)

                for q in questions:
                    if isinstance(q, dict) and "question" in q:
                        final_q = FinalQuestion(
                            id=str(question_id),
                            question=q["question"],
                            template=q.get("expected_approach", ""),
                            criteria=q.get("criteria", ""),
                            category=category
                        )
                        all_questions.append(final_q.dict())
                        question_id += 1
                
            except Exception as e:
                print(f"Error processing questions for category {category}: {str(e)}")
                print(f"Input string: {questions_str}")

        # Process each type of question
        if interview_questions:
            process_questions(interview_questions, "Project Based")
        if theoretical_questions:
            process_questions(theoretical_questions, "Theoretical")
        if skill_questions:
            process_questions(skill_questions, "Technical Skills")
        if situational_questions:
            process_questions(situational_questions, "Situational")

        # Save to questions.json
        with open('questions.json', 'w') as f:
            json.dump({"questions": all_questions}, f, indent=4)

# if __name__ == "__main__":
#     builder = QuestionGenerator(
#         "data/resume.pdf",
#         "Associate",
#         "Boston Consulting Groups"
#     )

#     # Generate interview questions in batches
#     interview_questions = []
#     # for _ in range(2):  # Adjust the range for the number of batches you want
#     #     questions = builder.generate_interview_questions()
#     #     interview_questions.append(questions)

#     # Generate theoretical questions in batches
#     theoretical_questions = []
#     # for _ in range(2):  # Adjust the range for the number of batches you want
#     #     theory_questions = builder.generate_theoretical_interview_questions()
#     #     theoretical_questions.append(theory_questions)

#     # Generate skill questions in batches
#     skill_questions = []
#     # for _ in range(2):  # Adjust the range for the number of batches you want
#     #     skill_qs = builder.generate_skill_questions()
#     #     skill_questions.append(skill_qs)

#     # # Generate situational questions in batches
#     situational_questions = []
#     for _ in range(2):  # Adjust the range for the number of batches you want
#         situation_qs = builder.Generate_Situations()
#         situational_questions.append(situation_qs)

#     # Save all questions to questions.json
#     builder.save_questions_to_json(
#         interview_questions,
#         theoretical_questions,
#         skill_questions,
#         situational_questions[0]
#     )