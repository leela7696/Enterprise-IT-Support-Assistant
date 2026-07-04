"""Conversation Manager for managing stateful conversations."""
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from enum import Enum


class NextAction(str, Enum):
    """Next action the assistant should take."""
    WAIT_FOR_USER = "WAIT_FOR_USER"
    CREATE_TICKET = "CREATE_TICKET"
    CLARIFY_ISSUE = "CLARIFY_ISSUE"
    TROUBLESHOOT = "TROUBLESHOOT"


class ConversationStateEnum(str, Enum):
    """Enum for conversation states."""
    START = "START"
    IDENTIFY_ISSUE = "IDENTIFY_ISSUE"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    WAITING_FOR_TICKET_CONFIRMATION = "WAITING_FOR_TICKET_CONFIRMATION"
    CREATE_TICKET = "CREATE_TICKET"
    TICKET_CREATED = "TICKET_CREATED"
    ISSUE_RESOLVED = "ISSUE_RESOLVED"
    END = "END"


class ConversationState:
    """Represents the state of a single conversation."""
    
    def __init__(self, conversation_id: str):
        self.conversation_id: str = conversation_id
        self.issue_type: Optional[str] = None
        self.issue_summary: Optional[str] = None
        self.current_state: ConversationStateEnum = ConversationStateEnum.START
        self.current_step: int = 0
        self.previous_answers: List[Dict[str, Any]] = []
        self.ticket_created: bool = False
        self.created_ticket: Optional[Dict[str, Any]] = None
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation state to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "issue_type": self.issue_type,
            "issue_summary": self.issue_summary,
            "current_state": self.current_state.value,
            "current_step": self.current_step,
            "previous_answers": self.previous_answers,
            "ticket_created": self.ticket_created,
            "created_ticket": self.created_ticket,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConversationManager:
    """Manages all active conversations."""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}

    def create_conversation(self) -> ConversationState:
        """Create a new conversation and return it."""
        conversation_id = f"CONV-{uuid.uuid4().hex[:8].upper()}"
        conversation = ConversationState(conversation_id)
        self.conversations[conversation_id] = conversation
        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)

    def update_conversation(
        self,
        conversation_id: str,
        issue_type: Optional[str] = None,
        issue_summary: Optional[str] = None,
        current_state: Optional[ConversationStateEnum] = None,
        current_step: Optional[int] = None,
        previous_answer: Optional[Dict[str, Any]] = None,
        ticket_created: Optional[bool] = None,
        created_ticket: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationState]:
        """Update a conversation's state."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        if issue_type is not None:
            conversation.issue_type = issue_type
        if issue_summary is not None:
            conversation.issue_summary = issue_summary
        if current_state is not None:
            conversation.current_state = current_state
        if current_step is not None:
            conversation.current_step = current_step
        if previous_answer is not None:
            conversation.previous_answers.append(previous_answer)
        if ticket_created is not None:
            conversation.ticket_created = ticket_created
        if created_ticket is not None:
            conversation.created_ticket = created_ticket
        
        conversation.updated_at = datetime.now()
        return conversation


# Singleton instance
conversation_manager = ConversationManager()
