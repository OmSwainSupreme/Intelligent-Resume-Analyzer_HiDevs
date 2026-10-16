"""
Integration test for the Smart Hiring Assistant.
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import load_resumes, load_jobs, run_matching_engine, generate_reports
from models import Resume, Job, ContactInfo, WorkExperience, Education
from file_manager import FileManager
from config import Config


class TestIntegration(unittest.TestCase):
    """Integration test cases."""

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

        # Create sample resume file
        resume_content = """
John Doe
email: john@example.com
phone: 555-123-4567

SKILLS
Python, Django, SQL, JavaScript

EXPERIENCE
Senior Software Engineer
Tech Corp | Jan 2020 - Present
- Developed web applications using Python/Django
- Led team of 3 developers

Software Engineer
Web Inc | Jun 2018 - Dec 2019
- Built REST APIs with Node.js
- Worked with SQL databases

EDUCATION
Bachelor of Science in Computer Science
State University | Graduated: 2018
"""

        resume_file = os.path.join(self.resumes_dir, "sample_resume.txt")
        with open(resume_file, 'w') as f:
            f.write(resume_content)

        # Create sample job file
        job_content = """
Senior Python Developer
ABC Company
Location: Remote
Employment Type: Full-time

We are looking for an experienced Python developer.

REQUIRED SKILLS
Python, Django, SQL, Git

PREFERRED SKILLS
React, AWS, Docker

EXPERIENCE LEVEL
Senior
MINIMUM YEARS: 3 years

JOB DESCRIPTION
- Develop backend services using Python/Django
- Work with relational databases
- Collaborate with frontend team
"""

        job_file = os.path.join(self.jobs_dir, "sample_job.txt")
        with open(job_file, 'w') as f:
            f.write(job_content)

        # Create file manager with test directories
        self.file_manager = FileManager(self.resumes_dir, self.jobs_dir, self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_load_resumes(self):
        """Test loading resumes from files."""
        resumes = load_resumes(self.file_manager)
        self.assertGreaterEqual(len(resumes), 1)

        resume = resumes[0]
        self.assertEqual(resume.name, "John Doe")
        self.assertEqual(resume.contact_info.email, "john@example.com")
        self.assertIn("python", [s.lower() for s in resume.skills])
        self.assertIn("django", [s.lower() for s in resume.skills])
        self.assertIn("sql", [s.lower() for s in resume.skills])
        self.assertGreaterEqual(len(resume.work_experience), 1)
        self.assertGreaterEqual(len(resume.education), 1)

    def test_load_jobs(self):
        """Test loading jobs from files."""
        jobs = load_jobs(self.file_manager)
        self.assertGreaterEqual(len(jobs), 1)

        job = jobs[0]
        self.assertEqual(job.title, "Senior Python Developer")
        self.assertEqual(job.company, "ABC Company")
        self.assertIn("python", [s.lower() for s in job.required_skills])
        self.assertIn("django", [s.lower() for s in job.required_skills])
        self.assertIn("sql", [s.lower() for s in job.required_skills])
        self.assertIn("git", [s.lower() for s in job.required_skills])
        self.assertGreaterEqual(job.min_years_experience, 3.0)
        self.assertEqual(job.experience_level.lower(), "senior")

    def test_run_matching_engine(self):
        """Test running the matching engine."""
        resumes = load_resumes(self.file_manager)
        jobs = load_jobs(self.file_manager)

        self.assertGreaterEqual(len(resumes), 1)
        self.assertGreaterEqual(len(jobs), 1)

        matches = run_matching_engine(resumes, jobs)
        self.assertGreaterEqual(len(matches), 1)

        match = matches[0]
        # Should have a reasonable match score
        self.assertGreaterEqual(match.overall_score, 0.0)
        self.assertLessEqual(match.overall_score, 100.0)

        # Should have explanation
        self.assertIsInstance(match.explanation, str)
        self.assertGreater(len(match.explanation), 0)

        # Should have strengths and weaknesses
        self.assertIsInstance(match.strengths, list)
        self.assertIsInstance(match.weaknesses, list)
        self.assertIsInstance(match.recommendations, list)

    def test_generate_reports(self):
        """Test generating reports."""
        resumes = load_resumes(self.file_manager)
        jobs = load_jobs(self.file_manager)
        matches = run_matching_engine(resumes, jobs)

        # This should not raise an exception
        try:
            generate_reports(resumes, jobs, matches, self.file_manager)
            success = True
        except Exception as e:
            success = False
            print(f"Error generating reports: {e}")

        self.assertTrue(success)

        # Check that output files were created
        output_files = os.listdir(self.output_dir)
        self.assertGreater(len(output_files), 0)

        # Check for expected report files
        report_extensions = ['.txt', '.json']
        has_reports = any(any(f.endswith(ext) for ext in report_extensions)
                         for f in output_files)
        self.assertTrue(has_reports)


if __name__ == '__main__':
    unittest.main()