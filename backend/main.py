from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.interview.routes import router as interview_router
from api.resume.routes import router as resume_router


app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello Interview Bot!"}

app.include_router(interview_router, prefix='/interview', tags=['interview'])
app.include_router(resume_router, prefix='/build_resume', tags=['build_resume'])