"""Policy search service with best match and keyword highlighting."""
import json
from pathlib import Path
from typing import List, Optional
from app.models import Policy
from app.config import settings


class PolicyService:
    """Service for searching IT policies."""

    def __init__(self):
        """Initialize policy service with data file path."""
        self.policies_file = settings.DATA_DIR / "policies.json"

    def _load_policies(self) -> List[dict]:
        """Load policies from JSON file.

        Returns:
            List of policy dictionaries
        """
        if not self.policies_file.exists():
            return []
        with open(self.policies_file, "r") as f:
            return json.load(f)

    def find_policy(self, topic: Optional[str] = None) -> Optional[Policy]:
        """Find the best matching policy for a given topic.

        Args:
            topic: Policy topic to search for

        Returns:
            Best matching Policy object if found, otherwise None
        """
        policies = self._load_policies()
        if not topic:
            return None

        topic_lower = topic.lower()
        best_match = None
        best_score = 0

        for policy_data in policies:
            score = 0
            matched_keywords = []

            # Check title
            title_lower = policy_data["title"].lower()
            if topic_lower in title_lower:
                score += 3
                matched_keywords.append(topic)

            # Check description
            desc_lower = policy_data["description"].lower()
            if topic_lower in desc_lower:
                score += 2

            if score > best_score:
                best_score = score
                best_match = policy_data
                best_match["matched_keywords"] = matched_keywords

        if best_match:
            return Policy(**best_match)
        return None
