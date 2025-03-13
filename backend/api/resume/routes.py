from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from Agents.ResumeBuilder import ResumeBuilder

router = APIRouter()

# Define a model for the form data
class ResumeFormData(BaseModel):
    linkedin_url: str
    role: str
    repos: list[str]

# Route to handle form submission and generate the resume
@router.post("/generate-resume")
async def generate_resume(data: ResumeFormData = Body(...)):
    # if not (data.linkedin_url and data.role and data.repos):
    #     raise HTTPException(status_code=400, detail="Please fill in all fields")
    
    resume_builder = ResumeBuilder(data.repos, data.linkedin_url, data.role)
    resume_result, skills_result, linked_in = resume_builder.build()
    
    # Return the results as JSON
    return {
        "resume": resume_result,
        "skills": skills_result,
        "linkedin": linked_in
    }
