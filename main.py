import argparse
import sys
import re
from typing import List, Optional
from pathlib import Path

from file_manager import FileManager
from models import Resume, Job, MatchResult
from parser import ResumeParser
from matcher import JobMatcher
from reporter import Reporter
from config import get_config, setup_logging, init_config
from ai_assistant import AIAssistant
import logging


def load_resumes(file_manager: FileManager) -> List[Resume]:
    """
    Load and parse all resume files.

    Args:
        file_manager: FileManager instance

    Returns:
        List of parsed Resume objects
    """
    resumes = []

    resume_files = file_manager.list_resume_files()
    for resume_file in resume_files:
        try:
            text = file_manager.read_resume(resume_file)
            if text is not None:
                resume = ResumeParser().parse_resume(text, str(resume_file))
                resumes.append(resume)
                print(f"Parsed resume: {resume.name} ({len(resume.skills)} skills)")
            else:
                print(f"Warning: Could not read resume file {resume_file}")
        except Exception as e:
            print(f"Error parsing resume {resume_file}: {e}")

    return resumes


def load_jobs(file_manager: FileManager) -> List[Job]:
    """
    Load and parse all job description files.

    Args:
        file_manager: FileManager instance

    Returns:
        List of parsed Job objects
    """
    # For now, we'll create simple Job objects from text
    # In a more advanced implementation, we'd have a JobParser
    jobs = []

    job_files = file_manager.list_job_files()
    for job_file in job_files:
        try:
            text = file_manager.read_job(job_file)
            if text is not None:
                # Simple job parsing - in reality, this would be more sophisticated
                job = parse_job_from_text(text, str(job_file))
                if job:
                    jobs.append(job)
                    print(f"Parsed job: {job.title} at {job.company}")
                else:
                    print(f"Warning: Could not parse job file {job_file}")
            else:
                print(f"Warning: Could not read job file {job_file}")
        except Exception as e:
            print(f"Error parsing job {job_file}: {e}")

    return jobs


def parse_job_from_text(text: str, file_source: str) -> Optional[Job]:
    """
    Parse a job description from text (simple implementation).

    Args:
        text: Job description text
        file_source: Source file path

    Returns:
        Job object or None if parsing fails
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return None

    # Extract basic information (this is a simplified parser)
    title = "Unknown Title"
    company = "Unknown Company"
    location = ""
    employment_type = ""
    required_skills = []
    preferred_skills = []
    experience_level = ""
    min_years_experience = 0.0
    description = ""

    # Simple parsing logic
    in_required = False
    in_preferred = False
    in_description = False
    # Flag to indicate that the next non-empty line should be the experience level
    next_line_is_experience_level = False

    for line in lines:
        line_lower = line.lower()

        # Look for title and company (usually at the start)
        if title == "Unknown Title" and line and not any(x in line_lower for x in ['email', 'phone', 'location']):
            # Heuristic: first substantial line might be title
            if len(line) < 100 and not line.isupper():  # Not all caps like a header
                title = line

        # Look for company
        if company == "Unknown Company" and title != "Unknown Title" and line and line != title:
            if len(line) < 100 and not any(x in line_lower for x in ['location', 'employment', 'required', 'preferred']):
                company = line

        # Section detection
        if 'required skills' in line_lower:
            in_required = True
            in_preferred = False
            next_line_is_experience_level = False  # Reset flag
            continue
        elif 'preferred skills' in line_lower:
            in_preferred = True
            in_required = False
            next_line_is_experience_level = False  # Reset flag
            continue
        elif 'experience level' in line_lower:
            in_required = False
            in_preferred = False
            # Extract experience level
            if ':' in line:
                experience_level = line.split(':', 1)[1].strip()
            else:
                # The value might be on the next line
                next_line_is_experience_level = True
            continue
        elif 'minimum years' in line_lower or 'min years' in line_lower:
            in_required = False
            in_preferred = False
            # Extract years
            import re
            years_match = re.search(r'(\d+\.?\d*)', line)
            if years_match:
                try:
                    min_years_experience = float(years_match.group(1))
                except ValueError:
                    pass
            continue
        elif any(x in line_lower for x in ['location:', 'employment type:']):
            in_required = False
            in_preferred = False
            next_line_is_experience_level = False  # Reset flag
            if 'location:' in line_lower:
                location = line.split(':', 1)[1].strip()
            elif 'employment type:' in line_lower:
                employment_type = line.split(':', 1)[1].strip()
            continue
        elif line_lower.startswith('job description') or line_lower.startswith('description:'):
            in_description = True
            in_required = False
            in_preferred = False
            next_line_is_experience_level = False  # Reset flag
            continue
        # Handle the case where the experience level is on the next line
        if next_line_is_experience_level and line:
            # We found the line after the "experience level" header
            experience_level = line.strip()
            next_line_is_experience_level = False
            # Continue to process this line for other sections? We'll assume it's just the value and not a section header.
            # But to be safe, we'll not process it as a section header and continue to next iteration.
            continue
        elif line and not line.isupper() and len(line) < 200:  # Likely content, not a header
            if in_description:
                description += line + " "
            elif in_required:
                # Extract skill from line (remove bullets, etc.)
                skills_line = line.lstrip('•-* ').strip()
                if skills_line:
                    # Split by commas and clean each skill
                    skills = [s.strip() for s in skills_line.split(',') if s.strip()]
                    required_skills.extend(skills)
            elif in_preferred:
                # Extract skill from line (remove bullets, etc.)
                skills_line = line.lstrip('•-* ').strip()
                if skills_line:
                    # Split by commas and clean each skill
                    skills = [s.strip() for s in skills_line.split(',') if s.strip()]
                    preferred_skills.extend(skills)

    # Clean up description
    description = description.strip()

    # If we didn't find title/company properly, try to extract from beginning
    if title == "Unknown Title" or company == "Unknown Company":
        # Look for patterns like "Title at Company" or "Title, Company"
        if lines:
            first_line = lines[0]
            if ' at ' in first_line:
                parts = first_line.split(' at ', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    company = parts[1].strip()
            elif ', ' in first_line and len(first_line.split(', ', 1)) == 2:
                parts = first_line.split(', ', 1)
                # Heuristic: if second part looks like a company name
                if len(parts[1]) < 50 and not parts[1].isupper():
                    title = parts[0].strip()
                    company = parts[1].strip()

    return Job(
        title=title,
        company=company,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_level=experience_level,
        min_years_experience=min_years_experience,
        description=description,
        location=location,
        employment_type=employment_type
    )


def run_matching_engine(resumes: List[Resume], jobs: List[Job]) -> List[MatchResult]:
    """
    Run the matching engine on all resume-job combinations.

    Args:
        resumes: List of resume objects
        jobs: List of job objects

    Returns:
        List of match results
    """
    config = get_config()
    matcher = JobMatcher(
        skill_weight=config.get("skill_weight", 0.6),
        experience_weight=config.get("experience_weight", 0.4)
    )

    ai_assistant = AIAssistant(
        enabled=config.get("ai_enabled", False),
        provider=config.get("ai_provider", "none")
    )

    matches = []
    total_comparisons = len(resumes) * len(jobs)
    current = 0

    print(f"Matching {len(resumes)} resumes against {len(jobs)} jobs ({total_comparisons} comparisons)...")

    for resume in resumes:
        for job in jobs:
            current += 1
            if current % 10 == 0 or current == total_comparisons:
                print(f"Progress: {current}/{total_comparisons}")

            # Match resume to job
            match_result = matcher.match_resume_to_job(resume, job)

            # Optionally enhance with AI
            if ai_assistant.enabled:
                # In a full implementation, we'd enhance various aspects
                pass

            matches.append(match_result)

    return matches


def generate_reports(resumes: List[Resume], jobs: List[Job], matches: List[MatchResult], file_manager: FileManager):
    """
    Generate reports based on the matching results.

    Args:
        resumes: List of resume objects
        jobs: List of job objects
        matches: List of match results
        file_manager: FileManager instance for saving reports
    """
    config = get_config()
    reporter = Reporter(file_manager)

    # Generate console report
    if config.get("generate_console_report", True):
        console_report = reporter.generate_console_report(resumes, jobs, matches)
        print("\n" + "="*60)
        print("CONSOLE REPORT PREVIEW")
        print("="*60)
        # Show first 20 lines of console report
        lines = console_report.split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print("... (truncated)")

        # Save to file
        console_filename = config.get("console_report_filename", "hiring_report_console.txt")
        if reporter.write_console_report(console_report, console_filename):
            print(f"\nConsole report saved to: {file_manager.output_dir / console_filename}")

    # Generate JSON report
    if config.get("generate_json_report", True):
        json_data = reporter.generate_json_report(resumes, jobs, matches)
        json_filename = config.get("json_report_filename", "hitting_report_data.json")
        if reporter.write_json_report(json_data, json_filename):
            print(f"JSON report saved to: {file_manager.output_dir / json_filename}")

    # Generate sample detailed report for top match
    if config.get("generate_text_report", True) and matches:
        # Find top match
        top_match = max(matches, key=lambda m: m.overall_score)
        resume = next((r for r in resumes if get_resume_id(r) == top_match.resume_id), None)
        job = next((j for j in jobs if get_job_id(j) == top_match.job_id), None)

        if resume and job:
            text_report = reporter.generate_text_report(resume, job, top_match)
            text_filename = config.get("text_report_filename", "hiring_report_detailed.txt")
            if reporter.write_text_report(text_report, text_filename):
                print(f"Detailed report saved to: {file_manager.output_dir / text_filename}")


def get_resume_id(resume: Resume) -> str:
    """Generate a unique ID for a resume."""
    if resume.file_source:
        import os
        return os.path.splitext(os.path.basename(resume.file_source))[0]
    return re.sub(r'[^\w\-_]', '_', resume.name.lower()) or "unknown_resume"


def get_job_id(job: Job) -> str:
    """Generate a unique ID for a job."""
    company_part = re.sub(r'[^\w\-_]', '_', job.company.lower())
    title_part = re.sub(r'[^\w\-_]', '_', job.title.lower())
    return f"{company_part}_{title_part}" or "unknown_job"


def create_sample_data():
    """Create sample resume and job data for demonstration."""
    import os
    from pathlib import Path

    config = get_config()
    resumes_dir = Path(config.get("resumes_directory"))
    jobs_dir = Path(config.get("jobs_directory"))

    # Create directories if they don't exist
    resumes_dir.mkdir(parents=True, exist_ok=True)
    jobs_dir.mkdir(parents=True, exist_ok=True)

    # Sample resumes
    sample_resumes = [
        {
            "filename": "alice_smith_resume.txt",
            "content": """Alice Smith
alice.smith@email.com | (555) 123-4567 | linkedin.com/in/alicesmith | github.com/alicesmith

SUMMARY
Experienced software engineer with 5 years of expertise in full-stack development, specializing in Python, JavaScript, and cloud technologies.

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, SQL, Git, Agile, REST APIs, Machine Learning

WORK EXPERIENCE
Senior Software Engineer | Tech Innovations Inc.
January 2020 - Present
- Developed scalable web applications using Python/Django and React
- Led a team of 4 engineers in implementing microservices architecture
- Reduced application latency by 40% through optimization and caching
- Implemented CI/CD pipelines using Docker and Kubernetes

Software Engineer | StartupXYZ
June 2017 - December 2019
- Built RESTful APIs using Python/Flask and PostgreSQL
- Developed frontend components with React and Redux
- Collaborated with UX designers to improve user experience
- Participated in code reviews and agile ceremonies

EDUCATION
Master of Science in Computer Science
University of Technology, 2017
GPA: 3.8/4.0

Bachelor of Science in Software Engineering
State University, 2015
GPA: 3.6/4.0

CERTIFICATIONS
AWS Certified Solutions Architect
Docker Certified Associate
"""
        },
        {
            "filename": "bob_johnson_resume.txt",
            "content": """Bob Johnson
bob.johnson@email.com | (555) 987-6543 | linkedin.com/in/bobjohnson

SUMMARY
Data scientist with 3 years of experience in machine learning, data analysis, and statistical modeling.

SKILLS
Python, R, SQL, Machine Learning, Deep Learning, TensorFlow, PyTorch, Pandas, NumPy, Scikit-learn, Tableau, Power BI, Statistics

WORK EXPERIENCE
Data Scientist | DataDriven Corp.
March 2021 - Present
- Developed predictive models for customer churn prediction (92% accuracy)
- Created data pipelines using Python and AWS Glue
- Built interactive dashboards using Tableau and Power BI
- Presented findings to stakeholders and executive team

Machine Learning Engineer | AI Solutions Ltd.
August 2019 - February 2021
- Implemented recommendation systems using collaborative filtering
- Conducted A/B testing and statistical analysis
- Optimized model performance using hyperparameter tuning
- Published 2 research papers in ML conferences

EDUCATION
Master of Science in Data Science
Tech Institute, 2019
GPA: 3.9/4.0

Bachelor of Science in Mathematics
College of Science, 2017
GPA: 3.7/4.0

CERTIFICATIONS
Google Cloud Professional Data Engineer
Microsoft Certified: Azure AI Engineer Associate
"""
        },
        {
            "filename": "carol_davis_resume.txt",
            "content": """Carol Davis
carol.davis@email.com | (555) 456-7890 | github.com/caroldavis

SUMMARY
DevOps engineer with 4 years of experience in cloud infrastructure, automation, and CI/CD pipelines.

SKILLS
AWS, Azure, Docker, Kubernetes, Jenkins, GitLab CI, Terraform, Ansible, Linux, Bash, Python, Monitoring, Prometheus, Grafana

WORK EXPERIENCE
DevOps Engineer | CloudNative Systems
May 2020 - Present
- Designed and implemented CI/CD pipelines for microservices
- Managed Kubernetes clusters on AWS EKS and Azure AKS
- Infrastructure as Code using Terraform and Ansible
- Monitoring and logging with Prometheus, Grafana, and ELK stack

System Administrator | HostingPro Inc.
January 2018 - April 2020
- Maintained Linux and Windows servers in datacenter environment
- Automated routine tasks using Bash and Python scripts
- Implemented backup and disaster recovery solutions
- Provided technical support to internal teams

EDUCATION
Bachelor of Science in Information Technology
Technical College, 2018
GPA: 3.5/4.0

CERTIFICATIONS
Certified Kubernetes Administrator (CKA)
AWS Certified DevOps Engineer
HashiCorp Certified: Terraform Associate
"""
        }
    ]

    # Sample jobs
    sample_jobs = [
        {
            "filename": "senior_python_engineer_job.txt",
            "content": """Senior Python Engineer
Tech Innovations Inc.
Location: San Francisco, CA
Employment Type: Full-time

JOB DESCRIPTION
We are seeking a Senior Python Engineer to join our growing team. You will be responsible for developing and maintaining our core backend systems and APIs.

REQUIRED SKILLS
Python, Django, REST APIs, PostgreSQL, Docker, AWS, Git, Agile Methodologies

PREFERRED SKILLS
React, Kubernetes, Machine Learning, Redis, Elasticsearch

EXPERIENCE LEVEL
Senior (5+ years)

MINIMUM YEARS OF EXPERIENCE
5

RESPONSIBILITIES
- Design and implement backend services using Python/Django
- Develop and maintain RESTful APIs for frontend consumption
- Optimize database queries and application performance
- Collaborate with cross-functional teams to deliver features
- Mentor junior engineers and conduct code reviews
"""
        },
        {
            "filename": "data_scientist_job.txt",
            "content": """Data Scientist
DataDriven Corp.
Location: New York, NY (Remote Available)
Employment Type: Full-time

JOB DESCRIPTION
Join our data science team to build machine learning models that drive business decisions and product improvements.

REQUIRED SKILLS
Python, Machine Learning, SQL, Pandas, Scikit-learn, Statistics, Data Visualization

PREFERRED SKILLS
Deep Learning, TensorFlow, PyTorch, Spark, AWS, Tableau, Power BI

EXPERIENCE LEVEL
Mid-level (2-4 years)

MINIMUM YEARS OF EXPERIENCE
2

RESPONSIBILITIES
- Develop machine learning models for prediction and classification
- Clean, preprocess, and analyze large datasets
- Create data pipelines and ETL processes
- Communicate insights to stakeholders through reports and presentations
- Stay updated with latest ML techniques and technologies
"""
        },
        {
            "filename": "devops_engineer_job.txt",
            "content": """DevOps Engineer
CloudNative Systems
Location: Seattle, WA
Employment Type: Full-time

JOB DESCRIPTION
We are looking for a DevOps Engineer to help us scale our infrastructure and improve our deployment processes.

REQUIRED SKILLS
AWS, Docker, Kubernetes, Jenkins, Terraform, Linux, Bash, Python, Monitoring

PREFERRED SKILLS
Azure, GitLab CI, Prometheus, Grafana, Helm, Istio, CloudFormation

EXPERIENCE LEVEL
Mid-level (3-5 years)

MINIMUM YEARS OF EXPERIENCE
3

RESPONSIBILITIES
- Design, implement, and manage CI/CD pipelines
- Maintain and optimize cloud infrastructure on AWS
- Implement Infrastructure as Code using Terraform
- Monitor system performance and troubleshoot issues
- Collaborate with development teams to improve deployment frequency
"""
        }
    ]

    # Write sample resumes
    for resume in sample_resumes:
        file_path = resumes_dir / resume["filename"]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(resume["content"])
            print(f"Created sample resume: {file_path}")
        except Exception as e:
            print(f"Error creating resume {file_path}: {e}")

    # Write sample jobs
    for job in sample_jobs:
        file_path = jobs_dir / job["filename"]
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(job["content"])
            print(f"Created sample job: {file_path}")
        except Exception as e:
            print(f"Error creating job {file_path}: {e}")

    print(f"\nSample data created in {resumes_dir} and {jobs_dir}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Smart Hiring Assistant")
    parser.add_argument(
        "--create-sample-data",
        action="store_true",
        help="Create sample resume and job data"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--no-samples",
        action="store_true",
        help="Skip creating sample data even if directories are empty"
    )

    args = parser.parse_args()

    # Initialize configuration
    if args.config_file:
        init_config(args.config_file)

    # Setup logging
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting Smart Hiring Assistant")

    config = get_config()

    # Create sample data if requested or if directories are empty
    if args.create_sample_data:
        print("Creating sample data...")
        create_sample_data()
    elif not args.no_samples:
        # Check if data directories exist and have files
        file_manager = FileManager(
            config.get("resumes_directory"),
            config.get("jobs_directory"),
            config.get("output_directory")
        )

        resume_files = file_manager.list_resume_files()
        job_files = file_manager.list_job_files()

        if len(resume_files) == 0 or len(job_files) == 0:
            print("No sample data found. Creating sample data...")
            create_sample_data()
        else:
            print(f"Found {len(resume_files)} resume files and {len(job_files)} job files.")

    # Initialize file manager
    file_manager = FileManager(
        config.get("resumes_directory"),
        config.get("jobs_directory"),
        config.get("output_directory")
    )

    # Load data
    print("\nLoading resumes...")
    resumes = load_resumes(file_manager)

    print("\nLoading jobs...")
    jobs = load_jobs(file_manager)

    if not resumes:
        print("Warning: No resumes loaded. Please check your data directory.")
        return 1

    if not jobs:
        print("Warning: No jobs loaded. Please check your data directory.")
        return 1

    print(f"\nLoaded {len(resumes)} resumes and {len(jobs)} jobs.")

    # Run matching engine
    print("\nRunning matching engine...")
    matches = run_matching_engine(resumes, jobs)

    # Generate reports
    print("\nGenerating reports...")
    generate_reports(resumes, jobs, matches, file_manager)

    # Print summary
    strong_matches = [m for m in matches if m.is_strong_match()]
    medium_matches = [m for m in matches if m.is_medium_match()]
    weak_matches = [m for m in matches if m.is_weak_match()]

    print("\n" + "="*60)
    print("MATCHING COMPLETE")
    print("="*60)
    print(f"Total comparisons: {len(matches)}")
    print(f"Strong matches (>=80%): {len(strong_matches)}")
    print(f"Medium matches (60-79%): {len(medium_matches)}")
    print(f"Weak matches (<60%): {len(weak_matches)}")

    if matches:
        avg_score = sum(m.overall_score for m in matches) / len(matches)
        print(f"Average match score: {avg_score:.1f}%")

        if strong_matches:
            top_match = max(matches, key=lambda m: m.overall_score)
            top_resume = next((r for r in resumes if get_resume_id(r) == top_match.resume_id), None)
            top_job = next((j for j in jobs if get_job_id(j) == top_match.job_id), None)
            if top_resume and top_job:
                print(f"\nTop match: {top_resume.name} -> {top_job.title} ({top_match.overall_score:.1f}%)")

    print(f"\nReports saved to: {file_manager.output_dir}")
    logger.info("Smart Hiring Assistant completed successfully")

    return 0


if __name__ == "__main__":
    sys.exit(main())