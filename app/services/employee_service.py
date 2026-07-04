"""Employee lookup service."""
import json
from pathlib import Path
from typing import List, Optional
from app.models import Employee
from app.config import settings


class EmployeeService:
    """Service for looking up employee information."""

    def __init__(self):
        """Initialize employee service with data file path."""
        self.employees_file = settings.DATA_DIR / "employees.json"

    def _load_employees(self) -> List[dict]:
        """Load employees from JSON file.

        Returns:
            List of employee dictionaries
        """
        if not self.employees_file.exists():
            return []
        with open(self.employees_file, "r") as f:
            return json.load(f)

    def find_employee_by_name(self, name: str) -> Optional[Employee]:
        """Find an employee by name.

        Args:
            name: Employee name to search for

        Returns:
            Employee object if found, otherwise None
        """
        employees = self._load_employees()
        name_lower = name.lower()
        for emp_data in employees:
            if name_lower in emp_data["name"].lower():
                return Employee(**emp_data)
        return None
