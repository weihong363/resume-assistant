from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    start_date: date
    end_date: Optional[date]
    description: Optional[str]

class Experience(BaseModel):
    company: str
    position: str
    start_date: date
    end_date: Optional[date]
    description: Optional[str]
    skills_used: List[str]

class Project(BaseModel):
    name: str
    description: str
    start_date: date
    end_date: Optional[date]
    url: Optional[HttpUrl]
    technologies: List[str]

class Skill(BaseModel):
    name: str
    level: str  # e.g. Beginner, Intermediate, Expert
    years_of_experience: Optional[int]

class Language(BaseModel):
    name: str
    proficiency: str  # e.g. Native, Fluent, Intermediate

class Resume(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    linkedin: Optional[HttpUrl]
    github: Optional[HttpUrl]
    summary: str
    education: List[Education]
    experience: List[Experience]
    projects: Optional[List[Project]]
    skills: List[Skill]
    languages: Optional[List[Language]]
    certifications: Optional[List[str]]