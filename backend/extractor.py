import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from resume_schema import ResumeSchema
from datetime import datetime
import json

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),    
    model="llama-3.3-70b-versatile",
    temperature=0
)

structured_llm = llm.with_structured_output(ResumeSchema, method="json_mode")

def repair_experience(experience_list: list) -> list:
    """
    Fixes common field name mistakes the AI makes in experience section.
    """
    repaired = []
    for exp in experience_list:
        fixed = {}

        # Fix job_title — AI sometimes uses position, role, title
        fixed["job_title"] = (
            exp.get("job_title") or
            exp.get("position") or
            exp.get("role") or
            exp.get("title") or
            "Unknown"
        )

        # Fix company — AI sometimes uses organization, employer
        fixed["company"] = (
            exp.get("company") or
            exp.get("organization") or
            exp.get("employer") or
            "Unknown"
        )

        # Fix duration — AI sometimes uses start_date + end_date separately
        if exp.get("duration"):
            fixed["duration"] = exp["duration"]
        elif exp.get("start_date") and exp.get("end_date"):
            fixed["duration"] = f"{exp['start_date']} - {exp['end_date']}"
        elif exp.get("start_date"):
            fixed["duration"] = f"{exp['start_date']} - Present"
        else:
            fixed["duration"] = "Unknown"

        # Fix description — AI sometimes uses responsibilities, bullets
        fixed["description"] = (
            exp.get("description") or
            exp.get("responsibilities") or
            exp.get("bullets") or
            exp.get("duties") or
            []
        )

        repaired.append(fixed)
    return repaired


def repair_education(education_list: list) -> list:
    """
    Fixes common field name mistakes the AI makes in education section.
    """
    repaired = []
    for edu in education_list:
        fixed = {}

        # Fix degree
        fixed["degree"] = (
            edu.get("degree") or
            edu.get("qualification") or
            edu.get("program") or
            "Unknown"
        )

        # Fix institution
        fixed["institution"] = (
            edu.get("institution") or
            edu.get("university") or
            edu.get("school") or
            edu.get("college") or
            "Unknown"
        )

        # Fix year
        if edu.get("year"):
            fixed["year"] = edu["year"]
        elif edu.get("start_date") and edu.get("end_date"):
            fixed["year"] = f"{edu['start_date']} - {edu['end_date']}"
        elif edu.get("graduation_year"):
            fixed["year"] = str(edu["graduation_year"])
        else:
            fixed["year"] = "Unknown"

        repaired.append(fixed)
    return repaired


def extract_resume(raw_text: str, job_role: str) -> ResumeSchema:
    today = datetime.now().strftime("%B %Y")

    prompt = f"""
    You are an expert resume parser. Extract information from the resume below
    and return ONLY a valid json object with no text before or after.

    Today's Date: {today}
    Target Job Role: {job_role}

    INSTRUCTIONS:
    1. NAME: Extract the name exactly as it appears.
    2. MATH: If a job says 'Present' or 'Current', calculate years from 
       start date until {today}. Return as float e.g. 1.5
    3. PROJECTS: Keep name and copy description bullet points exactly.
    4. DATA INTEGRITY: experience and education MUST be proper json arrays.
    5. MISSING FIELDS: If email or phone not found return null.
    6. CERTIFICATIONS: Extract all certifications with name, issuer and year.
    7. ACHIEVEMENTS: Extract all awards and achievements as list of strings.
    8. LANGUAGES: Extract all languages as list of strings.
    9. OTHER SECTIONS: Anything else goes in other_sections dictionary.

    RESUME TEXT:
    {raw_text}

    Return ONLY a valid json object following this exact structure:
    {{
        "name": "full name",
        "email": "email or null",
        "phone": "phone or null",
        "total_years_experience": 0.0,
        "skills": ["skill1", "skill2"],
        "experience": [
            {{
                "job_title": "title",
                "company": "company",
                "duration": "2020-2022",
                "description": ["bullet1", "bullet2"]
            }}
        ],
        "education": [
            {{
                "degree": "degree name",
                "institution": "school name",
                "year": "2019-2023"
            }}
        ],
        "projects": [
            {{
                "name": "project name",
                "description": ["bullet1", "bullet2"]
            }}
        ],
        "certifications": [
            {{
                "name": "cert name",
                "issuer": "issuer",
                "year": "year"
            }}
        ],
        "achievements": ["achievement1"],
        "languages": ["language1"],
        "other_sections": {{}}
    }}
    """

    try:
        # Try normal extraction first
        result = structured_llm.invoke(prompt)
        return result

    except Exception as e:
        # If it fails, extract raw JSON and repair it
        print(f"First attempt failed: {e}")
        print("Attempting JSON repair...")

        # Get raw response from LLM without structured output
        raw_llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0
        )

        raw_response = raw_llm.invoke(prompt)
        raw_text_response = raw_response.content

        # Extract JSON from response
        start = raw_text_response.find("{")
        end = raw_text_response.rfind("}") + 1
        json_str = raw_text_response[start:end]
        data = json.loads(json_str)

        # Repair field names
        if "experience" in data:
            data["experience"] = repair_experience(data["experience"])
        if "education" in data:
            data["education"] = repair_education(data["education"])

        # Fix missing total_years_experience
        if "total_years_experience" not in data:
            data["total_years_experience"] = 0.0

        # Fix missing skills
        if "skills" not in data:
            data["skills"] = []

        # Fix missing optional fields
        if "projects" not in data:
            data["projects"] = []
        if "certifications" not in data:
            data["certifications"] = []
        if "achievements" not in data:
            data["achievements"] = []
        if "languages" not in data:
            data["languages"] = []

        # Fix other_sections — every value must be a list not a string
        if "other_sections" in data:
            fixed_sections = {}
            for key, value in data["other_sections"].items():
                if isinstance(value, str):
                    fixed_sections[key] = [value]
                elif isinstance(value, list):
                    fixed_sections[key] = value
                else:
                    fixed_sections[key] = [str(value)]
            data["other_sections"] = fixed_sections
        else:
            data["other_sections"] = {}

        # Build ResumeSchema from repaired data
        return ResumeSchema(**data)