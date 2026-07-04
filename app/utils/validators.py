"""Validation functions for user inputs."""
from typing import Optional
import re
from app.config import MAX_QUESTION_LENGTH


def validate_question(question: Optional[str]) -> tuple[bool, Optional[str]]:
    """Validate user question input.
    
    Args:
        question: User's question string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if question is None:
        return False, "Question field is mandatory"
    if not isinstance(question, str):
        return False, "Question must be a string"
    if len(question.strip()) == 0:
        return False, "Question cannot be empty or whitespace only"
    if len(question) > MAX_QUESTION_LENGTH:
        return False, f"Question cannot be longer than {MAX_QUESTION_LENGTH} characters"
    
    # Check for excessive special characters
    special_char_count = len(re.findall(r"[^\w\s,.!?'-]", question))
    if special_char_count > len(question) * 0.3:
        return False, "Question contains too many special characters"
    
    return True, None
