"""
Unit tests for the resume parser.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parser import ResumeParser
from models import Resume, ContactInfo, WorkExperience, Education


class TestResumeParser(unittest.TestCase):
    """Test cases for the ResumeParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = ResumeParser()

    def test_parse_simple_resume(self):
        """Test parsing a simple resume."""
        resume_text = """
John Doe
email: john@example.com
phone: 555-123-4567

SKILLS
Python, JavaScript, SQL

EXPERIENCE
Software Engineer
Tech Company | Jan 2020 - Present
- Developed web applications

EDUCATION
Bachelor of Science in Computer Science
University | Graduated: 2019
"""

        resume = self.parser.parse_resume(resume_text, "test_resume.txt")

        # Check basic info
        self.assertEqual(resume.name, "John Doe")
        self.assertEqual(resume.contact_info.email, "john@example.com")
        self.assertEqual(resume.contact_info.phone, "555-123-4567")

        # Check skills
        self.assertIn("python", [s.lower() for s in resume.skills])
        self.assertIn("javascript", [s.lower() for s in resume.skills])
        self.assertIn("sql", [s.lower() for s in resume.skills])

        # Check experience
        self.assertEqual(len(resume.work_experience), 1)
        exp = resume.work_experience[0]
        self.assertEqual(exp.title, "Software Engineer")
        self.assertEqual(exp.company, "Tech Company")

        # Check education
        self.assertEqual(len(resume.education), 1)
        edu = resume.education[0]
        self.assertEqual(edu.degree, "Bachelor of Science in Computer Science")
        self.assertEqual(edu.institution, "University")

    def test_extract_contact_info(self):
        """Test contact information extraction."""
        text = """
John Doe
email: JOHN@EXAMPLE.COM
phone: (555) 123-4567
linkedin: john doe
github: johndoe
"""

        contact_info = self.parser._extract_contact_info(text)

        self.assertEqual(contact_info.email, "john@example.com")
        self.assertEqual(contact_info.phone, "(555) 123-4567")
        self.assertEqual(contact_info.linkedin, "john doe")
        self.assertEqual(contact_info.github, "johndoe")

    def test_extract_skills(self):
        """Test skills extraction."""
        text = """
SKILLS
Python, JavaScript, HTML/CSS, SQL, Git
Experience with AWS and Docker
"""

        skills = self.parser._extract_skills(text)

        # Should find skills from the skills section and from the experience text
        self.assertIn("python", [s.lower() for s in skills])
        self.assertIn("javascript", [s.lower() for s in skills])
        self.assertIn("sql", [s.lower() for s in skills])
        self.assertIn("git", [s.lower() for s in skills])
        # Note: HTML/CSS might be split or handled differently
        self.assertIn("aws", [s.lower() for s in skills])
        self.assertIn("docker", [s.lower() for s in skills])

    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Hello    World  \r\n\r\n  Test\t\t  "
        clean_text = self.parser._clean_text(dirty_text)
        self.assertEqual(clean_text, "Hello World\nTest")

    def test_extract_name(self):
        """Test name extraction."""
        text = """John Doe
email: john@example.com
Software Engineer with 5 years experience"""

        name = self.parser._extract_name(text)
        self.assertEqual(name, "John Doe")

        # Test with empty text
        empty_name = self.parser._extract_name("")
        self.assertEqual(empty_name, "")


if __name__ == '__main__':
    unittest.main()