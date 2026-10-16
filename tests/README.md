# Tests

This directory contains unit tests for the Smart Hiring Assistant.

## Test Modules

- `test_parser.py` - Tests for resume parsing functionality
- `test_matcher.py` - Tests for job matching algorithm
- `test_reporter.py` - Tests for report generation
- `test_integration.py` - Integration tests for the full system

## Running Tests

To run all tests:
```bash
python -m unittest discover tests
```

To run specific test module:
```bash
python -m unittest tests.test_parser
```