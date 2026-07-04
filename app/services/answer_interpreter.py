"""Answer Interpreter Service to parse natural language answers into structured states."""
from typing import Dict, Tuple, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from .types import IssueType


class InterpretedState(str, Enum):
    """Possible interpreted states from user answers."""
    NO_POWER = "NO_POWER"
    PARTIAL_BOOT = "PARTIAL_BOOT"
    BSOD = "BSOD"
    BLACK_SCREEN = "BLACK_SCREEN"
    BOOT_LOOP = "BOOT_LOOP"
    POWER_CONNECTED = "POWER_CONNECTED"
    AUTH_ERROR = "AUTH_ERROR"
    ROUTING_ERROR = "ROUTING_ERROR"
    CONNECTION_FAILED = "CONNECTION_FAILED"
    PAPER_JAM = "PAPER_JAM"
    OFFLINE = "OFFLINE"
    LOW_INK = "LOW_INK"
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class InterpretationResult(BaseModel):
    """Result from answer interpretation."""
    interpreted_state: InterpretedState
    confidence: float
    matched_keywords: list[str] = Field(default_factory=list)


# Keyword mappings for each issue type
KEYWORD_MAPPINGS = {
    IssueType.LAPTOP: {
        InterpretedState.NO_POWER: ["no power", "dead", "no lights", "nothing happens", "completely dead", "no response"],
        InterpretedState.PARTIAL_BOOT: ["logo appears", "logo is visible", "windows starts", "boot screen", "manufacturer logo", "starts to boot", "booting"],
        InterpretedState.BSOD: ["blue screen", "bsod", "blue screen of death"],
        InterpretedState.BLACK_SCREEN: ["black screen", "dark screen", "no display"],
        InterpretedState.BOOT_LOOP: ["restarting", "boot loop", "keeps restarting", "restarts repeatedly"],
        InterpretedState.POWER_CONNECTED: ["charging light", "charger light", "charging", "power connected"],
        InterpretedState.YES: ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "did", "works", "worked", "help", "helped", "on", "plugged in", "connected", "received"],
        InterpretedState.NO: ["no", "nope", "nah", "not", "didn't", "did not", "doesn't", "does not", "won't", "will not", "didn't help", "didn't work", "off", "unplugged", "disconnected", "not working"],
    },
    IssueType.VPN: {
        InterpretedState.AUTH_ERROR: ["authentication failed", "login failed", "invalid credentials", "wrong password", "auth error"],
        InterpretedState.ROUTING_ERROR: ["connected but no internet", "no internet access", "can't access sites", "connected but not working"],
        InterpretedState.CONNECTION_FAILED: ["cannot connect", "can't connect", "connection failed", "connection refused", "unable to connect"],
        InterpretedState.YES: ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "did", "works", "worked", "help", "helped", "connected"],
        InterpretedState.NO: ["no", "nope", "nah", "not", "didn't", "did not", "doesn't", "does not", "won't", "will not", "didn't help", "didn't work", "disconnected"],
    },
    IssueType.PRINTER: {
        InterpretedState.PAPER_JAM: ["paper jam", "jammed", "paper stuck"],
        InterpretedState.OFFLINE: ["offline", "printer offline"],
        InterpretedState.LOW_INK: ["no ink", "low ink", "toner low", "out of ink", "no toner"],
        InterpretedState.YES: ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "did", "works", "worked", "help", "helped", "on", "plugged in", "connected"],
        InterpretedState.NO: ["no", "nope", "nah", "not", "didn't", "did not", "doesn't", "does not", "won't", "will not", "didn't help", "didn't work", "off", "unplugged", "disconnected", "not working"],
    },
}

# Add default mappings for all other issue types
for issue_type in IssueType:
    if issue_type not in KEYWORD_MAPPINGS:
        KEYWORD_MAPPINGS[issue_type] = {
            InterpretedState.YES: ["yes", "yeah", "yep", "yup", "sure", "ok", "okay", "did", "works", "worked", "help", "helped", "on", "plugged in", "connected", "received"],
            InterpretedState.NO: ["no", "nope", "nah", "not", "didn't", "did not", "doesn't", "does not", "won't", "will not", "didn't help", "didn't work", "off", "unplugged", "disconnected", "not working"],
        }


class AnswerInterpreter:
    """Service to interpret natural language answers into structured states."""
    
    def interpret(self, answer: str, issue_type: Optional[IssueType] = None) -> InterpretationResult:
        """
        Interpret a natural language answer into a structured state.
        
        Args:
            answer: User's natural language answer
            issue_type: Optional issue type for context-specific interpretation
            
        Returns:
            InterpretationResult with state, confidence, and matched keywords
        """
        answer_lower = answer.lower().strip()
        
        # Get the appropriate keyword mapping
        if issue_type and issue_type in KEYWORD_MAPPINGS:
            mappings = KEYWORD_MAPPINGS[issue_type]
        else:
            # Default to yes/no mapping
            mappings = {
                InterpretedState.YES: ["yes", "yeah", "yep", "yup", "sure", "ok", "okay"],
                InterpretedState.NO: ["no", "nope", "nah", "not", "didn't"],
            }
        
        best_state = InterpretedState.UNKNOWN
        best_confidence = 0.0
        best_keywords = []
        
        # Priority order of states (more specific states first)
        priority_order = [
            InterpretedState.PARTIAL_BOOT,
            InterpretedState.BSOD,
            InterpretedState.BLACK_SCREEN,
            InterpretedState.BOOT_LOOP,
            InterpretedState.POWER_CONNECTED,
            InterpretedState.AUTH_ERROR,
            InterpretedState.ROUTING_ERROR,
            InterpretedState.CONNECTION_FAILED,
            InterpretedState.PAPER_JAM,
            InterpretedState.OFFLINE,
            InterpretedState.LOW_INK,
            InterpretedState.NO_POWER,
            InterpretedState.YES,
            InterpretedState.NO,
        ]
        
        # Check states in priority order
        for state in priority_order:
            if state not in mappings:
                continue
                
            keywords = mappings[state]
            matched = []
            for keyword in keywords:
                # Check if keyword exists and is not negated
                if keyword in answer_lower:
                    # Check for negations before the keyword
                    keyword_index = answer_lower.find(keyword)
                    # Look back up to 10 characters for negation words
                    context_before = answer_lower[max(0, keyword_index - 15):keyword_index]
                    negations = ["not", "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "cannot"]
                    is_negated = any(neg in context_before for neg in negations)
                    
                    if not is_negated:
                        matched.append(keyword)
            
            if matched:
                # Calculate confidence based on number and length of matches
                confidence = min(0.95, 0.5 + (len(matched) * 0.15) + (sum(len(k) for k in matched) / 100))
                
                # Boost confidence for priority states
                if state in [
                    InterpretedState.PARTIAL_BOOT,
                    InterpretedState.BSOD,
                    InterpretedState.BLACK_SCREEN,
                    InterpretedState.BOOT_LOOP,
                    InterpretedState.POWER_CONNECTED,
                    InterpretedState.AUTH_ERROR,
                    InterpretedState.ROUTING_ERROR,
                    InterpretedState.CONNECTION_FAILED,
                    InterpretedState.PAPER_JAM,
                    InterpretedState.OFFLINE,
                    InterpretedState.LOW_INK,
                ]:
                    confidence += 0.1
                    confidence = min(1.0, confidence)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_state = state
                    best_keywords = matched
        
        return InterpretationResult(
            interpreted_state=best_state,
            confidence=best_confidence,
            matched_keywords=best_keywords
        )


# Singleton instance
answer_interpreter = AnswerInterpreter()
