"""
File management utilities for the Smart Hiring Assistant.
Handles safe reading and writing of resume and job files.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for resumes and jobs."""

    def __init__(self, resumes_dir: str = "data/resumes", jobs_dir: str = "data/jobs", output_dir: str = "output"):
        """
        Initialize the FileManager.

        Args:
            resumes_dir: Directory containing resume files
            jobs_dir: Directory containing job description files
            output_dir: Directory for output reports
        """
        self.resumes_dir = Path(resumes_dir)
        self.jobs_dir = Path(jobs_dir)
        self.output_dir = Path(output_dir)

        # Ensure directories exist
        self.resumes_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"FileManager initialized:")
        logger.info(f"  Resumes directory: {self.resumes_dir.absolute()}")
        logger.info(f"  Jobs directory: {self.jobs_dir.absolute()}")
        logger.info(f"  Output directory: {self.output_dir.absolute()}")

    def list_resume_files(self) -> List[Path]:
        """
        List all resume files in the resumes directory.

        Returns:
            List of Path objects for resume files
        """
        resume_files = []
        for ext in ['*.txt', '*.pdf', '*.docx']:
            resume_files.extend(self.resumes_dir.glob(ext))
        logger.info(f"Found {len(resume_files)} resume files")
        return sorted(resume_files)

    def list_job_files(self) -> List[Path]:
        """
        List all job files in the jobs directory.

        Returns:
            List of Path objects for job files
        """
        job_files = []
        for ext in ['*.txt', '*.pdf', '*.docx']:
            job_files.extend(self.jobs_dir.glob(ext))
        logger.info(f"Found {len(job_files)} job files")
        return sorted(job_files)

    def read_text_file(self, file_path: Path) -> Optional[str]:
        """
        Safely read a text file.

        Args:
            file_path: Path to the file to read

        Returns:
            File contents as string, or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path}")
            return content
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except PermissionError:
            logger.error(f"Permission denied reading {file_path}")
            return None
        except UnicodeDecodeError:
            logger.error(f"Unable to decode {file_path} as UTF-8")
            return None
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return None

    def read_resume(self, file_path: Path) -> Optional[str]:
        """
        Read a resume file.

        Args:
            file_path: Path to the resume file

        Returns:
            Resume text content, or None if error
        """
        return self.read_text_file(file_path)

    def read_job(self, file_path: Path) -> Optional[str]:
        """
        Read a job description file.

        Args:
            file_path: Path to the job file

        Returns:
            Job text content, or None if error
        """
        return self.read_text_file(file_path)

    def write_report(self, content: str, filename: str) -> bool:
        """
        Write a report to the output directory.

        Args:
            content: Report content to write
            filename: Name of the output file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Report written to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing report {filename}: {str(e)}")
            return False

    def write_json_report(self, data: Dict, filename: str) -> bool:
        """
        Write a JSON report to the output directory.

        Args:
            data: Data to serialize as JSON
            filename: Name of the output file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"JSON report written to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing JSON report {filename}: {str(e)}")
            return False

    def get_file_stem(self, file_path: Path) -> str:
        """
        Get the stem (filename without extension) of a file.

        Args:
            file_path: Path to the file

        Returns:
            Filename stem
        """
        return file_path.stem