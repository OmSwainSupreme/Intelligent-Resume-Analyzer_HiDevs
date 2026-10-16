"""
Job matching algorithm for the Smart Hiring Assistant.
Calculates match scores between resumes and job postings with explainable scoring.
"""

from typing import List, Dict, Tuple, Optional
from models import Resume, Job, MatchResult, SkillMatch
import logging
import re
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobMatcher:
    """Matches resumes to job postings and calculates explainable match scores."""

    def __init__(self,
                 skill_weight: float = 0.6,
                 experience_weight: float = 0.4):
        """
        Initialize the JobMatcher.

        Args:
            skill_weight: Weight for skill matching (0.0 to 1.0)
            experience_weight: Weight for experience matching (0.0 to 1.0)
        """
        self.skill_weight = skill_weight
        self.experience_weight = experience_weight

        # Validate weights
        total_weight = skill_weight + experience_weight
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            self.skill_weight = skill_weight / total_weight
            self.experience_weight = experience_weight / total_weight

        logger.info(f"JobMatcher initialized with skill_weight={self.skill_weight:.2f}, "
                   f"experience_weight={self.experience_weight:.2f}")

    def match_resume_to_job(self, resume: Resume, job: Job) -> MatchResult:
        """
        Match a resume to a job posting and calculate explainable score.

        Args:
            resume: Resume object to match
            job: Job object to match against

        Returns:
            MatchResult with scores and explanations
        """
        logger.info(f"Matching resume '{resume.name}' to job '{job.title}' at {job.company}")

        # Initialize result
        result = MatchResult(
            resume_id=self._get_resume_id(resume),
            job_id=self._get_job_id(job),
            overall_score=0.0
        )

        # Calculate skill match
        skill_result = self._calculate_skill_match(resume, job)
        result.skill_score = skill_result['score']
        result.matched_required_skills = skill_result['matched_required']
        result.missing_required_skills = skill_result['missing_required']
        result.matched_preferred_skills = skill_result['matched_preferred']
        result.missing_preferred_skills = skill_result['missing_preferred']
        result.skill_matches = skill_result['skill_matches']

        # Calculate experience match
        experience_result = self._calculate_experience_match(resume, job)
        result.experience_score = experience_result['score']

        # Calculate overall score
        result.overall_score = (
            result.skill_score * self.skill_weight +
            result.experience_score * self.experience_weight
        )

        # Generate explanation
        result.explanation = self._generate_explanation(resume, job, result)
        result.strengths = self._identify_strengths(resume, job, result)
        result.weaknesses = self._identify_weaknesses(resume, job, result)
        result.recommendations = self._generate_recommendations(resume, job, result)

        logger.info(f"Match complete: {result.overall_score:.1f}% overall "
                   f"(Skills: {result.skill_score:.1f}%, Experience: {result.experience_score:.1f}%)")

        return result

    def _get_resume_id(self, resume: Resume) -> str:
        """Generate a unique ID for a resume."""
        if resume.file_source:
            # Use filename as ID if available
            import os
            return os.path.splitext(os.path.basename(resume.file_source))[0]
        # Fallback to name-based ID
        return re.sub(r'[^\w\-_]', '_', resume.name.lower()) or "unknown_resume"

    def _get_job_id(self, job: Job) -> str:
        """Generate a unique ID for a job."""
        company_part = re.sub(r'[^\w\-_]', '_', job.company.lower())
        title_part = re.sub(r'[^\w\-_]', '_', job.title.lower())
        return f"{company_part}_{title_part}" or "unknown_job"

    def _calculate_skill_match(self, resume: Resume, job: Job) -> Dict:
        """
        Calculate skill matching between resume and job.

        Returns:
            Dictionary with skill matching results
        """
        # Normalize skills for comparison
        resume_skills = {skill.lower().strip(): skill for skill in resume.skills}
        required_skills = {skill.lower().strip(): skill for skill in job.required_skills}
        preferred_skills = {skill.lower().strip(): skill for skill in job.preferred_skills}

        # Track matches
        matched_required = []
        missing_required = []
        matched_preferred = []
        missing_preferred = []
        skill_matches = []

        # Check required skills
        for skill_norm, skill_display in required_skills.items():
            matched, confidence, notes = self._skill_matches_resume(skill_norm, resume_skills)
            skill_matches.append(SkillMatch(
                skill=skill_display,
                required=True,
                matched=matched,
                confidence=confidence,
                notes=notes
            ))

            if matched:
                matched_required.append(skill_display)
            else:
                missing_required.append(skill_display)

        # Check preferred skills
        for skill_norm, skill_display in preferred_skills.items():
            matched, confidence, notes = self._skill_matches_resume(skill_norm, resume_skills)
            skill_matches.append(SkillMatch(
                skill=skill_display,
                required=False,
                matched=matched,
                confidence=confidence,
                notes=notes
            ))

            if matched:
                matched_preferred.append(skill_display)
            else:
                missing_preferred.append(skill_display)

        # Calculate skill score
        # Required skills are more important than preferred
        required_score = len(matched_required) / max(len(required_skills), 1) * 100
        preferred_score = len(matched_preferred) / max(len(preferred_skills), 1) * 100

        # Weight required skills higher (70%) than preferred (30%)
        if len(required_skills) > 0 or len(preferred_skills) > 0:
            skill_score = (required_score * 0.7) + (preferred_score * 0.3)
        else:
            skill_score = 100.0  # No skills required = perfect match

        return {
            'score': skill_score,
            'matched_required': matched_required,
            'missing_required': missing_required,
            'matched_preferred': matched_preferred,
            'missing_preferred': missing_preferred,
            'skill_matches': skill_matches
        }

    def _skill_matches_resume(self, skill_norm: str, resume_skills: Dict[str, str]) -> Tuple[bool, float, str]:
        """
        Check if a skill matches the resume with confidence scoring.

        Args:
            skill_norm: Normalized skill to match
            resume_skills: Dictionary of normalized resume skills

        Returns:
            Tuple of (matched, confidence, notes)
        """
        # Exact match
        if skill_norm in resume_skills:
            return True, 1.0, "Exact match"

        # Fuzzy match: check for substring matches or variations
        best_confidence = 0.0
        best_notes = ""

        for resume_skill_norm, resume_skill_display in resume_skills.items():
            # Check if skill is contained in resume skill (e.g., "Python" in "Python programming")
            if skill_norm in resume_skill_norm:
                confidence = 0.8
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_notes = f"Partial match: '{skill_norm}' found in '{resume_skill_display}'"

            # Check for common abbreviations/variations
            elif self._skills_are_related(skill_norm, resume_skill_norm):
                confidence = 0.6
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_notes = f"Related skills: '{skill_norm}' ~ '{resume_skill_display}'"

        matched = best_confidence > 0.5
        return matched, best_confidence, best_notes

    def _skills_are_related(self, skill1: str, skill2: str) -> bool:
        """
        Check if two skills are related (e.g., JS and JavaScript).

        Args:
            skill1: First skill
            skill2: Second skill

        Returns:
            True if skills are related
        """
        # Define skill relationships
        related_skills = {
            'js': ['javascript', 'node.js'],
            'javascript': ['js', 'node.js', 'ecmascript'],
            'node.js': ['js', 'javascript'],
            'ts': ['typescript'],
            'typescript': ['ts'],
            'py': ['python'],
            'python': ['py'],
            'ml': ['machine learning'],
            'machine learning': ['ml', 'ai'],
            'ai': ['ml', 'machine learning'],
            'db': ['sql', 'database'],
            'sql': ['db', 'database'],
            'aws': ['amazon web services'],
            'amazon web services': ['aws']
        }

        skill1_lower = skill1.lower()
        skill2_lower = skill2.lower()

        # Direct check
        if skill1_lower in related_skills and skill2_lower in related_skills[skill1_lower]:
            return True
        if skill2_lower in related_skills and skill1_lower in related_skills[skill2_lower]:
            return True

        return False

    def _calculate_experience_match(self, resume: Resume, job: Job) -> Dict:
        """
        Calculate experience matching between resume and job.

        Returns:
            Dictionary with experience matching results
        """
        # Get resume years of experience
        resume_years = resume.get_years_of_experience()

        # Get job requirements
        min_years = job.min_years_experience
        experience_level = job.experience_level.lower()

        # Calculate experience score
        score = 100.0  # Start with perfect score

        # Check minimum years requirement
        if min_years > 0:
            if resume_years >= min_years:
                # Bonus for exceeding requirements (up to a point)
                years_excess = resume_years - min_years
                if years_excess <= 5:  # Cap bonus at 5 years excess
                    score = min(100.0, score + (years_excess * 2))  # 2 points per year excess
                else:
                    score = 110.0  # Max bonus
            else:
                # Penalty for insufficient experience
                years_short = min_years - resume_years
                penalty = min(50.0, years_short * 15)  # 15 points per year short, max 50 penalty
                score = max(0.0, score - penalty)

        # Check experience level matching
        level_score = self._calculate_experience_level_match(resume, experience_level)
        # Combine years and level scores (70% years, 30% level)
        if experience_level:
            score = score * 0.7 + level_score * 0.3

        return {
            'score': score,
            'resume_years': resume_years,
            'job_min_years': min_years,
            'experience_level': experience_level
        }

    def _calculate_experience_level_match(self, resume: Resume, target_level: str) -> float:
        """
        Calculate how well resume experience level matches target level.

        Args:
            resume: Resume object
            target_level: Target experience level (entry, mid, senior, etc.)

        Returns:
            Score from 0.0 to 100.0
        """
        # Define experience level ranges (in years)
        level_ranges = {
            'entry': (0, 2),
            'junior': (0, 3),
            'mid': (2, 5),
            'middle': (2, 5),
            'senior': (5, 10),
            'lead': (5, 15),
            'principal': (8, 20),
            'executive': (10, 30)
        }

        resume_years = resume.get_years_of_experience()

        if target_level not in level_ranges:
            # Unknown level - assume match if any experience
            return 80.0 if resume_years > 0 else 50.0

        min_years, max_years = level_ranges[target_level]

        if min_years <= resume_years <= max_years:
            # Within range - perfect match
            return 100.0
        elif resume_years < min_years:
            # Below range - calculate how close
            if min_years == 0:
                return 100.0  # Entry level with 0 years is OK
            years_short = min_years - resume_years
            return max(0.0, 100.0 - (years_short * 20))  # 20 points per year short
        else:
            # Above range - calculate how much over
            years_over = resume_years - max_years
            if years_over <= 5:
                return max(80.0, 100.0 - (years_over * 5))  # Slight penalty for being overqualified
            else:
                return max(50.0, 100.0 - (years_over * 10))  # More penalty for being way overqualified

    def _generate_explanation(self, resume: Resume, job: Job, result: MatchResult) -> str:
        """
        Generate a human-readable explanation of the match score.

        Args:
            resume: Resume object
            job: Job object
            result: MatchResult with scores

        Returns:
            Explanation string
        """
        explanation_parts = []

        # Overall assessment
        if result.overall_score >= 90:
            explanation_parts.append("Excellent match - this candidate strongly meets the job requirements.")
        elif result.overall_score >= 80:
            explanation_parts.append("Strong match - this candidate meets most job requirements.")
        elif result.overall_score >= 70:
            explanation_parts.append("Good match - this candidate meets many job requirements.")
        elif result.overall_score >= 60:
            explanation_parts.append("Moderate match - this candidate meets some job requirements.")
        elif result.overall_score >= 50:
            explanation_parts.append("Weak match - this candidate meets few job requirements.")
        else:
            explanation_parts.append("Poor match - this candidate does not meet job requirements.")

        # Skill matching details
        req_matched = len(result.matched_required_skills)
        req_total = len(result.matched_required_skills) + len(result.missing_required_skills)
        if req_total > 0:
            explanation_parts.append(
                f"Skills: Matched {req_matched}/{req_total} required skills "
                f"({result.skill_score:.0f}% skill score)."
            )

        # Experience details
        explanation_parts.append(
            f"Experience: {result.experience_score:.0f}% match "
            f"(resume: ~{resume.get_years_of_experience():.1f} years, "
            f"job requires: {job.min_years_experience} years)."
        )

        # Specific gaps
        if result.missing_required_skills:
            explanation_parts.append(
                f"Missing required skills: {', '.join(result.missing_required_skills[:3])}"
                + ("..." if len(result.missing_required_skills) > 3 else "")
            )

        if result.missing_preferred_skills:
            explanation_parts.append(
                f"Missing preferred skills: {', '.join(result.missing_preferred_skills[:3])}"
                + ("..." if len(result.missing_preferred_skills) > 3 else "")
            )

        return " ".join(explanation_parts)

    def _identify_strengths(self, resume: Resume, job: Job, result: MatchResult) -> List[str]:
        """
        Identify candidate strengths for this job.

        Args:
            resume: Resume object
            job: Job object
            result: MatchResult with scores

        Returns:
            List of strength strings
        """
        strengths = []

        # Skill strengths
        if result.matched_required_skills:
            strengths.append(f"Strong match on required skills: {', '.join(result.matched_required_skills[:3])}")

        if result.matched_preferred_skills:
            strengths.append(f"Also has preferred skills: {', '.join(result.matched_preferred_skills[:3])}")

        # Experience strengths
        resume_years = resume.get_years_of_experience()
        if resume_years >= job.min_years_experience:
            strengths.append(f"Meets experience requirement ({resume_years:.1f} years >= {job.min_years_experience} years required)")

        # Education strengths (if we had more detailed education matching)
        if resume.education:
            strengths.append(f"Has {len(resume.education)} educational qualification(s)")

        # Limit to top 5 strengths
        return strengths[:5]

    def _identify_weaknesses(self, resume: Resume, job: Job, result: MatchResult) -> List[str]:
        """
        Identify candidate weaknesses for this job.

        Args:
            resume: Resume object
            job: Job object
            result: MatchResult with scores

        Returns:
            List of weakness strings
        """
        weaknesses = []

        # Skill weaknesses
        if result.missing_required_skills:
            weaknesses.append(f"Missing required skills: {', '.join(result.missing_required_skills[:3])}")

        if result.missing_preferred_skills:
            weaknesses.append(f"Missing preferred skills: {', '.join(result.missing_preferred_skills[:3])}")

        # Experience weaknesses
        resume_years = resume.get_years_of_experience()
        if resume_years < job.min_years_experience:
            weaknesses.append(f"Insufficient experience ({resume_years:.1f} years < {job.min_years_experience} years required)")

        # Limit to top 5 weaknesses
        return weaknesses[:5]

    def _generate_recommendations(self, resume: Resume, job: Job, result: MatchResult) -> List[str]:
        """
        Generate recommendations for improving the match.

        Args:
            resume: Resume object
            job: Job object
            result: MatchResult with scores

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Skill-based recommendations
        if result.missing_required_skills:
            skills_str = ', '.join(result.missing_required_skills[:3])
            recommendations.append(f"Consider gaining experience with: {skills_str}")

        # Experience-based recommendations
        resume_years = resume.get_years_of_experience()
        if resume_years < job.min_years_experience:
            needed = job.min_years_experience - resume_years
            recommendations.append(f"Gain approximately {needed:.1f} more years of relevant experience")

        # General recommendations based on score
        if result.overall_score < 60:
            recommendations.append("Consider applying for positions with lower experience requirements")
            recommendations.append("Look for roles that better match your current skill set")
        elif result.overall_score < 80:
            recommendations.append("Highlight transferable skills in your application")
            recommendations.append("Emphasize your ability to learn new technologies quickly")

        # Limit to top 3 recommendations
        return recommendations[:3]


def create_sample_matcher() -> JobMatcher:
    """
    Create a sample JobMatcher with default weights.

    Returns:
        Configured JobMatcher instance
    """
    return JobMatcher(skill_weight=0.6, experience_weight=0.4)


if __name__ == "__main__":
    # Test the matcher with sample data
    from models import Resume, Job, ContactInfo

    # Create sample resume
    sample_resume = Resume(
        name="John Doe",
        contact_info=ContactInfo(email="john@example.com", phone="555-1234"),
        skills=["Python", "JavaScript", "SQL", "Django", "React"],
        work_experience=[
            WorkExperience(
                title="Software Engineer",
                company="Tech Corp",
                start_date="Jan 2020",
                end_date="Present",
                description="Developed web applications using Python and JavaScript",
                skills_used=["Python", "JavaScript", "Django", "React"]
            )
        ],
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                institution="State University",
                graduation_year="2019"
            )
        ]
    )

    # Create sample job
    sample_job = Job(
        title="Senior Python Developer",
        company="ABC Company",
        required_skills=["Python", "Django", "SQL"],
        preferred_skills=["React", "AWS", "Docker"],
        experience_level="senior",
        min_years_experience=3.0,
        description="We are looking for a senior Python developer..."
    )

    # Test matching
    matcher = JobMatcher()
    result = matcher.match_resume_to_job(sample_resume, sample_job)

    print(f"Match Score: {result.overall_score:.1f}%")
    print(f"Explanation: {result.explanation}")
    print(f"Strengths: {', '.join(result.strengths)}")
    print(f"Weaknesses: {', '.join(result.weaknesses)}")