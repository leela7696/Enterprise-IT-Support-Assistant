"""Intent classification service with confidence scoring and keyword matching."""
import re
from typing import Optional, List
from app.models import Intent, IntentClassificationResult


class IntentService:
    """Service for classifying user intents from natural language questions."""

    def __init__(self):
        """Initialize intent service with keyword sets for each intent."""
        # Define keywords with weights for confidence calculation
        self.keyword_config = {
            Intent.CREATE_TICKET: {
                "keywords": [
                    ("vpn", 0.55),
                    ("printer", 0.55),
                    ("laptop", 0.55),
                    ("email", 0.55),
                    ("outlook", 0.55),
                    ("not working", 0.6),
                    ("crashes", 0.6),
                    ("offline", 0.6),
                    ("broken", 0.6),
                    ("issue", 0.4),
                    ("problem", 0.4),
                    ("won't start", 0.7),
                    ("can't connect", 0.6),
                    ("not connecting", 0.6),
                    ("password reset", 0.7)
                ],
                "vague_phrases": ["my system isn't working", "create ticket", "my system is not working"]
            },
            Intent.CHECK_STATUS: {
                "keywords": [
                    ("check ticket", 0.6),
                    ("what is the status", 0.6),
                    ("ticket status", 0.6),
                    ("inc", 0.5),
                    ("status of", 0.5),
                    ("track ticket", 0.55)
                ],
                "vague_phrases": []
            },
            Intent.EMPLOYEE_LOOKUP: {
                "keywords": [
                    ("show employee", 0.6),
                    ("find employee", 0.6),
                    ("employee info", 0.55),
                    ("who is", 0.5)
                ],
                "vague_phrases": []
            },
            Intent.POLICY_SEARCH: {
                "keywords": [
                    ("policy", 0.5),
                    ("password policy", 0.8),
                    ("leave policy", 0.8),
                    ("vpn policy", 0.8),
                    ("remote work policy", 0.8),
                    ("laptop usage policy", 0.8),
                    ("what is the policy", 0.6)
                ],
                "vague_phrases": []
            },
            Intent.GREETING: {
                "keywords": [
                    ("hi", 0.6),
                    ("hello", 0.6),
                    ("good morning", 0.7),
                    ("good afternoon", 0.7),
                    ("good evening", 0.7),
                    ("hey", 0.55)
                ],
                "vague_phrases": []
            }
        }

    def classify_intent(self, question: str) -> IntentClassificationResult:
        """Classify user intent and calculate confidence score.

        Args:
            question: User's natural language question

        Returns:
            IntentClassificationResult with intent, confidence, and matched keywords
        """
        question_lower = question.lower().strip()
        best_intent = Intent.UNKNOWN
        best_confidence = 0.0
        matched_keywords: List[str] = []

        # Check each intent
        for intent, config in self.keyword_config.items():
            current_confidence = 0.0
            current_matched: List[str] = []

            for keyword, weight in config["keywords"]:
                if keyword in question_lower:
                    current_confidence += weight
                    current_matched.append(keyword)

            # Cap confidence at 1.0
            current_confidence = min(current_confidence, 1.0)

            # Update best intent if current is better
            if current_confidence > best_confidence:
                best_confidence = current_confidence
                best_intent = intent
                matched_keywords = current_matched

        return IntentClassificationResult(
            intent=best_intent,
            confidence=best_confidence,
            matched_keywords=matched_keywords
        )

    def extract_ticket_id(self, question: str) -> Optional[str]:
        """Extract ticket ID from question (format: INC followed by numbers).

        Args:
            question: User's question

        Returns:
            Ticket ID if found, otherwise None
        """
        match = re.search(r"INC\d+", question.upper())
        return match.group(0) if match else None

    def extract_employee_name(self, question: str) -> Optional[str]:
        """Extract employee name from question.

        Args:
            question: User's question

        Returns:
            Employee name if found, otherwise None
        """
        question_lower = question.lower()
        keywords = ["employee", "show", "find", "who is"]
        for keyword in keywords:
            if keyword in question_lower:
                parts = question_lower.split(keyword)
                if len(parts) > 1:
                    name_part = parts[1].strip()
                    # Remove any trailing punctuation
                    name_part = re.sub(r'[,.!?]$', '', name_part)
                    if name_part:
                        return name_part.title()
        return None

    def extract_policy_topic(self, question: str) -> Optional[str]:
        """Extract policy topic from question.

        Args:
            question: User's question

        Returns:
            Policy topic if found, otherwise None
        """
        question_lower = question.lower()
        policy_topics = [
            "password",
            "vpn",
            "leave",
            "remote work",
            "laptop usage"
        ]
        for topic in policy_topics:
            if topic in question_lower:
                return topic
        return None

    def is_vague_ticket_request(self, question: str) -> bool:
        """Check if ticket creation request is too vague.

        Args:
            question: User's question

        Returns:
            True if request is vague, otherwise False
        """
        question_lower = question.lower().strip()
        config = self.keyword_config[Intent.CREATE_TICKET]
        return any(phrase in question_lower for phrase in config["vague_phrases"])
