"""Ticket management service with priority, category, and suggested resolutions."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from app.models import Ticket, Priority, Status
from app.config import Category, AssignedTeam, settings


class TicketService:
    """Service for managing IT support tickets."""

    def __init__(self):
        """Initialize ticket service with data file path."""
        self.tickets_file = settings.DATA_DIR / "tickets.json"

    def _load_tickets(self) -> List[dict]:
        """Load tickets from JSON file.

        Returns:
            List of ticket dictionaries
        """
        if not self.tickets_file.exists():
            return []
        with open(self.tickets_file, "r") as f:
            return json.load(f)

    def _save_tickets(self, tickets: List[dict]) -> None:
        """Save tickets to JSON file.

        Args:
            tickets: List of ticket dictionaries to save
        """
        with open(self.tickets_file, "w") as f:
            json.dump(tickets, f, indent=2, default=str)

    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID.

        Returns:
            New ticket ID in format INC followed by number
        """
        tickets = self._load_tickets()
        if not tickets:
            return "INC1001"
        last_id = tickets[-1]["ticket_id"]
        number = int(last_id.replace("INC", ""))
        return f"INC{number + 1}"

    def _determine_priority(self, issue: str) -> Priority:
        """Determine ticket priority based on issue description.

        Args:
            issue: Issue description

        Returns:
            Priority level (High, Medium, Low)
        """
        issue_lower = issue.lower()
        if "laptop won't start" in issue_lower or "laptop not starting" in issue_lower:
            return Priority.HIGH
        if any(keyword in issue_lower for keyword in ["vpn", "printer", "email", "outlook", "internet", "wifi", "monitor", "keyboard", "mouse"]):
            return Priority.MEDIUM
        if "password reset" in issue_lower or "forgot password" in issue_lower:
            return Priority.LOW
        return Priority.MEDIUM

    def _determine_category(self, issue: str) -> str:
        """Determine ticket category based on issue description.

        Args:
            issue: Issue description

        Returns:
            Category string
        """
        issue_lower = issue.lower()
        if any(keyword in issue_lower for keyword in ["vpn", "network", "connect", "wifi"]):
            return Category.NETWORK
        if any(keyword in issue_lower for keyword in ["laptop", "printer", "hardware"]):
            return Category.HARDWARE
        if any(keyword in issue_lower for keyword in ["outlook", "email", "software"]):
            return Category.SOFTWARE
        if any(keyword in issue_lower for keyword in ["password", "account", "login"]):
            return Category.ACCOUNT
        return Category.OTHER

    def _determine_assigned_team(self, category: str) -> str:
        """Determine which team to assign the ticket to.

        Args:
            category: Ticket category

        Returns:
            Assigned team name
        """
        if category == Category.NETWORK:
            return AssignedTeam.IT_INFRASTRUCTURE
        if category == Category.HARDWARE:
            return AssignedTeam.END_USER_SUPPORT
        if category == Category.SOFTWARE:
            return AssignedTeam.END_USER_SUPPORT
        if category == Category.ACCOUNT:
            return AssignedTeam.SECURITY
        return AssignedTeam.END_USER_SUPPORT

    def _get_suggested_resolution(self, issue: str) -> Optional[str]:
        """Get suggested troubleshooting steps based on issue.

        Args:
            issue: Issue description

        Returns:
            Suggested resolution string if available
        """
        issue_lower = issue.lower()
        if "vpn" in issue_lower:
            return "Please reconnect to the VPN and verify your internet connection. If the problem persists, restart your computer."
        if "printer" in issue_lower:
            return "Ensure the printer is powered on, connected to the network, and has paper and toner."
        if "laptop won't start" in issue_lower:
            return "Check if the laptop is plugged in and the battery is charged. Try holding the power button for 10 seconds."
        if "email" in issue_lower or "outlook" in issue_lower:
            return "Restart Outlook and check your internet connection. Verify your password is correct."
        if "password reset" in issue_lower:
            return "Please use the self-service password reset tool on the company portal."
        return None

    def create_ticket(self, issue: str, notes: Optional[str] = None) -> Ticket:
        """Create a new support ticket.

        Args:
            issue: Description of the issue
            notes: Optional additional notes

        Returns:
            Created Ticket object
        """
        ticket_id = self._generate_ticket_id()
        priority = self._determine_priority(issue)
        category = self._determine_category(issue)
        assigned_team = self._determine_assigned_team(category)
        suggested_resolution = self._get_suggested_resolution(issue)

        ticket = Ticket(
            ticket_id=ticket_id,
            issue=issue,
            priority=priority,
            category=category,
            assigned_team=assigned_team,
            status=Status.OPEN,
            created_at=datetime.now(),
            suggested_resolution=suggested_resolution,
            notes=notes
        )

        tickets = self._load_tickets()
        tickets.append(ticket.model_dump())
        self._save_tickets(tickets)

        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a ticket by ID.

        Args:
            ticket_id: Ticket ID to look up

        Returns:
            Ticket object if found, otherwise None
        """
        tickets = self._load_tickets()
        for ticket_data in tickets:
            if ticket_data["ticket_id"] == ticket_id:
                # Convert created_at back to datetime
                ticket_data["created_at"] = datetime.fromisoformat(ticket_data["created_at"])
                return Ticket(**ticket_data)
        return None
