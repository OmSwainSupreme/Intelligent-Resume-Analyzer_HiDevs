"""
Report generation utilities for the Smart Hiring Assistant.
Generates reports in console, text, and JSON formats.
"""

import re
from typing import List, Dict, Any
from models import Resume, Job, MatchResult
from file_manager import FileManager
import json
from datetime import datetime


class Reporter:
    """Generates hiring reports in various formats."""

    def __init__(self, file_manager: FileManager = None):
        """
        Initialize the Reporter.

        Args:
            file_manager: FileManager instance for writing reports
        """
        self.file_manager = file_manager or FileManager()

    def generate_console_report(self,
                              resumes: List[Resume],
                              jobs: List[Job],
                              matches: List[MatchResult] = None) -> str:
        """
        Generate a formatted console report.

        Args:
            resumes: List of resume objects
            jobs: List of job objects
            matches: List of match results (if None, will generate all combinations)

        Returns:
            Formatted console report string
        """
        if matches is None:
            # Generate all combinations if not provided
            matches = []
            for resume in resumes:
                for job in jobs:
                    # In a real implementation, we'd call the matcher here
                    # For now, we'll create placeholder matches
                    pass

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SMART HIRING ASSISTANT - HIREING REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Resumes: {len(resumes)}")
        report_lines.append(f"Total Jobs: {len(jobs)}")
        report_lines.append("")

        # Sort matches by overall score (descending)
        sorted_matches = sorted(matches, key=lambda x: x.overall_score, reverse=True)

        report_lines.append("TOP CANDIDATE MATCHES:")
        report_lines.append("-" * 80)

        for i, match in enumerate(sorted_matches[:10], 1):  # Top 10 matches
            # Find the corresponding resume and job
            resume = next((r for r in resumes if self._get_resume_id(r) == match.resume_id), None)
            job = next((j for j in jobs if self._get_job_id(j) == match.job_id), None)

            resume_name = resume.name if resume else match.resume_id
            job_title = job.title if job else match.job_id
            company = job.company if job else "Unknown"

            report_lines.append(f"{i}. {resume_name} -> {job_title} at {company}")
            report_lines.append(f"   Overall Match: {match.overall_score:.1f}%")
            report_lines.append(f"   Skills Match: {match.skill_score:.1f}%")
            report_lines.append(f"   Experience Match: {match.experience_score:.1f}%")

            if match.explanation:
                report_lines.append(f"   Explanation: {match.explanation}")

            if match.strengths:
                report_lines.append(f"   Strengths: {', '.join(match.strengths[:3])}")

            if match.weaknesses:
                report_lines.append(f"   Concerns: {', '.join(match.weaknesses[:3])}")

            report_lines.append("")

        # Summary statistics
        if sorted_matches:
            scores = [m.overall_score for m in sorted_matches]
            report_lines.append("SUMMARY STATISTICS:")
            report_lines.append("-" * 80)
            report_lines.append(f"Average Match Score: {sum(scores)/len(scores):.1f}%")
            report_lines.append(f"Highest Match Score: {max(scores):.1f}%")
            report_lines.append(f"Lowest Match Score: {min(scores):.1f}%")

            strong_matches = [m for m in sorted_matches if m.is_strong_match()]
            medium_matches = [m for m in sorted_matches if m.is_medium_match()]
            weak_matches = [m for m in sorted_matches if m.is_weak_match()]

            report_lines.append(f"Strong Matches (≥80%): {len(strong_matches)}")
            report_lines.append(f"Medium Matches (60-79%): {len(medium_matches)}")
            report_lines.append(f"Weak Matches (<60%): {len(weak_matches)}")

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("End of Report")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def generate_text_report(self,
                           resume: Resume,
                           job: Job,
                           match_result: MatchResult) -> str:
        """
        Generate a detailed text report for a single resume-job match.

        Args:
            resume: Resume object
            job: Job object
            match_result: MatchResult for this specific pair

        Returns:
            Detailed text report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DETAILED CANDIDATE ASSESSMENT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Candidate Information
        report_lines.append("CANDIDATE INFORMATION:")
        report_lines.append("-" * 40)
        report_lines.append(f"Name: {resume.name}")
        if resume.contact_info.email:
            report_lines.append(f"Email: {resume.contact_info.email}")
        if resume.contact_info.phone:
            report_lines.append(f"Phone: {resume.contact_info.phone}")
        report_lines.append(f"Years of Experience: {resume.get_years_of_experience():.1f}")
        report_lines.append(f"Skills Count: {len(resume.skills)}")
        report_lines.append(f"Education Count: {len(resume.education)}")
        report_lines.append("")

        # Job Information
        report_lines.append("JOB INFORMATION:")
        report_lines.append("-" * 40)
        report_lines.append(f"Title: {job.title}")
        report_lines.append(f"Company: {job.company}")
        report_lines.append(f"Location: {job.location or 'Not specified'}")
        report_lines.append(f"Employment Type: {job.employment_type or 'Not specified'}")
        report_lines.append(f"Minimum Experience: {job.min_years_experience} years")
        report_lines.append(f"Experience Level: {job.experience_level or 'Not specified'}")
        report_lines.append("")

        # Match Results
        report_lines.append("MATCH RESULTS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Overall Match Score: {match_result.overall_score:.1f}%")
        report_lines.append(f"Skills Match Score: {match_result.skill_score:.1f}%")
        report_lines.append(f"Experience Match Score: {match_result.experience_score:.1f}%")
        report_lines.append("")

        # Detailed Explanation
        if match_result.explanation:
            report_lines.append("EXPLANATION:")
            report_lines.append("-" * 40)
            report_lines.append(match_result.explanation)
            report_lines.append("")

        # Skill Breakdown
        report_lines.append("SKILL BREAKDOWN:")
        report_lines.append("-" * 40)
        report_lines.append(f"Required Skills Matched: {len(match_result.matched_required_skills)}/"
                          f"{len(match_result.matched_required_skills) + len(match_result.missing_required_skills)}")
        if match_result.matched_required_skills:
            report_lines.append(f"  Matched: {', '.join(match_result.matched_required_skills)}")
        if match_result.missing_required_skills:
            report_lines.append(f"  Missing: {', '.join(match_result.missing_required_skills)}")

        report_lines.append(f"Preferred Skills Matched: {len(match_result.matched_preferred_skills)}/"
                          f"{len(match_result.matched_preferred_skills) + len(match_result.missing_preferred_skills)}")
        if match_result.matched_preferred_skills:
            report_lines.append(f"  Matched: {', '.join(match_result.matched_preferred_skills)}")
        if match_result.missing_preferred_skills:
            report_lines.append(f"  Missing: {', '.join(match_result.missing_preferred_skills)}")
        report_lines.append("")

        # Strengths and Weaknesses
        if match_result.strengths:
            report_lines.append("STRENGTHS:")
            report_lines.append("-" * 40)
            for strength in match_result.strengths:
                report_lines.append(f"• {strength}")
            report_lines.append("")

        if match_result.weaknesses:
            report_lines.append("AREAS FOR IMPROVEMENT:")
            report_lines.append("-" * 40)
            for weakness in match_result.weaknesses:
                report_lines.append(f"• {weakness}")
            report_lines.append("")

        # Recommendations
        if match_result.recommendations:
            report_lines.append("RECOMMENDATIONS:")
            report_lines.append("-" * 40)
            for rec in match_result.recommendations:
                report_lines.append(f"• {rec}")
            report_lines.append("")

        # Detailed Skill Matches
        if match_result.skill_matches:
            report_lines.append("DETAILED SKILL MATCHES:")
            report_lines.append("-" * 40)
            for skill_match in match_result.skill_matches:
                req_text = "Required" if skill_match.required else "Preferred"
                match_text = "✓ MATCH" if skill_match.matched else "✗ MISS"
                conf_text = f"({skill_match.confidence:.0%} confidence)"
                report_lines.append(f"  {match_text} {skill_match.skill} [{req_text}] {conf_text}")
                if skill_match.notes:
                    report_lines.append(f"      Note: {skill_match.notes}")
            report_lines.append("")

        report_lines.append("=" * 80)
        report_lines.append("End of Assessment")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def generate_json_report(self,
                           resumes: List[Resume],
                           jobs: List[Job],
                           matches: List[MatchResult] = None) -> Dict[str, Any]:
        """
        Generate a JSON report containing all match data.

        Args:
            resumes: List of resume objects
            jobs: List of job objects
            matches: List of match results (if None, will generate all combinations)

        Returns:
            Dictionary suitable for JSON serialization
        """
        if matches is None:
            # In a real implementation, we'd generate matches here
            matches = []

        # Prepare data for JSON serialization
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_resumes": len(resumes),
                "total_jobs": len(jobs),
                "total_matches": len(matches)
            },
            "resumes": [
                {
                    "id": self._get_resume_id(r),
                    "name": r.name,
                    "contact_info": {
                        "email": r.contact_info.email,
                        "phone": r.contact_info.phone,
                        "linkedin": r.contact_info.linkedin,
                        "github": r.contact_info.github
                    },
                    "skills": r.skills,
                    "years_of_experience": r.get_years_of_experience(),
                    "education_count": len(r.education),
                    "file_source": r.file_source
                }
                for r in resumes
            ],
            "jobs": [
                {
                    "id": self._get_job_id(j),
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "employment_type": j.employment_type,
                    "min_years_experience": j.min_years_experience,
                    "experience_level": j.experience_level,
                    "required_skills": j.required_skills,
                    "preferred_skills": j.preferred_skills
                }
                for j in jobs
            ],
            "matches": [
                {
                    "resume_id": m.resume_id,
                    "job_id": m.job_id,
                    "overall_score": m.overall_score,
                    "skill_score": m.skill_score,
                    "experience_score": m.experience_score,
                    "explanation": m.explanation,
                    "strengths": m.strengths,
                    "weaknesses": m.weaknesses,
                    "recommendations": m.recommendations,
                    "skill_breakdown": {
                        "matched_required": m.matched_required_skills,
                        "missing_required": m.missing_required_skills,
                        "matched_preferred": m.matched_preferred_skills,
                        "missing_preferred": m.missing_preferred_skills
                    },
                    "detailed_skill_matches": [
                        {
                            "skill": sm.skill,
                            "required": sm.required,
                            "matched": sm.matched,
                            "confidence": sm.confidence,
                            "notes": sm.notes
                        }
                        for sm in m.skill_matches
                    ],
                    "is_strong_match": m.is_strong_match(),
                    "is_medium_match": m.is_medium_match(),
                    "is_weak_match": m.is_weak_match(),
                    "matched_at": m.matched_at.isoformat() if hasattr(m.matched_at, 'isoformat') else str(m.matched_at)
                }
                for m in matches
            ],
            "summary": self._generate_match_summary(matches)
        }

        return data

    def write_console_report(self, report_content: str, filename: str = "console_report.txt") -> bool:
        """
        Write console report to file.

        Args:
            report_content: Report content to write
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        return self.file_manager.write_report(report_content, filename)

    def write_text_report(self, report_content: str, filename: str = "detailed_report.txt") -> bool:
        """
        Write detailed text report to file.

        Args:
            report_content: Report content to write
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        return self.file_manager.write_report(report_content, filename)

    def write_json_report(self, data: Dict[str, Any], filename: str = "matches_report.json") -> bool:
        """
        Write JSON report to file.

        Args:
            data: Report data dictionary
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        return self.file_manager.write_json_report(data, filename)

    def _get_resume_id(self, resume: Resume) -> str:
        """Generate a unique ID for a resume."""
        if resume.file_source:
            import os
            return os.path.splitext(os.path.basename(resume.file_source))[0]
        return re.sub(r'[^\w\-_]', '_', resume.name.lower()) or "unknown_resume"

    def _get_job_id(self, job: Job) -> str:
        """Generate a unique ID for a job."""
        company_part = re.sub(r'[^\w\-_]', '_', job.company.lower())
        title_part = re.sub(r'[^\w\-_]', '_', job.title.lower())
        return f"{company_part}_{title_part}" or "unknown_job"

    def _generate_match_summary(self, matches: List[MatchResult]) -> Dict[str, Any]:
        """
        Generate summary statistics from matches.

        Args:
            matches: List of match results

        Returns:
            Dictionary with summary statistics
        """
        if not matches:
            return {
                "total_matches": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "strong_matches": 0,
                "medium_matches": 0,
                "weak_matches": 0
            }

        scores = [m.overall_score for m in matches]
        strong_matches = [m for m in matches if m.is_strong_match()]
        medium_matches = [m for m in matches if m.is_medium_match()]
        weak_matches = [m for m in matches if m.is_weak_match()]

        return {
            "total_matches": len(matches),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "strong_matches": len(strong_matches),
            "medium_matches": len(medium_matches),
            "weak_matches": len(weak_matches)
        }


def create_sample_reporter() -> Reporter:
    """
    Create a sample Reporter instance.

    Returns:
        Configured Reporter instance
    """
    return Reporter()


if __name__ == "__main__":
    # Test the reporter with sample data
    from models import Resume, Job, ContactInfo, MatchResult

    # Create sample resume and job
    sample_resume = Resume(
        name="Jane Smith",
        contact_info=ContactInfo(email="jane@example.com", phone="555-5678"),
        skills=["Python", "Java", "SQL", "Spring Boot"],
        work_experience=[
            WorkExperience(
                title="Backend Developer",
                company="Enterprise Inc",
                start_date="Mar 2019",
                end_date="Present",
                description="Developed microservices using Java and Spring Boot",
                skills_used=["Java", "Spring Boot", "SQL", "Docker"]
            )
        ],
        education=[
            Education(
                degree="Master of Science in Software Engineering",
                institution="Tech Institute",
                graduation_year="2018"
            )
        ]
    )

    sample_job = Job(
        title="Senior Java Engineer",
        company="XYZ Corp",
        required_skills=["Java", "Spring Boot", "Microservices"],
        preferred_skills=["AWS", "Kubernetes", "Docker"],
        experience_level="senior",
        min_years_experience=4.0,
        description="Looking for experienced Java developer..."
    )

    # Create a sample match result
    sample_match = MatchResult(
        resume_id="jane_smith",
        job_id="xyz_corp_senior_java_engineer",
        overall_score=85.5,
        skill_score=80.0,
        experience_score=95.0,
        matched_required_skills=["Java", "Spring Boot"],
        missing_required_skills=["Microservices"],
        matched_preferred_skills=["Docker"],
        missing_preferred_skills=["AWS", "Kubernetes"],
        explanation="Strong match with solid Java/Spring Boot experience. Good technical fit with minor gaps in cloud technologies.",
        strengths=[
            "Strong match on required skills: Java, Spring Boot",
            "Exceeds experience requirement (6.2 years >= 4.0 years required)",
            "Has preferred skill: Docker"
        ],
        weaknesses=[
            "Missing required skill: Microservices",
            "Missing preferred skills: AWS, Kubernetes"
        ],
        recommendations=[
            "Consider gaining experience with microservices architecture",
            "Highlight transferable skills in your application"
        ]
    )

    # Test reporting
    reporter = Reporter()

    # Console report
    console_report = reporter.generate_console_report([sample_resume], [sample_job], [sample_match])
    print("CONSOLE REPORT:")
    print(console_report)
    print("\n" + "="*50 + "\n")

    # Text report
    text_report = reporter.generate_text_report(sample_resume, sample_job, sample_match)
    print("TEXT REPORT (first 500 chars):")
    print(text_report[:500] + "..." if len(text_report) > 500 else text_report)
    print("\n" + "="*50 + "\n")

    # JSON report
    json_data = reporter.generate_json_report([sample_resume], [sample_job], [sample_match])
    print("JSON REPORT (keys):")
    print(list(json_data.keys()))