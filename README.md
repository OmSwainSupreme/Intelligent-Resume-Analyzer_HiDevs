# Smart Hiring Assistant

A Python-based application that automates resume screening and job matching by extracting structured information from resumes, evaluating candidates against job requirements, and generating explainable hiring reports.

## Features

- **Resume Parsing**: Extracts structured data from text resumes using regex and string operations
- **Job Matching**: Calculates match scores based on skills, experience, and qualifications
- **Explainable Scoring**: Provides detailed breakdown of how scores are calculated
- **Multiple Report Formats**: Console, text, and JSON output options
- **Safe File Handling**: Robust file management with error handling
- **Extensible Design**: Modular architecture for easy enhancement
- **Optional AI Integration**: Hooks for AI-powered enhancements (currently rule-based)

## Project Structure

```
smart-hiring-assistant/
├── main.py                    # Entry point with CLI interface
├── models.py                  # Data models (Resume, Job, MatchResult, etc.)
├── parser.py                  # Resume parsing logic
├── matcher.py                 # Job matching algorithm
├── reporter.py                # Report generation
├── file_manager.py            # File management operations
├── ai_assistant.py            # Optional AI assistant interface
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore                 # Git ignore rules
├── data/                      # Sample data directory
│   ├── resumes/               # Sample resume files (.txt)
│   └── jobs/                  # Sample job descriptions
├── output/                    # Generated reports output
└── tests/                     # Unit tests
    ├── test_parser.py
    ├── test_matcher.py
    ├── test_reporter.py
    └── test_file_manager.py
```

## Installation

1. Clone or download this repository
2. Ensure you have Python 3.11+ installed
3. Install dependencies (if any are added):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:
```bash
python main.py
```

The application will:
1. Load sample resumes from `data/resumes/`
2. Load sample job descriptions from `data/jobs/`
3. Parse resumes and extract candidate information
4. Match candidates against job requirements
5. Generate explainable match scores
6. Output hiring reports to the console and/or files

### Command Line Options

- `--create-sample-data`: Force creation of sample data files (useful if directories are empty)
- `--no-samples`: Skip sample data creation even if directories are empty
- `--config-file PATH`: Specify a custom configuration file path

## Data Formats

### Resumes
Place text resumes in the `data/resumes/` directory. The parser expects:
- Contact information (email, phone) at the top
- Clearly labeled sections (Skills, Experience, Education, Certifications)
- Standard resume formatting

### Job Descriptions
Place job descriptions in the `data/jobs/` directory. Each file should contain:
- Job title and company
- Location and employment type
- Required skills and qualifications
- Preferred skills and qualifications
- Experience level requirements
- Minimum years of experience
- Job description text
- Responsibilities

## Output

Reports are generated in the `output/` directory and displayed in the console, including:
- Ranked candidate list
- Match scores with explanations
- Skill gap analysis
- Hiring recommendations

### Report Formats

1. **Console Report** (`hiring_report_console.txt`): Color-coded output with rankings and summary statistics
2. **JSON Report** (`hiring_report_data.json`): Structured data for further processing
3. **Detailed Report** (`hiring_report_detailed.txt`): Comprehensive report for the top candidate match

## Testing

Run unit tests:
```bash
python -m unittest discover tests
```

Or run with verbose output:
```bash
python -m unittest discover tests -v
```

## Configuration

The application uses a JSON configuration file (default: `config.json` in the current directory) to manage:
- Scoring weights (skill_weight, experience_weight)
- Match thresholds (strong_match_threshold, medium_match_threshold)
- File paths (resumes_directory, jobs_directory, output_directory)
- Logging configuration
- AI assistant settings

Example configuration:
```json
{
  "skill_weight": 0.6,
  "experience_weight": 0.4,
  "strong_match_threshold": 80.0,
  "medium_match_threshold": 60.0,
  "resumes_directory": "data/resumes",
  "jobs_directory": "data/jobs",
  "output_directory": "output",
  "log_level": "INFO",
  "ai_enabled": false,
  "ai_provider": "openai",
  "ai_model": "gpt-3.5-turbo"
}
```

## Matching Algorithm

The Smart Hiring Assistant uses an explainable, weighted scoring system:

### Skill Matching (60% weight by default)
- **Required Skills**: Exact matches, fuzzy matches, and related skill variations
- **Preferred Skills**: Bonus points for matching preferred skills
- **Scoring**: 
  - Required skills score = (matched_required / total_required) × 70%
  - Preferred skills score = (matched_preferred / total_preferred) × 30%
  - Final skill score = required skills score + preferred skills score

### Experience Matching (40% weight by default)
- **Years Experience**: Compares candidate's years of experience against job requirements
- **Experience Level**: Matches candidate's level (entry, mid, senior) against job's required level
- **Scoring**:
  - Years score: Based on meeting/exceeding minimum years requirements
  - Level score: Based on how well candidate's experience level matches job's required level
  - Final experience score = (years_score × 0.7) + (level_score × 0.3)

### Overall Score
```
overall_score = (skill_score × skill_weight) + (experience_score × experience_weight)
```

## Python Concepts Demonstrated

This implementation showcases various Python programming concepts:

- **Modular Programming**: Separation of concerns across multiple modules
- **Data Modeling**: Using classes and dataclasses to represent structured data
- **File Handling**: Safe reading/writing operations with proper error handling
- **Regular Expressions**: Pattern matching for text extraction in resume parsing
- **Data Structures**: Lists, dictionaries, and sets for efficient data manipulation
- **Object-Oriented Programming**: Classes with methods and attributes
- **Algorithm Design**: Weighted scoring system with explainable results
- **Configuration Management**: JSON-based configuration with fallback defaults
- **Command-Line Interface**: Argument parsing for flexible execution
- **Testing**: Comprehensive unit test suite for all modules
- **Logging**: Structured logging for debugging and monitoring
- **Type Hints**: Function annotations for better code clarity and IDE support

## Responsible Use Considerations

- Match scores are heuristic decision-support signals, not validated predictions of job performance
- The system focuses on explainable, skill-based matching to promote fair hiring practices
- Users should review explanations and consider multiple factors beyond numerical scores
- The tool is designed to assist human decision-makers, not replace them
- Regular audits should be performed to check for unintended biases in matching results

## Limitations

- Currently supports only plain text (.txt) resume and job files
- PDF and DOCX formats are not supported
- AI integration is currently a placeholder (rule-based only)
- Skill matching uses a predefined dictionary of common skills
- Experience calculation assumes standard date formats in resumes

## Troubleshooting

### Common Issues

1. **No resumes/jobs found**: 
   - Ensure files are placed in the correct directories (`data/resumes/` and `data/jobs/`)
   - Use `--create-sample-data` to generate sample files for testing

2. **Parsing errors**:
   - Resumes should have clearly marked sections (SKILLS, EXPERIENCE, EDUCATION)
   - Contact information should be at the top of the resume
   - Use standard date formats (e.g., "Jan 2020 - Present", "2020-2022")

3. **Low match scores**:
   - Check the explanation section of reports for specific gaps
   - Consider adjusting skill terminology to match common skill names in the parser
   - Review experience level and years requirements in job descriptions

4. **Report generation issues**:
   - Check that the output directory is writable
   - Verify file permissions in the output directory

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

## License

This project is for educational and demonstration purposes.