from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# --- Output Structure ---
class ATSResult(BaseModel):
    ats_score: int = Field(description="Final ATS score out of 100")
    keyword_score: int = Field(description="Keyword match score out of 40")
    title_score: int = Field(description="Job title match score out of 20")
    experience_score: int = Field(description="Years of experience score out of 20")
    education_score: int = Field(description="Education match score out of 20")
    ats_decision: str = Field(description="ATS decision: Auto Rejected, Maybe, Good Candidate, or Priority")
    verdict: str = Field(description="One brutal honest line a real recruiter would think")
    rejection_reasons: List[str] = Field(description="Top 3 reasons this resume gets rejected")
    missing_keywords: List[str] = Field(description="Keywords from JD not found in resume")
    matched_keywords: List[str] = Field(description="Keywords from JD found in resume")

# --- Model ---
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0,
    model_kwargs={"seed": 42}
)

structured_llm = llm.with_structured_output(ATSResult, method="json_mode")

# --- Prompt ---
CYNICAL_RECRUITER_PROMPT = """
You are an ATS system combined with a cynical recruiter with 15 years experience.
First detect the job type, then score accordingly.

Candidate Name: {name}
Target Job Role: {job_role}
Years of Experience: {years_exp}
Current Skills: {skills}

Resume Experience:
{experience}

Education:
{education}

Job Description:
{job_description}

STEP 1 - DETECT JOB TYPE:
Look at the job description and classify as ONE of:
- CORPORATE: Business, tech, marketing, finance roles
- ACADEMIC: College applications, university, research, teaching
- ENTRY_LEVEL: First job, internship, junior roles
- SENIOR: Manager, director, lead, senior roles

STEP 2 - APPLY CORRECT SCORING WEIGHTS:

If CORPORATE:
- Keywords (40pts) + Job Title Match (20pts) + Experience (20pts) + Education (20pts)

If ACADEMIC:
- Keywords (40pts) + Academic Achievement (30pts) + Community/Volunteer (30pts)
- Job title is IRRELEVANT for academic applications

If ENTRY_LEVEL:
- Keywords (40pts) + Transferable Skills (20pts) + Education (30pts) + Any Experience (10pts)
- Job title is NOT important for entry level

If SENIOR:
- Keywords (40pts) + Job Title Match (25pts) + Years of Experience (35pts)
- Education is LESS important for senior roles

STEP 3 - CALCULATE SCORE:
Add up all components based on detected job type
Maximum score is always 100

STEP 4 - APPLY ATS DECISION:
- Score 0-39   = "Auto Rejected"
- Score 40-60  = "Maybe"
- Score 61-80  = "Good Candidate"
- Score 81-100 = "Priority"

Return a json object with EXACTLY these field names:
{{
    "ats_score": (total score out of 100),
    "keyword_score": (keyword component score),
    "title_score": (title or achievement component score),
    "experience_score": (experience component score),
    "education_score": (education component score),
    "ats_decision": (one of: Auto Rejected, Maybe, Good Candidate, Priority),
    "verdict": (one brutal honest line a real recruiter would think),
    "rejection_reasons": (list of top 3 specific reasons this resume gets rejected),
    "missing_keywords": (list of keywords from JD NOT found in resume),
    "matched_keywords": (list of keywords from JD FOUND in resume)
}}

Be brutally honest. Be specific. No sugarcoating.
"""
prompt = ChatPromptTemplate.from_template(CYNICAL_RECRUITER_PROMPT)
ats_chain = prompt | structured_llm

def run_ats_audit(resume_data: dict, job_description: str) -> ATSResult:
    """
    Takes extracted resume data and job description.
    Returns realistic ATS audit result.
    """
    # Format experience
    experience_text = ""
    for exp in resume_data.get("experience", []):
        experience_text += f"\n{exp['job_title']} at {exp['company']} ({exp['duration']})\n"
        for bullet in exp.get("description", []):
            experience_text += f"  {bullet}\n"

    # Format education
    education_text = ""
    for edu in resume_data.get("education", []):
        education_text += f"{edu['degree']} at {edu['institution']} ({edu['year']})\n"

    result = ats_chain.invoke({
        "name": resume_data.get("name", "Unknown"),
        "job_role": resume_data.get("job_role", "Not specified"),
        "years_exp": resume_data.get("total_years_experience", 0),
        "skills": ", ".join(resume_data.get("skills", [])),
        "experience": experience_text,
        "education": education_text,
        "job_description": job_description
    })

    return result