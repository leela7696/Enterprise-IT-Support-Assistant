"""Pydantic models for data validation and serialization."""
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Dict
from app.config import ErrorCode


class Intent(str, Enum):
    """Intent classification enumeration."""
    CREATE_TICKET = "CREATE_TICKET"
    CHECK_STATUS = "CHECK_STATUS"
    EMPLOYEE_LOOKUP = "EMPLOYEE_LOOKUP"
    POLICY_SEARCH = "POLICY_SEARCH"
    GREETING = "GREETING"
    UNKNOWN = "UNKNOWN"
    TROUBLESHOOT = "TROUBLESHOOT"


class Priority(str, Enum):
    """Ticket priority enumeration."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Status(str, Enum):
    """Ticket status enumeration."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class NextAction(str, Enum):
    """Next action the assistant should take."""
    WAIT_FOR_USER = "WAIT_FOR_USER"
    CREATE_TICKET = "CREATE_TICKET"
    CLARIFY_ISSUE = "CLARIFY_ISSUE"
    TROUBLESHOOT = "TROUBLESHOOT"


class IntentClassificationResult(BaseModel):
    """Result from intent classification."""
    intent: Intent
    confidence: float
    matched_keywords: List[str]


class ErrorDetail(BaseModel):
    """Error detail schema."""
    code: ErrorCode
    message: str


class Employee(BaseModel):
    """Employee data model."""
    id: str = Field(..., description="Unique employee identifier")
    name: str = Field(..., description="Full name of the employee")
    department: str = Field(..., description="Department the employee belongs to")
    designation: str = Field(..., description="Job title")
    manager: str = Field(..., description="Manager's name")
    email: str = Field(..., description="Work email address")
    phone: str = Field(..., description="Work phone number")
    office_location: str = Field(default="Headquarters", description="Office location")


class Ticket(BaseModel):
    """Ticket data model."""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    issue: str = Field(..., description="Description of the issue")
    priority: Priority = Field(..., description="Priority level of the ticket")
    category: str = Field(..., description="Category of the issue")
    assigned_team: str = Field(..., description="Team assigned to handle the ticket")
    status: Status = Field(..., description="Current status of the ticket")
    created_at: datetime = Field(..., description="Timestamp when ticket was created")
    suggested_resolution: Optional[str] = Field(default=None, description="Suggested troubleshooting steps")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class Policy(BaseModel):
    """Policy data model."""
    id: str = Field(..., description="Unique policy identifier")
    title: str = Field(..., description="Policy title")
    description: str = Field(..., description="Full policy description")
    matched_keywords: Optional[List[str]] = Field(default=None, description="Keywords matched during search")


class AskRequest(BaseModel):
    """Request schema for /ask endpoint."""
    question: str = Field(
        ...,
        description="User's question or request in natural language",
        max_length=500,
        example="My VPN is not connecting"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID for stateful conversations",
        example="CONV-ABC12345"
    )


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    status: str = Field(..., description="Health status of the service", example="healthy")
    version: str = Field(..., description="Application version", example="1.0.0")
    uptime: str = Field(..., description="Time since service started", example="0:05:30")


class ApiResponse(BaseModel):
    """Standard API response schema."""
    success: bool = Field(..., description="Indicates if request was successful")
    request_id: str = Field(..., description="Unique request identifier", example="REQ-20260703-0001")
    intent: Optional[Intent] = Field(default=None, description="Detected user intent")
    confidence: Optional[float] = Field(default=None, description="Confidence score of intent classification")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for stateful conversations")
    current_step: Optional[int] = Field(default=None, description="Current step in troubleshooting flow")
    next_action: Optional[NextAction] = Field(default=None, description="Next action the assistant expects")
    timestamp: datetime = Field(..., description="Response timestamp")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    data: Optional[Any] = Field(default=None, description="Response data (if any)")
    error: Optional[ErrorDetail] = Field(default=None, description="Error details (if any)")
    response: Optional[str] = Field(default=None, description="Text response from assistant")
    message: Optional[str] = Field(default=None, description="Human-readable message (deprecated, use response)")
