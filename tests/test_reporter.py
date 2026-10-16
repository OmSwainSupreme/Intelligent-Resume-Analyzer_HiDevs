"""
Unit tests for the reporter.
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reporter import Reporter
from file_manager import FileManager
from models import Resume, Job, ContactInfo, WorkExperience, Education, MatchResult


class TestReporter(unittest.TestCase):
    """Test cases for the Reporter class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.resumes_dir = os.path.join(self.test_dir, "resumes")
        self.jobs_dir = os.path.join(self.test_dir, "jobs")
        self.output_dir = os.path.join(self.test_dir, "output")

        os.makedirs(self.resumes_dir)
        os.makedirs(self.jobs_dir)
        os.makedirs(self.output_dir)

        self.file_manager = FileManager(self.resumes_dir, self.jobs_dir, self.output_dir)
        self.reporter = Reporter(self.file_manager)

        # Create sample resume and job
        self.sample_resume = Resume(
            name="Jane Smith",
            contact_info=ContactInfo(email="jane@example.com", phone="555-123-4567"),
            skills=["Python", "JavaScript", "SQL"],
            work_experience=[
                WorkExperience(
                    title="Software Engineer",
                    company="Tech Corp",
                    start_date="Jan 2020",
                    end_date="Present",
                    description="Developed web applications",
                    skills_used=["Python", "JavaScript"]
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

        self.sample_job = Job(
            title="Senior Developer",
            company="ABC Company",
            required_skills=["Python", "Django"],
            preferred_skills=["React", "AWS"],
            experience_level="senior",
            min_years_experience=3.0,
            description="Senior developer position"
        )

        self.sample_match = MatchResult(
            resume_id="jane_smith",
            job_id="abc_company_senior_developer",
            overall_score=75.5,
            skill_score=70.0,
            experience_score=85.0,
            matched_required_skills=["Python"],
            missing_required_skills=["Django"],
            matched_preferred_skills=[],
            missing_preferred_skills=["React", "AWS"],
            explanation="Good match with solid Python experience. Missing Django framework experience.",
            strengths=[
                "Strong Python skills",
                "Good experience level match"
            ],
            weaknesses=[
                "Missing Django framework experience",
                "Missing AWS cloud experience"
            ],
            recommendations=[
                "Consider learning Django for web development",
                "Gain experience with AWS cloud services"
            ]
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_generate_console_report(self):
        """Test console report generation."""
        report = self.reporter.generate_console_report(
            [self.sample_resume],
            [self.sample_job],
            [self.sample_match]
        )

        # Check that report contains expected elements
        self.assertIn("SMART HIRING ASSISTANT", report)
        self.assertIn("Jane Smith", report)
        self.assertIn("ABC Company", report)
        self.assertIn("75.5%", report)
        self.assertIn("Skills Match:", report)
        self.assertIn("Experience Match:", report)
        self.assertIn("Explanation:", report)

    def test_generate_text_report(self):
        """Test detailed text report generation."""
        report = self.reporter.generate_text_report(
            self.sample_resume,
            self.sample_job,
            self.sample_match
        )

        # Check that report contains expected elements
        self.assertIn("DETAILED CANDIDATE ASSESSMENT", report)
        self.assertIn("Jane Smith", report)
        self.assertIn("Senior Developer", report)
        self.assertIn("ABC Company", report)
        self.assertIn("75.5%", report)
        self.assertIn("EXPLANATION:", report)
        self.assertIn("STRENGTHS:", report)
        self.assertIn("AREAS FOR IMPROVEMENT:", report)
        self.assertIn("RECOMMENDATIONS:", report)

    def test_generate_json_report(self):
        """Test JSON report generation."""
        json_data = self.reporter.generate_json_report(
            [self.sample_resume],
            [self.sample_job],
            [self.sample_match]
        )

        # Check that JSON data has expected structure
        self.assertIn("metadata", json_data)
        self.assertIn("resumes", json_data)
        self.assertIn("jobs", json_data)
        self.assertIn("matches", json_data)
        self.assertIn("summary", json_data)

        # Check metadata
        self.assertEqual(json_data["metadata"]["total_resumes"], 1)
        self.assertEqual(json_data["metadata"]["total_jobs"], 1)
        self.assertEqual(json_data["metadata"]["total_matches"], 1)

        # Check resume data
        resume_data = json_data["resumes"][0]
        self.assertEqual(resume_data["name"], "Jane Smith")
        self.assertEqual(resume_data["contact_info"]["email"], "jane@example.com")
        self.assertEqual(resume_data["skills"], ["Python", "JavaScript", "SQL"])

        # Check job data
        job_data = json_data["jobs"][0]
        self.assertEqual(job_data["title"], "Senior Developer")
        self.assertEqual(job_data["company"], "ABC Company")
        self.assertEqual(job_data["required_skills"], ["Python", "Django"])

        # Check match data
        match_data = json_data["matches"][0]
        self.assertEqual(match_data["overall_score"], 75.5)
        self.assertEqual(match_data["skill_score"], 70.0)
        self.assertEqual(match_data["experience_score"], 85.0)
        self.assertEqual(match_data["explanation"],
                        "Good match with solid Python experience. Missing Django framework experience.")

    def test_write_reports(self):
        """Test writing reports to files."""
        # Test console report
        console_report = self.reporter.generate_console_report(
            [self.sample_resume],
            [self.sample_job],
            [self.sample_match]
        )

        success = self.reporter.write_console_report(console_report, "test_console.txt")
        self.assertTrue(success)

        # Check file exists
        console_path = os.path.join(self.output_dir, "test_console.txt")
        self.assertTrue(os.path.exists(console_path))

        # Test JSON report
        json_data = self.reporter.generate_json_report(
            [self.sample_resume],
            [self.sample_job],
            [self.sample_match]
        )

        success = self.reporter.write_json_report(json_data, "test_json.json")
        self.assertTrue(success)

        # Check file exists
        json_path = os.path.join(self.output_dir, "test_json.json")
        self.assertTrue(os.path.exists(json_path))

        # Test text report
        text_report = self.reporter.generate_text_report(
            self.sample_resume,
            self.sample_job,
            self.sample_match
        )

        success = self.reporter.write_text_report(text_report, "test_text.txt")
        self.assertTrue(success)

        # Check file exists
        text_path = os.path.join(self.output_dir, "test_text.txt")
        self.assertTrue(os.path.exists(text_path))


if __name__ == '__main__':
    unittest.main()