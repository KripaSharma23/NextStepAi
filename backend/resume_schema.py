from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Experience(BaseModel):
    job_title: str = Field(description="Job title or position")
    company: str = Field(description="Company or organization name")
    duration: str = Field(description="Duration of employment e.g. 2020-2022")
    description: List[str] = Field(description="List of responsibilities and achievements")

class Education(BaseModel):
    degree: str = Field(description="Degree or qualification name")
    institution: str = Field(description="School or university name")
    year: str = Field(description="Year or duration e.g. 2019-2023")

    def __init__(self, **data):
        if "year" in data and data["year"] is not None:
            data["year"] = str(data["year"])
        super().__init__(**data)

        
class Project(BaseModel):
    name: str = Field(description="Project name")
    description: List[str] = Field(description="List of project details and achievements")

class Certification(BaseModel):
    name: str = Field(description="Certification name")
    issuer: str = Field(description="Issuing organization")
    year: Optional[str] = Field(default=None, description="Year obtained e.g. 2022")

    def __init__(self, **data):
        # Convert year to string if it comes as integer
        if "year" in data and data["year"] is not None:
            data["year"] = str(data["year"])
        super().__init__(**data)
        
class ResumeSchema(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: Optional[str] = Field(default=None, description="Email address if present")
    phone: Optional[str] = Field(default=None, description="Phone number if present")
    total_years_experience: float = Field(description="Total years of work experience as a number e.g. 1.5")
    skills: List[str] = Field(description="List of technical and soft skills")
    experience: List[Experience] = Field(description="List of work experiences. Must be a proper array not a string.")
    education: List[Education] = Field(description="List of education entries. Must be a proper array not a string.")
    projects: Optional[List[Project]] = Field(default=[], description="List of projects if any")
    certifications: Optional[List[Certification]] = Field(default=[], description="List of certifications or licenses if any")
    achievements: Optional[List[str]] = Field(default=[], description="List of achievements awards or honours if any")
    languages: Optional[List[str]] = Field(default=[], description="Languages known if mentioned")
    other_sections: Dict[str, List[str]] = Field(default={}, description="Anything else not captured above like hobbies volunteering etc")