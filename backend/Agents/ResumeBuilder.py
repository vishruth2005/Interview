import asyncio
from phi.agent import Agent, RunResponse
from phi.model.google import Gemini
from dotenv import load_dotenv
import os
from typing import Dict, Optional
from phi.utils.log import logger
from github import Github, GithubException, Auth
import re
from proxycurl.asyncio import Proxycurl
from pydantic import BaseModel, Field
from typing import List
import warnings
import json

load_dotenv()
warnings.filterwarnings('ignore')

class Projects(BaseModel):
    name: str = Field(..., description="Name of the project.")
    content1: str = Field(..., description="First point of the project.")
    content2: str = Field(..., description="Second point of the project.")
    content3: str = Field(..., description="Third point of the project.")

class Skills(BaseModel):
    type: str = Field(..., description="Type of the skill.")
    skills: List[str] = Field(..., description="Skills of that type")

class Experience(BaseModel):
    company_details: str = Field(..., description="The name of the company along with its location.")
    contribution_1: str = Field(..., description="A brief description of a key responsibility or achievement in this role.")
    contribution_2: str = Field(..., description="Another important responsibility or achievement that highlights your contributions.")
    contribution_3: str = Field(..., description="A third significant responsibility or accomplishment that showcases your skills.")

class Education(BaseModel):
    degree_title: str = Field(..., description="The official title of the degree obtained.")
    start_date: str = Field(..., description="The date when the degree program commenced.")
    end_date: str = Field(..., description="The date when the degree program concluded. Use 'present' if you are still enrolled.")
    institution_name: str = Field(..., description="The name of the educational institution where the degree was earned.")

class LinkedInProfile(BaseModel):
    full_name: str = Field(..., description="The full name of the individual as it should appear on their LinkedIn profile.")
    education: List[Education] = Field(..., description="A list detailing the educational qualifications attained by the individual.")
    experience: List[Experience] = Field(..., description="A list summarizing the professional experiences and roles held by the individual.")

def to_json(data_string):  
    json_data = json.loads(f'[{data_string.replace("}\n{", "}, {")}]')
    return json.dumps(json_data, indent=4)

class ResumeBuilder:
    
    def __init__(self, repos, linkedin_profile_url, role):
        self.access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        self.linkedin_profile_url = linkedin_profile_url
        self.role = role
        self.agent = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")), markdown=True)
        self.projectagent = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")), response_model = Projects)
        self.linkinagent = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")), response_model = LinkedInProfile)
        self.skillagent = Agent(model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")), response_model = Skills)
        self.github_client = self.authenticate()
        self.repo_list = repos
        self.parsed_readmes = {}  # Store parsed READMEs in the class
        # self.profile = {'name': 'Vishruth Srivatsa', 'occupation': "Executive member at Web Enthusiasts'\u200b Club NITK", 'experiences': [{'company': "Web Enthusiasts'\u200b Club NITK", 'title': 'Executive member', 'description': "-Participated in Unfold'24 hackathon organized by Devfolio and built a project called JusticeChain\n-Participated in EthIndia'2k24 and won the pool prize of CDP for building a project called AIgentX\n-Participated in Hackverse 5.0 and won the Fintech track for building a project called Viresco\n-Took a research paper discussion on Combating Adversial Attacks using Robust Word Recognition Model"}, {'company': 'IEEE', 'title': 'Executive member', 'description': '- Organised an event called BlackBox and held a talk on machine learning for first years.'}, {'company': 'Genesis NITK', 'title': 'Executive member', 'description': '- Participated in several college level dance competitions\n- Won second place in college level group dance competition as part of Genesis crew'}], 'education': [{'start': '1 8 2023', 'end': '30 4 2027', 'field_of_study': 'Computational And Data Science', 'degree_name': 'Bachelor of Technology - BTech', 'school': 'National Institute of Technology Karnataka'}, {'start': '1 6 2021', 'end': '30 4 2023', 'field_of_study': 'Science', 'degree_name': 'Higher Secondary Education', 'school': 'BASE PU College'}]}

    def fetch_linkedin_profile(self):
        async def get_filtered_profile_data(profile_url):
            proxycurl = Proxycurl(os.getenv("PROXYCURL_API_KEY"))
            profile_data = await proxycurl.linkedin.person.get(linkedin_profile_url=profile_url)

            # Filter the relevant data
            filtered_data = {
                "name": profile_data['full_name'],
                "occupation": profile_data['occupation'],
                "experiences": [
                    {
                        "company": exp['company'],
                        "title": exp['title'],
                        "description": exp['description']
                    } for exp in profile_data['experiences'] if exp.get('description')
                ],
                "education": [
                    {
                        "start": str(edu['starts_at']['day']) + '-' + str(edu['starts_at']['month']) + '-' + str(edu['starts_at']['year']),
                        "end": str(edu['ends_at']['day']) + '-' + str(edu['ends_at']['month']) + '-' + str(edu['ends_at']['year']),
                        "field_of_study": edu['field_of_study'],
                        "degree_name": edu['degree_name'],
                        "school": edu["school"]
                    } for edu in profile_data['education']
                ]
            }
            return filtered_data

        self.profile = asyncio.run(get_filtered_profile_data(self.linkedin_profile_url))

    def authenticate(self) -> Github:
        """Authenticate with GitHub using the provided access token."""
        if not self.access_token:
            raise ValueError("GitHub access token is required")
        
        auth = Auth.Token(self.access_token)
        logger.debug("Authenticating with GitHub")
        return Github(auth=auth)

    def get_readme_of_repositories(self) -> Dict[str, Optional[str]]:
        """Get the README file content for specified repositories."""
        logger.debug("Getting README files for specified repositories")
        readme_contents: Dict[str, Optional[str]] = {}
        
        for repo_name in self.repo_list:
            try:
                repo = self.github_client.get_repo(repo_name)
                readme = repo.get_readme()
                readme_contents[repo.full_name] = readme.decoded_content.decode('utf-8')
                logger.debug(f"Retrieved README for {repo.full_name}")
            except GithubException as e:
                if e.status == 404:
                    logger.warning(f"No README found for {repo_name}")
                    readme_contents[repo_name] = None
                else:
                    logger.error(f"Error retrieving README for {repo_name}: {e}")
                    readme_contents[repo_name] = None

        return readme_contents

    def parse_readmes(self):
        """Parse and clean up the README content for repositories."""
        logger.debug("Parsing README files")
        readme_contents = self.get_readme_of_repositories()
        
        self.parsed_readmes = {
            repo_name: self.parse_readme(content) if content else "No README available"
            for repo_name, content in readme_contents.items()
        }
        logger.debug("Finished parsing README files")

    def parse_readme(self, input_text: str) -> str:
        """Clean up and parse the README content."""
        text_without_html = re.sub(r"<[^>]*>", "", input_text)
        text_without_links = re.sub(r"\[.*?\]\(.*?\)|<.*?>", "", text_without_html)
        text_without_icons = re.sub(r"[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\U0001F1E6-\U0001F1FF]+", "", text_without_links)
        cleaned_text = re.sub(r"[^\w\s.,]", "", text_without_icons)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)
        return cleaned_text.strip()

    def build_projects(self) -> str:
        """Summarise the specified projects and build the Project section of a Resume."""
        logger.info("Building resume by summarizing project READMEs and LinkedIn data")

        if not self.parsed_readmes:
            logger.error("Parsed READMEs are not available. Ensure parse_readmes() is called first.")
            return "Error: Parsed READMEs are missing."

        formatted_output = "Project Repository Data:\n"
        for repo_name, content in self.parsed_readmes.items():
            project_name = "/".join(repo_name.split("/")[1:])
            formatted_output += f"\nProject: {project_name}\n"
            formatted_output += f"Content:\n{content}\n"

        keyword_extraction_prompt = (
            "You are an AI expert specializing in text analysis. Your task is to analyze the given project overviews "
            "and extract the most important technical keywords and key sections relevant to each project. "
            f"The projects and their overviews are:\n\n{formatted_output}\n\n"
            "Output the extracted keywords and sections for each project in the following format:\n"
            "ProjectName:\n"
            "Keywords: [list of keywords]\n"
            "Key Sections: [summary of important sections]"
        )

        keyword_extraction_run = self.agent.run(keyword_extraction_prompt)
        extracted_keywords_and_sections = keyword_extraction_run.content

        resume_building_prompt = (
            "You are a professional project summarizer specializing in creating impactful and concise highlights for resumes. "
            "Your task is to use the provided keywords and key sections for each project to build a summary of technical accomplishments, "
            "core contributions, and notable results. Focus on showcasing expertise and measurable achievements, and avoid soft skills. "
            f"The extracted keywords and sections are:\n\n{extracted_keywords_and_sections}\n\n"
            "Format the summary for all projects under the following heading:\n"
            "## Projects:\n"
            "1. **ProjectName 1:**\n"
            "   - **[First key point]**\n"
            "   - **[Second key point]**\n"
            "   - **[Third key point]**\n\n"
            "2. **ProjectName 2:**\n"
            "   - **[First key point]**\n"
            "   - **[Second key point]**\n"
            "   - **[Third key point]**\n\n"
            "3. **ProjectName 3:**\n"
            "   - **[First key point]**\n"
            "   - **[Second key point]**\n"
            "   - **[Third key point]**\n\n"
            "Do not include any extra text or explanations; the output should be in markdown format."
        )

        resume_building_run = self.agent.run(resume_building_prompt)

        logger.info("Resume building complete")
        return resume_building_run.content

    def build_skills(self) -> str:
        """Extract relevant skills from parsed READMEs and format them for the specific role."""
        logger.info("Building skills section from parsed project READMEs")

        if not self.parsed_readmes:
            logger.error("Parsed READMEs are not available. Ensure parse_readmes() is called first.")
            return "Error: Parsed READMEs are missing."

        formatted_output = "Parsed Project Repository Data:\n"
        for repo_name, content in self.parsed_readmes.items():
            formatted_output += f"\nProject: {repo_name}\nContent:\n{content}\n"

        skill_extraction_prompt = (
            f"You are an expert AI specializing in skill extraction for resumes. Your task is to analyze the provided project data "
            f"and extract the most relevant skills tailored to the role of a {self.role}. "
            "Format the skills section in a way that is most appropriate and impactful for the given role. "
            "Limit the output to a maximum of three categories of skills, with each category containing up to five skills only. "
            "Do not include any extra text or explanations, only output the formatted skills in markdown format.\n\n"
            "The format of the output should be relevant to the given role. For example:\n\n"
            "- **For technical roles like Software Engineer:** \n"
            "  - **Programming Languages:** Python, Java, C++, JavaScript, SQL\n"
            "  - **Frameworks:** Django, Flask, React, Angular, Spring\n"
            "  - **Tools:** Docker, Kubernetes, Git, Jenkins, VS Code\n\n"
            "- **For consulting roles:**\n"
            "  - **Analytical Skills:** Data Analysis, Problem Solving, Market Research, Business Modeling, Risk Assessment\n"
            "  - **Industry Expertise:** Healthcare, Finance, Technology\n"
            "  - **Tools & Techniques:** Tableau, Excel, PowerPoint, SQL, SAP\n\n"
            f"The project data is:\n{formatted_output}\n\n"
            f"Based on the role '{self.role}', format the skills section appropriately and only provide the skills in markdown format."
        )

        skill_extraction_run = self.agent.run(skill_extraction_prompt)
        return skill_extraction_run.content
    
    def use_linked_in(self):
        prompt = (
            f"This is the LinkedIn information in JSON format: {self.profile}."
            "\n\nPlease structure the information in the following detailed format:"
            
            "## [Insert Full Name]\n\n"
            
            "## Experiences:\n"
            "1. **Experience 1 Title** (Company Name, Location):\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            
            "2. **Experience 2 Title** (Company Name, Location):\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            
            "3. **Experience 3 Title** (Company Name, Location):\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            "   - [Detail about responsibility or achievement]\n"
            
            "## Education:\n"
            "1. **Degree Title:** Bachelor of Technology in Computer Science (or other degree)\n"
            "   - **Institution Name:** [Insert Institution Name]\n"
            "   - **Start Date:** [Format: 1st January 1998]\n"
            "   - **End Date:** [Format: 31st December 2002]\n"
            
            "2. **Degree Title:** Master of Science in Data Science (or other degree)\n"
            "   - **Institution Name:** [Insert Institution Name]\n"
            "   - **Start Date:** [Format: 1st January 2004]\n"
            "   - **End Date:** [Format: 31st December 2006]\n"

            "\n\nNote: Ensure that all sections are filled out completely and accurately. Convert degree titles to their full forms (e.g., 'B.Tech in CS' becomes 'Bachelor of Technology in Computer Science'). Format dates as '1st January 1998' for clarity and aesthetic appeal."
        )

        run: RunResponse = self.agent.run(prompt)     
        return run.content
    
    def build(self):
        self.parse_readmes()
        resume_result = self.build_projects()
        skills_result = self.build_skills()
        self.fetch_linkedin_profile()
        linked_in = self.use_linked_in()

        return resume_result, skills_result, linked_in
        

# def main():
#     linkedin_profile_url = 'https://www.linkedin.com/in/vishruth-srivatsa-b56638286/'
#     role_input = 'Data Scientist'
#     resume_builder = ResumeBuilder(['marcdhi/Lexify', 'suyash101101/AIgentX'], linkedin_profile_url, role_input)
#     resume_builder.build()

# if __name__ == "__main__":
#     main()