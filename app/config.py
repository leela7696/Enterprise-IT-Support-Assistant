"""Configuration and constants for the Enterprise IT Support Assistant."""
from pydantic_settings import BaseSettings
from pathlib import Path
from enum import Enum


class Settings(BaseSettings):
    """Application settings."""
    APP_TITLE: str = "Enterprise IT Support Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-powered, offline-first IT support assistant that helps users "
        "with ticket creation, status checks, employee lookup, and policy search."
    )
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    LOG_DIR: Path = Path(__file__).parent / "logs"
    DATA_DIR: Path = Path(__file__).parent / "data"


class ErrorCode(str, Enum):
    """Error code enumeration."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Category(str, Enum):
    """Ticket category enumeration."""
    NETWORK = "Network"
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    ACCOUNT = "Account"
    OTHER = "Other"


class AssignedTeam(str, Enum):
    """Assigned team enumeration."""
    IT_INFRASTRUCTURE = "IT Infrastructure"
    END_USER_SUPPORT = "End User Support"
    SECURITY = "Security"
    HR = "Human Resources"


# Constants
CONFIDENCE_THRESHOLD = 0.5
MAX_QUESTION_LENGTH = 500
REQUEST_ID_PREFIX = "REQ"

# Initialize settings
settings = Settings()

# Create directories if they don't exist
settings.LOG_DIR.mkdir(exist_ok=True)
settings.DATA_DIR.mkdir(exist_ok=True)
