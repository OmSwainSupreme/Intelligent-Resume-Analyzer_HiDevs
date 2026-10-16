"""
Data models for the Smart Hiring Assistant.
Defines the structure for resumes, jobs, and match results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class ContactInfo:
    """Contact information for a candidate."""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass
class WorkExperience:
    """Work experience entry."""
    title: str = ""
    company: str = ""
    start_date: str = ""  # Could be improved with datetime objects
    end_date: str = ""
    description: str = ""
    skills_used: List[str] = field(default_factory=list)


@dataclass
class Education:
    """Education entry."""
    degree: str = ""
    institution: str = ""
    graduation_year: str = ""
    gpa: str = ""
    relevant_coursework: List[str] = field(default_factory=list)


@dataclass
class Resume:
    """Represents a parsed resume."""
    # Basic information
    name: str = ""
    contact_info: ContactInfo = field(default_factory=ContactInfo)

    # Professional details
    skills: List[str] = field(default_factory=list)
    work_experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    # Metadata
    raw_text: str = ""
    parsed_at: datetime = field(default_factory=datetime.now)
    file_source: str = ""  # Path to the original file

    def get_years_of_experience(self) -> float:
        """Calculate total years of work experience."""
        # Simple implementation - could be enhanced
        total_months = 0
        for exp in self.work_experience:
            # This is a simplified calculation
            # In a real app, we'd parse dates properly
            total_months += 12  # Assume 1 year per experience for now
        return total_months / 12.0 if total_months > 0 else 0.0

    def has_skill(self, skill: str) -> bool:
        """Check if resume contains a specific skill (case-insensitive)."""
        skill_lower = skill.lower()
        return any(skill_lower in s.lower() for s in self.skills)


@dataclass
class Job:
    """Represents a job posting."""
    title: str = ""
    company: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    experience_level: str = ""  # entry, mid, senior, etc.
    min_years_experience: float = 0.0
    description: str = ""
    location: str = ""
    employment_type: str = ""  # full-time, part-time, contract, etc.

    def get_all_skills(self) -> List[str]:
        """Get combined list of required and preferred skills."""
        return self.required_skills + self.preferred_skills


@dataclass
class SkillMatch:
    """Result of matching a single skill."""
    skill: str
    required: bool  # True if required skill, False if preferred
    matched: bool
    confidence: float = 1.0  # 0.0 to 1.0
    notes: str = ""


@dataclass
class MatchResult:
    """Result of matching a resume to a job."""
    resume_id: str
    job_id: str
    overall_score: float  # 0.0 to 100.0
    skill_score: float = 0.0
    experience_score: float = 0.0

    # Detailed breakdown
    skill_matches: List[SkillMatch] = field(default_factory=list)
    matched_required_skills: List[str] = field(default_factory=list)
    missing_required_skills: List[str] = field(default_factory=list)
    matched_preferred_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)

    # Explanation
    explanation: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    matched_at: datetime = field(default_factory=datetime.now)

    def is_strong_match(self, threshold: float = 80.0) -> bool:
        """Determine if this is a strong match based on threshold."""
        return self.overall_score >= threshold

    def is_medium_match(self, low_threshold: float = 60.0, high_threshold: float = 80.0) -> bool:
        """Determine if this is a medium match."""
        return low_threshold <= self.overall_score < high_threshold

    def is_weak_match(self, threshold: float = 60.0) -> bool:
        """Determine if this is a weak match."""
        return self.overall_score < threshold