"""
Unit tests for the job matcher.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from matcher import JobMatcher
from models import Resume, Job, ContactInfo, WorkExperience, Education


class TestJobMatcher(unittest.TestCase):
    """Test cases for the JobMatcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.matcher = JobMatcher(skill_weight=0.6, experience_weight=0.4)

        # Create a sample resume
        self.sample_resume = Resume(
            name="John Doe",
            contact_info=ContactInfo(email="john@example.com"),
            skills=["Python", "Django", "SQL", "JavaScript"],
            work_experience=[
                WorkExperience(
                    title="Senior Developer",
                    company="Tech Corp",
                    start_date="Jan 2020",
                    end_date="Present",
                    description="Led development team",
                    skills_used=["Python", "Django"]
                ),
                WorkExperience(
                    title="Software Engineer",
                    company="Web Inc",
                    start_date="Jun 2018",
                    end_date="Dec 2019",
                    description="Built web applications",
                    skills_used=["JavaScript", "SQL"]
                )
            ],
            education=[
                Education(
                    degree="Bachelor of Science in Computer Science",
                    institution="State University",
                    graduation_year="2018"
                )
            ]
        )

        # Create a sample job
        self.sample_job = Job(
            title="Senior Python Developer",
            company="ABC Company",
            required_skills=["Python", "Django", "SQL"],
            preferred_skills=["React", "AWS", "Docker"],
            experience_level="senior",
            min_years_experience=3.0,
            description="Senior Python developer position"
        )

    def test_skill_matching(self):
        """Test skill matching functionality."""
        result = self.matcher.match_resume_to_job(self.sample_resume, self.sample_job)

        # Should have good skill match since resume has Python, Django, SQL
        self.assertGreaterEqual(result.skill_score, 70.0)

        # Should have matched required skills
        self.assertIn("Python", result.matched_required_skills)
        self.assertIn("Django", result.matched_required_skills)
        self.assertIn("SQL", result.matched_required_skills)

        # Should not have missing required skills (since we have all three)
        self.assertEqual(len(result.missing_required_skills), 0)

    def test_experience_matching(self):
        """Test experience matching functionality."""
        result = self.matcher.match_resume_to_job(self.sample_resume, self.sample_job)

        # Resume has ~2 years experience (two entries at 1 year each), job requires 3+ years
        # Should have fair experience score
        self.assertGreaterEqual(result.experience_score, 70.0)

        # Test with insufficient experience
        low_exp_job = Job(
            title="Entry Level Developer",
            required_skills=["Python"],
            min_years_experience=0.0,
            experience_level="entry"
        )

        result_low = self.matcher.match_resume_to_job(self.sample_resume, low_exp_job)
        # Should still have good experience score (overqualified but not penalized too much)
        self.assertGreaterEqual(result_low.experience_score, 70.0)

    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        result = self.matcher.match_resume_to_job(self.sample_resume, self.sample_job)

        # Overall score should be weighted average
        expected_score = (result.skill_score * 0.6) + (result.experience_score * 0.4)
        self.assertAlmostEqual(result.overall_score, expected_score, places=1)

        # Score should be between 0 and 100
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 100.0)

    def test_match_result_properties(self):
        """Test MatchResult helper methods."""
        result = self.matcher.match_resume_to_job(self.sample_resume, self.sample_job)

        # Test is_strong_match
        if result.overall_score >= 80.0:
            self.assertTrue(result.is_strong_match())
        else:
            self.assertFalse(result.is_strong_match())

        # Test is_weak_match
        if result.overall_score < 60.0:
            self.assertTrue(result.is_weak_match())
        else:
            self.assertFalse(result.is_weak_match())

        # Test is_medium_match
        if 60.0 <= result.overall_score < 80.0:
            self.assertTrue(result.is_medium_match())
        else:
            self.assertFalse(result.is_medium_match())

    def test_empty_resume(self):
        """Test matching with empty resume."""
        empty_resume = Resume(name="Empty", skills=[], work_experience=[], education=[])

        result = self.matcher.match_resume_to_job(empty_resume, self.sample_job)

        # Should have low scores
        self.assertLess(result.skill_score, 30.0)
        self.assertLess(result.experience_score, 40.0)
        self.assertLess(result.overall_score, 30.0)


if __name__ == '__main__':
    unittest.main()