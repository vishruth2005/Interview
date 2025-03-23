from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
import PyPDF2
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, Field
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from phi.tools.duckduckgo import DuckDuckGo
import io

load_dotenv()

class QuestionAnswer(BaseModel):
    question: str = Field(..., description="Interview question")
    answer: str = Field(..., description="Model answer to the question")
    category: str = Field(..., description="Category of the question (skill-based, project-based, etc.)")

class TipCategory(BaseModel):
    category: str = Field(..., description="Category of tips (e.g., Communication, Body Language)")
    points: List[str] = Field(..., description="List of tips in this category")

class InterviewTips(BaseModel):
    categories: List[TipCategory] = Field(..., description="List of tip categories")

class QuestionAnswers(BaseModel):
    qa_pairs: List[QuestionAnswer] = Field(..., description="List of question-answer pairs")

class Resource(BaseModel):
    title: str = Field(..., description="Title of the learning resource")
    url: str = Field(..., description="URL of the learning resource")

class LearningItem(BaseModel):
    name: str = Field(..., description="Name of the concept or skill to learn")
    description: str = Field(..., description="Detailed description of what this concept/skill is")
    importance: str = Field(..., description="Why this skill/concept is important for the role")
    resources: List[Resource] = Field(..., description="List of learning resources")

class ThingsToLearn(BaseModel):
    items: List[LearningItem] = Field(..., description="List of things to learn")

class CheatsheetGenerator:
    def __init__(self, resume_content, role, company):
        """Initialize with resume content, role, and company."""
        self.resume = resume_content
        self.role = role
        self.company = company
        
        # Agent for generating skill-based Q&A pairs
        self.skill_qa_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description=(
                "You are an expert in generating comprehensive interview preparation materials."
                "Your task is to create detailed question and answer pairs for skill-based interview questions."
            ),
            instructions=[
                "Generate 10 skill-based interview question and answer pairs.",
                "Each question should focus on a different technical or professional skill relevant to the role.",
                "Provide a comprehensive, well-structured answer for each question that demonstrates mastery of the skill.",
                "Ensure answers include concrete examples and demonstrate depth of knowledge.",
                "Answers should be 150-250 words in length and follow industry best practices.",
                "Format each entry with a question followed by a model answer."
            ],
            response_model=QuestionAnswers
        )
        
        # Agent for generating project-based Q&A pairs
        self.project_qa_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description=(
                "You are an expert in generating comprehensive interview preparation materials."
                "Your task is to create detailed project-based question and answer pairs based on resume content."
            ),
            instructions=[
                "Generate 10 project-based interview question and answer pairs.",
                "Analyze the resume to identify specific projects to focus questions on.",
                "Create questions that probe technical details, challenges faced, and outcomes achieved.",
                "Provide detailed answers that highlight technical skills, problem-solving abilities, and achievements.",
                "Answers should be 150-250 words and demonstrate both technical depth and business impact.",
                "Format each entry with a question followed by a model answer."
            ],
            response_model=QuestionAnswers
        )
        
        # Agent for generating theoretical Q&A pairs
        self.theoretical_qa_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description=(
                "You are an expert in generating comprehensive interview preparation materials."
                "Your task is to create detailed theoretical question and answer pairs."
            ),
            instructions=[
                "Generate 10 theoretical interview question and answer pairs.",
                "Questions should focus on fundamental concepts and principles relevant to the role and industry.",
                "Provide technically accurate answers that demonstrate deep understanding of concepts.",
                "Include relevant examples, use cases, or applications in the answers.",
                "Answers should be 150-250 words and reflect current best practices and industry standards.",
                "Format each entry with a question followed by a model answer."
            ],
            response_model=QuestionAnswers
        )
        
        # Agent for generating behavioral Q&A pairs
        self.behavioral_qa_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            tools=[DuckDuckGo()],
            description=(
                "You are an expert in generating comprehensive interview preparation materials."
                "Your task is to create detailed behavioral question and answer pairs by using the web to get the compannys policy and culture."
            ),
            show_tool_calls=True,
            instructions=[
                "You are a human resource expert with access to the internet."
                "Generate 10 behavioral interview question and answer pairs.",
                "Use the internet to find the company's policy and culture and harness that to generate behavioural and HR questions",
                "As human resource answers are subjective, instead of hard answers, provide a possible way in which the person can answer."
                "Questions should cover different aspects of professional behavior and soft skills.",
                "Use the STAR method (Situation, Task, Action, Result) for structuring answers.",
                "Answers should demonstrate emotional intelligence, teamwork, leadership, and problem-solving.",
                "Answer methodshould be 150-250 words and provide specific examples.",
                "Format each entry with a question followed by a model answer."
            ],
            response_model=QuestionAnswers
        )
        
        # Agent for generating interview presentation tips
        self.interview_tips_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            description=(
                "You are an expert in interview coaching and preparation."
                "Your task is to create comprehensive tips for self-presentation during interviews."
            ),
            instructions=[
                "Generate detailed tips for how candidates should present themselves during interviews.",
                "Include guidance on verbal communication, body language, attire, and overall demeanor.",
                "Provide specific tips for different interview stages (introduction, answering questions, asking questions, closing).",
                "Include advice on handling difficult or unexpected situations.",
                "Tips should be actionable, specific, and tailored to the company culture and role.",
                "Format the output as structured sections with clear, concise bullet points.",
                "Include at least 5 different sections with at least 5 specific tips in each."
            ],
            response_model=InterviewTips
        )

        # Agent for generating things to learn
        self.learning_generator = Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
            tools=[DuckDuckGo()],
            description=(
                "You are an expert career advisor and technical learning consultant. "
                "Your task is to analyze the gap between a candidate's current skills and the requirements "
                "of their target role, then provide detailed learning recommendations."
            ),
            instructions=[
                "Analyze the resume and identify key missing skills and concepts for the target role.",
                "For each identified gap:",
                "1. Name the skill/concept clearly",
                "2. Provide a detailed explanation of what it is",
                "3. Explain why it's important for the role",
                "4. Search the web to find high-quality learning resources",
                "5. Focus on both technical and domain-specific knowledge",
                "6. Prioritize skills that are frequently mentioned in job postings",
                "7. Include a mix of fundamental concepts and cutting-edge technologies",
                "Format each item with:",
                "- name: The skill/concept name",
                "- description: Detailed explanation",
                "- importance: Why it matters",
                "- resources: List of learning resources with titles and URLs"
            ],
            response_model=ThingsToLearn
        )

    def generate_skill_qa_pairs(self):
        """Generate skill-based question and answer pairs."""
        prompt = (
            f"You are preparing a candidate for an interview at {self.company} for the role of {self.role}. "
            f"Based on the following resume content, generate skill-based interview question and answer pairs: {self.resume}"
        )
        run: RunResponse = self.skill_qa_generator.run(prompt)
        return run.content

    def generate_project_qa_pairs(self):
        """Generate project-based question and answer pairs."""
        prompt = (
            f"You are preparing a candidate for an interview at {self.company} for the role of {self.role}. "
            f"Based on the following resume content, generate project-based interview question and answer pairs: {self.resume}"
        )
        run: RunResponse = self.project_qa_generator.run(prompt)
        return run.content

    def generate_theoretical_qa_pairs(self):
        """Generate theoretical question and answer pairs."""
        prompt = (
            f"You are preparing a candidate for an interview at {self.company} for the role of {self.role}. "
            f"Generate theoretical interview question and answer pairs relevant to this role and industry."
        )
        run: RunResponse = self.theoretical_qa_generator.run(prompt)
        return run.content

    def generate_behavioral_qa_pairs(self):
        """Generate behavioral question and answer pairs."""
        prompt = (
            f"You are preparing a candidate for an interview at {self.company}. "
            f"Based on the following resume content, generate behavioral interview question and answer pairs. make sure you just give a method of answering the question since behavioural questions are subjective. make sure it is tailored for the companys policy and culture: {self.resume}"
        )
        run: RunResponse = self.behavioral_qa_generator.run(prompt)
        return run.content

    def generate_interview_tips(self):
        """Generate interview tips organized by categories."""
        prompt = (
            f"Generate comprehensive interview tips for a {self.role} position at {self.company}. "
            "Organize the tips into distinct categories such as 'Communication', 'Body Language', "
            "'Technical Preparation', 'Company Research', etc. For each category, provide 3-5 specific, "
            "actionable tips. Format the response as a structured list of categories and their tips."
        )
        run: RunResponse = self.interview_tips_generator.run(prompt)
        return run.content

    def generate_learning_recommendations(self):
        """Generate recommendations for things to learn."""
        prompt = (
            f"You are helping a candidate prepare for a {self.role} position at {self.company}. "
            f"Based on their resume: {self.resume}\n"
            f"Identify key skills and concepts they should learn to be more competitive for this role which they are lacking and provide detailed explaination. "
            f"Consider both the specific requirements of {self.company} and industry standards for this position. "
            f"Search the web to find current, high-quality learning resources for each recommendation."
        )
        run: RunResponse = self.learning_generator.run(prompt)
        return run.content

    def generate_cheatsheet(self):
        """Generate the complete interview cheatsheet."""
        # Generate all components
        skill_qa = self.generate_skill_qa_pairs()
        project_qa = self.generate_project_qa_pairs()
        theoretical_qa = self.generate_theoretical_qa_pairs()
        behavioral_qa = self.generate_behavioral_qa_pairs()
        interview_tips = self.generate_interview_tips()
        learning_recommendations = self.generate_learning_recommendations()
        
        # Compile data for JSON storage
        cheatsheet_data = {
            "company": self.company,
            "role": self.role,
            "qa_pairs": [],
            "interview_tips": {
                "categories": []
            },
            "things_to_learn": []
        }
        
        # Process interview tips
        if hasattr(interview_tips, 'categories'):
            cheatsheet_data["interview_tips"]["categories"] = [
                {"category": cat.category, "points": cat.points}
                for cat in interview_tips.categories
            ]
        else:
            # Fallback: Try to parse the tips into a structured format
            try:
                # Assuming the response might be a string that can be parsed
                parsed_tips = []
                current_category = None
                current_points = []
                
                for line in str(interview_tips).split('\n'):
                    line = line.strip()
                    if line:
                        if not line.startswith('•') and ':' in line:
                            # If we have a previous category, save it
                            if current_category and current_points:
                                cheatsheet_data["interview_tips"]["categories"].append({
                                    "category": current_category,
                                    "points": current_points
                                })
                            # Start new category
                            current_category = line.split(':')[0].strip()
                            current_points = []
                        elif line.startswith('•') or line.startswith('-'):
                            if current_category:
                                current_points.append(line.lstrip('•- ').strip())
                
                # Add the last category if exists
                if current_category and current_points:
                    cheatsheet_data["interview_tips"]["categories"].append({
                        "category": current_category,
                        "points": current_points
                    })
            except Exception as e:
                print(f"Error parsing tips: {e}")
                # Fallback to simple format
                cheatsheet_data["interview_tips"]["categories"] = [{
                    "category": "General Tips",
                    "points": [str(interview_tips)]
                }]
        
        # Process learning recommendations
        if hasattr(learning_recommendations, 'items'):
            cheatsheet_data["things_to_learn"] = [
                {
                    "name": item.name,
                    "description": item.description,
                    "importance": item.importance,
                    "resources": [
                        {"title": resource.title, "url": resource.url}
                        for resource in item.resources
                    ]
                }
                for item in learning_recommendations.items
            ]
        
        # Process QA pairs
        # Helper function to process QA pairs
        def process_qa_pairs(qa_response, category):
            if hasattr(qa_response, 'qa_pairs'):
                pairs = qa_response.qa_pairs
            else:
                pairs = [QuestionAnswer(
                    question="Generated Question",
                    answer=qa_response,
                    category=category
                )]
            return pairs
        
        # Add all Q&A pairs to the cheatsheet
        for qa in process_qa_pairs(skill_qa, "Skill-Based"):
            cheatsheet_data["qa_pairs"].append({
                "question": qa.question,
                "answer": qa.answer,
                "category": "Skill-Based"
            })
        
        for qa in process_qa_pairs(project_qa, "Project-Based"):
            cheatsheet_data["qa_pairs"].append({
                "question": qa.question,
                "answer": qa.answer,
                "category": "Project-Based"
            })
        
        for qa in process_qa_pairs(theoretical_qa, "Theoretical"):
            cheatsheet_data["qa_pairs"].append({
                "question": qa.question,
                "answer": qa.answer,
                "category": "Theoretical"
            })
        
        for qa in process_qa_pairs(behavioral_qa, "Behavioral"):
            cheatsheet_data["qa_pairs"].append({
                "question": qa.question,
                "answer": qa.answer,
                "category": "Behavioral"
            })
        
        # Save cheatsheet to JSON file
        with open('cheatsheet.json', 'w') as f:
            json.dump(cheatsheet_data, f, indent=4)
        
        return cheatsheet_data

    def generate_pdf(self, cheatsheet_data):
        """Generate a PDF document from the cheatsheet data using reportlab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#1a237e')  # Dark blue
        ))
        
        styles.add(ParagraphStyle(
            name='SubTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#1a237e')  # Dark blue
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=15,
            textColor=colors.HexColor('#283593'),  # Indigo
            borderWidth=1,
            borderColor=colors.HexColor('#283593'),
            borderPadding=8,
            borderRadius=5
        ))
        
        styles.add(ParagraphStyle(
            name='QuestionText',
            parent=styles['Normal'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=5,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='AnswerText',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=5,
            spaceAfter=15,
            textColor=colors.HexColor('#333333'),
            leftIndent=20
        ))
        
        styles.add(ParagraphStyle(
            name='TipText',
            parent=styles['Normal'],
            fontSize=11,
            spaceBefore=2,
            spaceAfter=5,
            textColor=colors.HexColor('#333333'),
            leftIndent=20
        ))
        
        # Build the document content
        content = []
        
        # Add title page
        content.append(Paragraph(f"Interview Preparation Guide", styles['MainTitle']))
        content.append(Paragraph(f"Company: {self.company}", styles['SubTitle']))
        content.append(Paragraph(f"Role: {self.role}", styles['SubTitle']))
        content.append(Spacer(1, 30))
        
        # Add a brief introduction
        intro_text = f"""
        This guide has been specially prepared to help you prepare for your interview at {self.company} for the {self.role} position. 
        It contains key interview tips, practice questions, and model answers organized by category. Use this guide to structure 
        your preparation and boost your confidence for the interview.
        """
        content.append(Paragraph(intro_text, styles['AnswerText']))
        content.append(Spacer(1, 30))
        
        # Add interview tips section with better formatting
        content.append(Paragraph("Essential Interview Tips", styles['SectionHeader']))
        content.append(Spacer(1, 10))
        
        # Add tips from structured categories
        for category_data in cheatsheet_data["interview_tips"]["categories"]:
            # Add category header
            content.append(Paragraph(category_data["category"], styles['QuestionText']))
            content.append(Spacer(1, 5))
            
            # Add points under this category
            for point in category_data["points"]:
                content.append(Paragraph(f"• {point}", styles['TipText']))
            
            content.append(Spacer(1, 15))
        
        content.append(Spacer(1, 20))
        
        # Add Q&A sections by category with enhanced formatting
        categories = {}
        for qa in cheatsheet_data["qa_pairs"]:
            if qa["category"] not in categories:
                categories[qa["category"]] = []
            categories[qa["category"]].append(qa)
        
        for category, qa_pairs in categories.items():
            # Add page break before each new section
            content.append(Paragraph(f"{category}", styles['SectionHeader']))
            
            for i, qa in enumerate(qa_pairs, 1):
                # Format question with Q number
                question_text = f"Q{i}: {qa['question']}"
                content.append(Paragraph(question_text, styles['QuestionText']))
                
                # Format answer with proper indentation and styling
                answer_text = f"<i>Answer:</i> {qa['answer']}"
                content.append(Paragraph(answer_text, styles['AnswerText']))
                content.append(Spacer(1, 10))
        
        # Add Things to Learn section
        if "things_to_learn" in cheatsheet_data and cheatsheet_data["things_to_learn"]:
            content.append(Paragraph("Things to Learn", styles['SectionHeader']))
            content.append(Spacer(1, 10))
            
            for item in cheatsheet_data["things_to_learn"]:
                # Add skill/concept name
                content.append(Paragraph(item["name"], styles['QuestionText']))
                
                # Add description
                content.append(Paragraph("<b>What it is:</b> " + item["description"], styles['TipText']))
                
                # Add importance
                content.append(Paragraph("<b>Why it's important:</b> " + item["importance"], styles['TipText']))
                
                # Add resources
                content.append(Paragraph("<b>Learning Resources:</b>", styles['TipText']))
                for resource in item["resources"]:
                    if isinstance(resource, dict) and 'title' in resource and 'url' in resource:
                        content.append(Paragraph(f"• <link href='{resource['url']}'>{resource['title']}</link>", styles['TipText']))
                    elif isinstance(resource, str):
                        # Handle case where resource might be a simple string
                        content.append(Paragraph(f"• {resource}", styles['TipText']))
                
                content.append(Spacer(1, 15))
            
            content.append(Spacer(1, 20))
        
        # Build the PDF with a try-except block to handle any encoding issues
        try:
            doc.build(content)
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"Error building PDF: {str(e)}")
            # If there's an error, try to clean the text and rebuild
            clean_content = []
            for item in content:
                if isinstance(item, Paragraph):
                    # Clean the text by removing problematic characters
                    clean_text = item.text.encode('ascii', 'ignore').decode()
                    clean_content.append(Paragraph(clean_text, item.style))
                else:
                    clean_content.append(item)
            doc.build(clean_content)
            buffer.seek(0)
            return buffer
