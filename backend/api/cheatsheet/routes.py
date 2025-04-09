from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from Agents.document import CheatsheetGenerator
import io
import os
from fastapi.responses import StreamingResponse

router = APIRouter()

# Define a model for the cheatsheet generation request data
class CheatsheetRequest(BaseModel):
    resume_content: str
    role: str
    company: str

# Route to generate a cheatsheet and return JSON data
@router.post("/generate")
async def generate_cheatsheet(data: CheatsheetRequest = Body(...)):
    try:
        # Create the cheatsheet generator with the provided data
        cheatsheet_generator = CheatsheetGenerator(
            resume_content=data.resume_content,
            role=data.role,
            company=data.company
        )
        
        # Generate the cheatsheet data
        cheatsheet_data = cheatsheet_generator.generate_cheatsheet()
        
        return {
            "message": "Cheatsheet generated successfully",
            "data": cheatsheet_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to generate a cheatsheet PDF and return as downloadable file
@router.post("/generate-pdf")
async def generate_cheatsheet_pdf(data: CheatsheetRequest = Body(...)):
    try:
        # Create the cheatsheet generator with the provided data
        cheatsheet_generator = CheatsheetGenerator(
            resume_content=data.resume_content,
            role=data.role,
            company=data.company
        )
        
        # Generate the cheatsheet data
        cheatsheet_data = cheatsheet_generator.generate_cheatsheet()
        
        # Generate PDF from the data
        pdf_buffer = cheatsheet_generator.generate_pdf(cheatsheet_data)
        
        # Return the PDF as a downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview_cheatsheet.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
