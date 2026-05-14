from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# --- Output Structure ---
class SkillGap(BaseModel):
    skill_name: str = Field(description="Name of the missing skill")
    priority: str = Field(description="Priority level: High, Medium or Low")
    reason: str = Field(description="Why this skill is important for the job role")
    how_to_learn: List[str] = Field(description="List of resources or ways to learn this skill")

class GapAnalysisResult(BaseModel):
    overall_match_percentage: int = Field(description="How well candidate matches the job as a percentage 0-100")
    strong_areas: List[str] = Field(description="Skills and experiences candidate already has that match the job")
    skill_gaps: List[SkillGap] = Field(description="List of skills missing ranked by priority")
    quick_wins: List[str] = Field(description="Things candidate can fix or add to resume quickly without learning new skills")
    estimated_ready_time: str = Field(description="Estimated time needed to be fully ready for this role e.g. 3 months")

# --- Model ---
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

structured_llm = llm.with_structured_output(GapAnalysisResult, method="json_mode")

# --- Prompt ---
GAP_ANALYST_PROMPT = """
You are an expert career coach and skill gap analyst.
Your job is to compare a candidate's current skills against 
what a job requires and give them a clear honest roadmap.

Candidate Name: {name}
Target Job Role: {job_role}
Years of Experience: {years_exp}
Current Skills: {skills}
Education: {education}

Resume Experience:
{experience}

Job Description:
{job_description}

Analyze the gap between what the candidate has and what the job needs.

Return a json object with EXACTLY these field names:
{{
    "overall_match_percentage": (number 0-100 showing how well candidate matches job),
    "strong_areas": (list of skills and experiences candidate already has that match),
    "skill_gaps": (list of objects each with skill_name, priority, reason, how_to_learn),
    "quick_wins": (list of things candidate can fix quickly without learning new skills),
    "estimated_ready_time": (estimated time to be ready for this role e.g. 3 months)
}}

For each skill gap:
- priority must be exactly "High", "Medium" or "Low"
- how_to_learn must be a list of 2-3 specific resources like course names or websites
- reason must explain WHY this skill matters for the specific job role

Be specific. Be encouraging but honest.
"""

prompt = ChatPromptTemplate.from_template(GAP_ANALYST_PROMPT)
gap_chain = prompt | structured_llm

def run_gap_analysis(resume_data: dict, job_description: str) -> GapAnalysisResult:
    """
    Takes extracted resume data and job description.
    Returns skill gap analysis result.
    """
    # Format experience as readable text
    experience_text = ""
    for exp in resume_data.get("experience", []):
        experience_text += f"\n{exp['job_title']} at {exp['company']} ({exp['duration']})\n"
        for bullet in exp.get("description", []):
            experience_text += f"  {bullet}\n"

    # Format education as readable text
    education_text = ""
    for edu in resume_data.get("education", []):
        education_text += f"{edu['degree']} at {edu['institution']} ({edu['year']})\n"

    result = gap_chain.invoke({
        "name": resume_data.get("name", "Unknown"),
        "job_role": resume_data.get("job_role", "Not specified"),
        "years_exp": resume_data.get("total_years_experience", 0),
        "skills": ", ".join(resume_data.get("skills", [])),
        "education": education_text,
        "experience": experience_text,
        "job_description": job_description
    })

    return result