from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# --- Output Structure ---
class RewrittenExperience(BaseModel):
    job_title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    duration: str = Field(description="Duration of employment")
    improved_bullets: List[str] = Field(description="Rewritten bullet points with metrics and keywords")

class RewrittenResume(BaseModel):
    candidate_name: str = Field(description="Full name of candidate")
    improved_summary: str = Field(description="A powerful 3 line professional summary tailored to the job")
    improved_skills: List[str] = Field(description="Updated skills list with missing keywords added")
    improved_experience: List[RewrittenExperience] = Field(description="Each job with rewritten bullet points")
    improvement_notes: List[str] = Field(description="List of what was changed and why")

# --- Model ---
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.7
)

structured_llm = llm.with_structured_output(RewrittenResume, method="json_mode")

# --- Prompt ---
REWRITER_PROMPT = """
You are an expert resume writer with 10 years of experience.
You specialize in rewriting resumes to pass ATS systems and 
impress human recruiters.

Candidate Name: {name}
Target Job Role: {job_role}
Current Skills: {skills}
Missing Keywords from JD: {missing_keywords}

Original Experience:
{experience}

Job Description:
{job_description}

Your job is to rewrite this resume to be ATS optimized and impactful.

REWRITING RULES:
1. KEYWORDS: Naturally inject missing keywords into bullet points
2. METRICS: Every bullet point must have a number or percentage
   If original has no metric, add a realistic estimated one
3. ACTION VERBS: Start every bullet with a strong action verb
   Examples: Spearheaded, Orchestrated, Achieved, Delivered, Optimized
4. SUMMARY: Write a powerful 3 line summary targeting the job role
5. SKILLS: Add missing keywords to skills list naturally
6. DO NOT lie or fabricate experience — only improve the language

Return a json object with EXACTLY these field names:
{{
    "candidate_name": "full name of candidate",
    "improved_summary": "powerful 3 line professional summary",
    "improved_skills": ["skill1", "skill2", "skill3"],
    "improved_experience": [
        {{
            "job_title": "job title",
            "company": "company name",
            "duration": "duration",
            "improved_bullets": ["bullet1", "bullet2", "bullet3"]
        }}
    ],
    "improvement_notes": ["note1", "note2", "note3"]
}}

IMPORTANT: improved_skills MUST be a JSON array of strings NOT a comma separated string.
Make it sound human, powerful and professional.
"""

prompt = ChatPromptTemplate.from_template(REWRITER_PROMPT)
rewriter_chain = prompt | structured_llm

def run_rewriter(resume_data: dict, job_description: str, missing_keywords: List[str]) -> RewrittenResume:
    """
    Takes extracted resume data, job description and missing keywords.
    Returns a fully rewritten improved resume.
    """
    # Format experience as readable text
    experience_text = ""
    for exp in resume_data.get("experience", []):
        experience_text += f"\n{exp['job_title']} at {exp['company']} ({exp['duration']})\n"
        for bullet in exp.get("description", []):
            experience_text += f"  {bullet}\n"

    result = rewriter_chain.invoke({
        "name": resume_data.get("name", "Unknown"),
        "job_role": resume_data.get("job_role", "Not specified"),
        "skills": ", ".join(resume_data.get("skills", [])),
        "missing_keywords": ", ".join(missing_keywords),
        "experience": experience_text,
        "job_description": job_description
    })

    return result