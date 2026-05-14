from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import YOUR specific files
from parser import parse_pdf
from extractor import extract_resume

app = FastAPI(title="NextStep AI Backend")

# 1. CORS Configuration
# This allows your React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "online", "message": "NextStep AI API is running"}

@app.post("/upload_resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_role: str = Form(...)
):
    try:
        # Step 1: Read the file bytes
        file_content = await file.read()
        
        # Step 2: Use your parser.py logic to get text
        raw_text = parse_pdf(file_content)
        
        if not raw_text:
            return JSONResponse(status_code=400, content={"error": "Could not extract text from PDF"})

        # Step 3: Use your extractor.py logic to get AI analysis
        # Note: Ensure your 'extract_resume' function in extractor.py 
        # is updated to accept both (raw_text, job_role)
        analysis = extract_resume(raw_text, job_role)

        # Step 4: Return the final structured data
        return {
            "success": True,
            "filename": file.filename,
            "job_role": job_role,
            "data": analysis # This will be your ResumeSchema JSON
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Future Feature: Resume Generation
@app.post("/generate_resume")
async def generate_resume(data: dict):
    # This is where we will add the docx generation logic later
    return {"message": "Resume generation feature coming soon!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
