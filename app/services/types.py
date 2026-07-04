"""Common types for services."""
from enum import Enum


class IssueType(str, Enum):
    """Types of issues we can troubleshoot."""
    LAPTOP = "Laptop"
    VPN = "VPN"
    PRINTER = "Printer"
    OUTLOOK = "Outlook"
    EMAIL = "Email"
    PASSWORD_RESET = "Password Reset"
    INTERNET = "Internet"
    MONITOR = "Monitor"
    KEYBOARD = "Keyboard"
    MOUSE = "Mouse"
    UNKNOWN = "Unknown"
