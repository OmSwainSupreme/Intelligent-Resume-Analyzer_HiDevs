"""
Configuration management for the Smart Hiring Assistant.
Handles application settings and configuration options.
"""

from typing import Dict, Any, Optional
import os
from pathlib import Path
import json


class Config:
    """Configuration manager for the Smart Hiring Assistant."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the Config manager.

        Args:
            config_file: Path to configuration file (JSON format)
        """
        self.config_file = Path(config_file) if config_file else None
        self.config: Dict[str, Any] = {}
        self._load_defaults()

        if self.config_file and self.config_file.exists():
            self.load_from_file()

    def _load_defaults(self):
        """Load default configuration values."""
        self.config = {
            # Matching weights
            "skill_weight": 0.6,
            "experience_weight": 0.4,

            # Scoring thresholds
            "strong_match_threshold": 80.0,
            "medium_match_low": 60.0,
            "medium_match_high": 80.0,

            # File paths
            "resumes_directory": "data/resumes",
            "jobs_directory": "data/jobs",
            "output_directory": "output",

            # Report settings
            "generate_console_report": True,
            "generate_text_report": True,
            "generate_json_report": True,
            "console_report_filename": "hiring_report_console.txt",
            "text_report_filename": "hiring_report_detailed.txt",
            "json_report_filename": "hiring_report_data.json",

            # AI Assistant settings
            "ai_enabled": False,
            "ai_provider": "none",  # openai, anthropic, local, none

            # Parsing settings
            "max_resume_length": 50000,  # characters
            "skills_case_sensitive": False,

            # Experience calculation
            "assume_experience_per_entry": 1.5,  # years per experience entry if dates unclear

            # Display settings
            "top_matches_to_show": 10,
            "include_weak_matches": False,

            # Logging
            "log_level": "INFO",
            "log_to_file": False,
            "log_filename": "smart_hiring_assistant.log"
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple configuration values.

        Args:
            updates: Dictionary of key-value pairs to update
        """
        self.config.update(updates)

    def load_from_file(self, config_file: Optional[str] = None) -> bool:
        """
        Load configuration from a JSON file.

        Args:
            config_file: Path to config file (uses instance config_file if not provided)

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(config_file) if config_file else self.config_file
        if not file_path or not file_path.exists():
            logger.warning(f"Configuration file not found: {file_path}")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # Update config with file values
            self.config.update(file_config)
            logger.info(f"Loaded configuration from {file_path}")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            return False

    def save_to_file(self, config_file: Optional[str] = None) -> bool:
        """
        Save configuration to a JSON file.

        Args:
            config_file: Path to config file (uses instance config_file if not provided)

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(config_file) if config_file else self.config_file
        if not file_path:
            logger.error("No configuration file specified")
            return False

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, sort_keys=True)

            logger.info(f"Saved configuration to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {e}")
            return False

    def get_matching_weights(self) -> tuple[float, float]:
        """
        Get the matching weights for skills and experience.

        Returns:
            Tuple of (skill_weight, experience_weight)
        """
        skill_weight = self.get("skill_weight", 0.6)
        experience_weight = self.get("experience_weight", 0.4)

        # Normalize to ensure they sum to 1.0
        total = skill_weight + experience_weight
        if abs(total - 1.0) > 0.001:
            skill_weight = skill_weight / total
            experience_weight = experience_weight / total

        return skill_weight, experience_weight

    def is_ai_enabled(self) -> bool:
        """Check if AI enhancement is enabled."""
        return self.get("ai_enabled", False)

    def get_ai_provider(self) -> str:
        """Get the AI provider name."""
        return self.get("ai_provider", "none")

    def to_dict(self) -> Dict[str, Any]:
        """
        Get a copy of the full configuration.

        Returns:
            Dictionary containing all configuration values
        """
        return self.config.copy()


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Global Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def init_config(config_file: Optional[str] = None) -> Config:
    """
    Initialize the global configuration.

    Args:
        config_file: Path to configuration file

    Returns:
        Initialized Config instance
    """
    global _config_instance
    _config_instance = Config(config_file)
    return _config_instance


# Set up logging for config module
import logging
logger = logging.getLogger(__name__)


def setup_logging():
    """Set up logging configuration based on config settings."""
    config = get_config()
    log_level = config.get("log_level", "INFO")
    log_to_file = config.get("log_to_file", False)
    log_filename = config.get("log_filename", "smart_hiring_assistant.log")

    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if enabled
    if log_to_file:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


if __name__ == "__main__":
    # Test the configuration system
    config = Config()

    print("Default Configuration:")
    print(f"Skill weight: {config.get('skill_weight')}")
    print(f"Experience weight: {config.get('experience_weight')}")
    print(f"AI enabled: {config.get('ai_enabled')}")
    print(f"Resumes directory: {config.get('resumes_directory')}")

    # Test getting matching weights
    skill_w, exp_w = config.get_matching_weights()
    print(f"Normalized weights - Skill: {skill_w:.2f}, Experience: {exp_w:.2f}")

    # Test updating config
    config.set("skill_weight", 0.7)
    config.set("ai_enabled", True)
    config.set("ai_provider", "openai")

    print("\nAfter Updates:")
    print(f"Skill weight: {config.get('skill_weight')}")
    print(f"AI enabled: {config.get('ai_enabled')}")
    print(f"AI provider: {config.get('ai_provider')}")

    # Test saving and loading
    test_config_path = "test_config.json"
    if config.save_to_file(test_config_path):
        print(f"\nSaved configuration to {test_config_path}")

        # Load into new config instance
        config2 = Config(test_config_path)
        print(f"Loaded skill weight: {config2.get('skill_weight')}")
        print(f"Loaded AI enabled: {config2.get('ai_enabled')}")

        # Clean up
        import os
        if os.path.exists(test_config_path):
            os.remove(test_config_path)