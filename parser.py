"""
Resume parser for the Smart Hiring Assistant.
Extracts structured information from text resumes using regex and string operations.
XXX
"""

import re
from typing import List, Optional
from models import Resume, ContactInfo, WorkExperience, Education
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeParser:
    """Parses text resumes into structured Resume objects."""

    def __init__(self):
        """Initialize the resume parser with regex patterns."""
        # Common regex patterns for resume parsing
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

        # Section headers commonly found in resumes
        self.section_headers = {
            'skills': r'(?i)(?:skills?|technical\s+skills?|competencies?|technologies?|tools?)',
            'experience': r'(?i)(?:experience|work\s+history|employment|professional\s+experience)',
            'education': r'(?i)(?:education|academic\s+background|qualifications)',
            'certifications': r'(?i)(?:certifications?|certificates?|licenses?)',
            'summary': r'(?i)(?:summary|profile|objective|about\s+me)'
        }

        # Common skill keywords for extraction
        self.common_skills = [
            'python', 'java', 'javascript', 'typescript', 'html', 'css', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'spring', 'sql', 'nosql', 'mongodb', 'postgresql',
            'mysql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'jenkins',
            'machine learning', 'ai', 'data science', 'analytics', 'tableau', 'power bi',
            'excel', 'word', 'powerpoint', 'photoshop', 'illustrator', 'figma', 'sketch',
            'project management', 'agile', 'scrum', 'jira', 'trello', 'asana',
            'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking'
        ]

    def parse_resume(self, text: str, file_source: str = "") -> Resume:
        """
        Parse resume text into a structured Resume object.

        Args:
            text: Raw resume text
            file_source: Source file path for tracking

        Returns:
            Parsed Resume object
        """
        logger.info(f"Parsing resume from {file_source if file_source else 'provided text'}")

        # Clean the text
        cleaned_text = self._clean_text(text)

        # Extract contact information
        contact_info = self._extract_contact_info(cleaned_text)

        # Extract name (usually at the beginning)
        name = self._extract_name(cleaned_text)

        # Extract sections
        skills = self._extract_skills(cleaned_text)
        work_experience = self._extract_work_experience(cleaned_text)
        education = self._extract_education(cleaned_text)
        certifications = self._extract_certifications(cleaned_text)

        # Create Resume object
        resume = Resume(
            name=name,
            contact_info=contact_info,
            skills=skills,
            work_experience=work_experience,
            education=education,
            certifications=certifications,
            raw_text=text,
            file_source=file_source
        )

        logger.info(f"Parsed resume for {resume.name}: {len(resume.skills)} skills, "
                   f"{len(resume.work_experience)} experiences, {len(resume.education)} educations")

        return resume

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize resume text.

        Args:
            text: Raw resume text

        Returns:
            Cleaned text
        """
        # Split into lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            # Replace multiple spaces/tabs with single space
            line = re.sub(r'[ \t]+', ' ', line)
            if line:  # Only keep non-empty lines
                cleaned_lines.append(line)
        # Join with single newline
        return '\n'.join(cleaned_lines)

    def _extract_contact_info(self, text: str) -> ContactInfo:
        """
        Extract contact information from resume text.

        Args:
            text: Resume text

        Returns:
            ContactInfo object
        """
        contact_info = ContactInfo()

        # Extract email
        email_matches = re.findall(self.email_pattern, text)
        if email_matches:
            contact_info.email = email_matches[0].lower()

        # Extract phone
        phone_matches = re.findall(self.phone_pattern, text)
        if phone_matches:
            contact_info.phone = phone_matches[0]  # Keep original formatting

        # TODO: Extract LinkedIn, GitHub, etc.
        # For now, look for common patterns
        linkedin_match = re.search(r'(?i)linkedin:\s*(.+)', text)
        if linkedin_match:
            contact_info.linkedin = linkedin_match.group(1).strip()
        else:
            in_match = re.search(r'in/\s*(.+)', text)
            if in_match:
                contact_info.linkedin = in_match.group(1).strip()

        github_pattern = r'(?i)(?:github:\s*|https?://github\.com/)'
        github_match = re.search(github_pattern, text)
        if github_match:
            # Extract everything after the GitHub prefix
            match_start = github_match.end()
            contact_info.github = text[match_start:].strip()

        return contact_info

    def _extract_name(self, text: str) -> str:
        """
        Extract name from resume text.
        Assumes name is at the beginning of the resume.

        Args:
            text: Resume text

        Returns:
            Extracted name
        """
        lines = text.split('\n')
        if not lines:
            return ""

        # Look for name in first few non-empty lines
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50 and not re.match(r'^\d+$', line):  # Not just numbers
                # Skip lines that look like contact info or section headers
                if not (re.search(self.email_pattern, line) or
                       re.search(self.phone_pattern, line) or
                       any(re.search(pattern, line, re.IGNORECASE)
                           for pattern in self.section_headers.values())):
                    # This looks like a name
                    return line

        # Fallback: return first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()

        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract skills from resume text.

        Args:
            text: Resume text

        Returns:
            List of skills
        """
        skills = set()  # Use set to avoid duplicates

        # Find skills section
        skills_section = self._extract_section(text, self.section_headers['skills'])
        if skills_section:
            # Extract skills from the skills section
            skills.update(self._extract_skills_from_text(skills_section))
        else:
            # If no explicit skills section, scan entire text
            skills.update(self._extract_skills_from_text(text))

        # Also look for skills in experience descriptions
        experience_section = self._extract_section(text, self.section_headers['experience'])
        if experience_section:
            skills.update(self._extract_skills_from_text(experience_section))

        return sorted(list(skills))

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from a block of text.

        Args:
            text: Text to search for skills

        Returns:
            List of found skills
        """
        found_skills = []
        text_lower = text.lower()

        # Check for each common skill
        for skill in self.common_skills:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(skill)}\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)

        # Also look for skill-like patterns (comma-separated lists, bullet points)
        # Split by common delimiters and check each item
        lines = re.split(r'[,;\n\-\•]', text)
        for line in lines:
            line = line.strip()
            if line and len(line) < 50 and len(line.split()) <= 4:  # Likely a skill
                # Check if it's not just a number or date
                if not re.match(r'^[\d\s\-\/\.]+$', line):
                    found_skills.append(line.lower())

        return list(set(found_skills))  # Remove duplicates

    def _extract_section(self, text: str, section_pattern: str) -> Optional[str]:
        """
        Extract a section from resume text based on header pattern.

        Args:
            text: Resume text
            section_pattern: Regex pattern for the section header

        Returns:
            Section content or None if not found
        """
        # Find the section header
        header_match = re.search(section_pattern, text)
        if not header_match:
            return None

        # Get the start position (after the header)
        start_pos = header_match.end()

        # Find the next section header or end of text
        next_section_pos = len(text)
        for pattern in self.section_headers.values():
            if pattern != section_pattern:  # Don't match the same section
                next_match = re.search(pattern, text[start_pos:])
                if next_match:
                    pos = start_pos + next_match.start()
                    if pos < next_section_pos:
                        next_section_pos = pos

        # Extract the section content
        section_content = text[start_pos:next_section_pos].strip()
        return section_content if section_content else None

    def _extract_work_experience(self, text: str) -> List[WorkExperience]:
        """
        Extract work experience from resume text.

        Args:
            text: Resume text

        Returns:
            List of WorkExperience objects
        """
        experience_list = []

        # Extract experience section
        experience_section = self._extract_section(text, self.section_headers['experience'])
        if not experience_section:
            return experience_list

        # Split into individual experience entries
        # Look for patterns like company names, dates, titles
        experience_blocks = self._split_experience_blocks(experience_section)

        for block in experience_blocks:
            experience = self._parse_experience_block(block)
            if experience:
                experience_list.append(experience)

        return experience_list

    def _split_experience_blocks(self, text: str) -> List[str]:
        """
        Split experience section into individual experience blocks.

        Args:
            text: Experience section text

        Returns:
            List of experience blocks
        """
        # Simple approach: split by double newline or clear delimiters
        blocks = re.split(r'\n\s*\n', text)
        # Filter out empty blocks and those that are too short
        blocks = [block.strip() for block in blocks if block.strip() and len(block.strip()) > 20]
        return blocks

    def _parse_experience_block(self, block: str) -> Optional[WorkExperience]:
        """
        Parse a single experience block into a WorkExperience object.

        Args:
            block: Text block representing one experience

        Returns:
            WorkExperience object or None if parsing fails
        """
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            return None

        # Initialize title and company
        title = ""
        company = ""
        start_index = 0

        # Check if first line contains both title and company (using existing logic)
        if len(lines) >= 1:
            title, company = self._extract_title_and_company(lines[0])
            # If we got a company, then we assume title and company are on the first line
            if company:
                start_index = 1
            else:
                # If no company found in first line, check second line for company
                if len(lines) >= 2:
                    # Second line might be the company (possibly with date)
                    company_line = lines[1]
                    # Try to split by common separators to get the company name
                    for sep in [' | ', ' - ', ',']:
                        if sep in company_line:
                            company = company_line.split(sep)[0].strip()
                            break
                    else:
                        company = company_line.strip()
                    start_index = 2
                else:
                    # Only one line, title is that line, company unknown
                    title = lines[0]
                    start_index = 1

        # If we still don't have a title, try to extract from first line again (without company)
        if not title and len(lines) >= 1:
            title = lines[0]
            start_index = 1

        # Try to extract dates
        start_date, end_date = self._extract_dates(block)

        # Description is everything else after the title/company lines
        description_lines = lines[start_index:] if start_index < len(lines) else []
        description = '\n'.join(description_lines)

        # Extract skills used in this experience
        skills_used = self._extract_skills_from_text(block)

        return WorkExperience(
            title=title,
            company=company,
            start_date=start_date,
            end_date=end_date,
            description=description,
            skills_used=skills_used
        )

    def _extract_title_and_company(self, line: str) -> tuple[str, str]:
        """
        Extract job title and company from a line.

        Args:
            line: Text line containing title and company

        Returns:
            Tuple of (title, company)
        """
        # Common patterns: "Title at Company" or "Title, Company" or "Title - Company"
        patterns = [
            r'^(.+?)\s+(?:at|@)\s+(.+)$',
            r'^(.+?),\s*(.+)$',
            r'^(.+?)\s+-\s*(.+)$',
            r'^(.+?)\s+\|\s*(.+)$'
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                company = match.group(2).strip()
                return title, company

        # If no pattern matches, assume the whole line is title
        return line.strip(), ""

    def _extract_dates(self, text: str) -> tuple[str, str]:
        """
        Extract start and end dates from text.

        Args:
            text: Text to search for dates

        Returns:
            Tuple of (start_date, end_date)
        """
        # Date patterns: "Jan 2020 - Dec 2022", "2020-2022", "Jan 2020 - Present"
        date_patterns = [
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|present|current)',
            r'(\d{4})\s*[-–]\s*(\d{4}|present|current)',
            r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4})',
            r'(\d{4})\s*[-–]\s*(\d{4})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_date = match.group(1).strip()
                end_date = match.group(2).strip()
                return start_date, end_date

        return "", ""

    def _extract_education(self, text: str) -> List[Education]:
        """
        Extract education from resume text.

        Args:
            text: Resume text

        Returns:
            List of Education objects
        """
        education_list = []

        # Extract education section
        education_section = self._extract_section(text, self.section_headers['education'])
        if not education_section:
            return education_list

        # Split into individual education entries
        education_blocks = re.split(r'\n\s*\n', education_section)
        education_blocks = [block.strip() for block in education_blocks if block.strip()]

        for block in education_blocks:
            education = self._parse_education_block(block)
            if education:
                education_list.append(education)

        return education_list

    def _parse_education_block(self, block: str) -> Optional[Education]:
        """
        Parse a single education block into an Education object.

        Args:
            block: Text block representing one education entry

        Returns:
            Education object or None if parsing fails
        """
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            return None

        degree = ""
        institution = ""
        start_index = 0

        # Check if we have at least two lines
        if len(lines) >= 1:
            degree, institution = self._extract_degree_and_institution(lines[0])
            # If institution looks like a degree (contains degree keywords),
            # we likely mis-parsed; treat first line as degree and look for institution in second line
            degree_keywords = ['bachelor', 'master', 'phd', 'doctor', 'associate', 'b.s.', 'm.s.', 'b.a.', 'm.a.']
            if institution and any(keyword in institution.lower() for keyword in degree_keywords):
                # Mis-parsed: the first line is actually the degree, and we haven't found institution yet
                degree = institution
                institution = ""
            if institution:
                start_index = 1
            else:
                # If no institution found in first line, check second line
                if len(lines) >= 2:
                    # Second line might be the institution (possibly with graduation year or other info)
                    institution_line = lines[1]
                    # Try to split by common separators to get the institution name
                    for sep in [' | ', ' - ', ',']:
                        if sep in institution_line:
                            institution = institution_line.split(sep)[0].strip()
                            break
                    else:
                        institution = institution_line.strip()
                    start_index = 2
                else:
                    # Only one line, assume it's the institution
                    institution = lines[0]
                    start_index = 1

        # If we still don't have an institution, use the first line as institution
        if not institution and len(lines) >= 1:
            institution = lines[0]
            start_index = 1

        # Try to extract graduation year
        graduation_year = self._extract_graduation_year(block)

        # Extract GPA if present
        gpa = self._extract_gpa(block)

        # Relevant coursework
        relevant_coursework = self._extract_relevant_coursework(block)

        return Education(
            degree=degree,
            institution=institution,
            graduation_year=graduation_year,
            gpa=gpa,
            relevant_coursework=relevant_coursework
        )

    def _extract_degree_and_institution(self, line: str) -> tuple[str, str]:
        """
        Extract degree and institution from a line.

        Args:
            line: Text line containing degree and institution

        Returns:
            Tuple of (degree, institution)
        """
        # Common patterns: "Bachelor of Science in Computer Science, University XYZ"
        # or "University XYZ - Bachelor of Arts"
        patterns = [
            r'^(.+?),\s*(.+)$',  # Degree, Institution
            r'^(.+?)\s+-\s*(.+)$',  # Institution - Degree
            r'^(.+?)\s+(?:at|@)\s+(.+)$'  # Degree at Institution
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                part1 = match.group(1).strip()
                part2 = match.group(2).strip()

                # Heuristic: if part1 contains degree-like words, it's the degree
                degree_keywords = ['bachelor', 'master', 'phd', 'doctor', 'associate', 'b.s.', 'm.s.', 'b.a.', 'm.a.']
                if any(keyword in part1.lower() for keyword in degree_keywords):
                    return part1, part2
                else:
                    return part2, part1

        # If no pattern matches, return the line as institution
        return "", line.strip()

    def _extract_graduation_year(self, text: str) -> str:
        """
        Extract graduation year from text.

        Args:
            text: Text to search for graduation year

        Returns:
            Graduation year string
        """
        # Look for 4-digit years
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        if year_matches:
            # Return the last year found (likely graduation)
            return year_matches[-1]
        return ""

    def _extract_gpa(self, text: str) -> str:
        """
        Extract GPA from text.

        Args:
            text: Text to search for GPA

        Returns:
            GPA string
        """
        # Look for GPA patterns like "GPA: 3.5/4.0" or "3.5 GPA"
        gpa_patterns = [
            r'gpa[:\s]+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*gpa',
            r'(\d+\.?\d*)\s*/\s*4\.0'
        ]

        for pattern in gpa_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _extract_relevant_coursework(self, text: str) -> List[str]:
        """
        Extract relevant coursework from text.

        Args:
            text: Text to search for coursework

        Returns:
            List of coursework strings
        """
        coursework = []

        # Look for "Relevant Coursework:" section
        coursework_match = re.search(r'(?i)relevant\s+coursework[:]\s*(.+)$', text)
        if coursework_match:
            coursework_text = coursework_match.group(1)
            # Split by common delimiters: comma, semicolon, newline, hyphen, bullet point
            items = re.split(r'[,;\n\-•]', coursework_text)
            coursework = [item.strip() for item in items if item.strip()]

        return coursework

    def _extract_certifications(self, text: str) -> List[str]:
        """
        Extract certifications from resume text.

        Args:
            text: Resume text

        Returns:
            List of certifications
        """
        certifications = []

        # Extract certifications section
        cert_section = self._extract_section(text, self.section_headers['certifications'])
        if cert_section:
            # Split by common delimiters: comma, semicolon, newline, hyphen, bullet point
            lines = re.split(r'[,;\n\-•]', cert_section)
            certifications = [line.strip() for line in lines if line.strip()]

        return certifications