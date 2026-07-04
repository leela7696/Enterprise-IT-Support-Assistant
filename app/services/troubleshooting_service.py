"""Troubleshooting Service with decision trees for common IT issues."""
from typing import Dict, Tuple, Optional
import logging
from .answer_interpreter import (
    AnswerInterpreter,
    InterpretedState,
    answer_interpreter
)
from .types import IssueType


logger = logging.getLogger(__name__)


# Decision trees for each issue type
# Each step is a tuple: (question, yes_step, no_step, idk_response, ticket_prompt, final_step)
DECISION_TREES = {
    IssueType.LAPTOP: [
        ("I'm sorry you're facing this issue. Is the laptop completely dead or does it turn on but show an error?", 1, 1, "No problem. Can you describe what happens when you press the power button?", None, False),
        ("Is the charging adapter firmly connected to both the laptop and a power outlet?", 2, 3, "Okay, let's check the basics first. Is the charging LED on?", None, False),
        ("Great! Is the charging indicator light ON?", 4, 5, "No problem. Can you try a different power outlet if available?", None, False),
        ("Okay, please try connecting the charger properly. Did that help?", 2, 5, "Let's try to get the charger connected first. Is the charger plugged in all the way?", None, False),
        ("Good! Have you tried holding the power button for 10 seconds to force a restart?", 6, 6, "Let's try a force restart. Hold the power button for 10 seconds, then try turning it on again.", None, False),
        ("Okay, please try another power outlet if available. Did that help?", 4, 6, "No problem. Let's check another outlet if possible.", None, False),
        ("Excellent! I'm glad that resolved the issue.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.VPN: [
        ("I'm sorry you're having VPN issues. Can you connect to the internet normally (without VPN)?", 1, 2, "Okay, let's check your internet connection first. Can you load a website like google.com?", None, False),
        ("Okay, let's troubleshoot your internet first. Is your Wi-Fi connected or Ethernet cable plugged in?", 3, 4, "No problem. Let's check your network connection.", None, False),
        ("Good! Are you receiving an authentication error when trying to connect to VPN?", 5, 6, "Okay, what error message are you seeing when trying to connect?", None, False),
        ("Great! Please check your network connection. Did that resolve the issue?", 1, 6, "Let's get your internet connected first.", None, False),
        ("Okay, please reset your VPN password via the company portal. Did that resolve the issue?", 7, 8, "No problem. Let's try resetting your password first.", None, False),
        ("Okay, please try disconnecting and reconnecting the VPN. Did that help?", 7, 8, "Let's try a simple reconnect first.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.PRINTER: [
        ("I'm sorry your printer isn't working. Is the printer powered on?", 1, 2, "No problem. Let's check the power first. Is the printer turned on?", None, False),
        ("Okay, please make sure the printer is powered on. Did that help?", 1, 3, "Let's get the printer turned on first.", None, False),
        ("Good! Is the printer connected to the computer or network?", 4, 5, "Okay, let's check the connections.", None, False),
        ("Great! Have you tried restarting both the printer and your computer?", 6, 7, "Let's try a quick restart of both devices.", None, False),
        ("Okay, please connect the printer properly. Did that help?", 4, 7, "Let's get the printer connected first.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.OUTLOOK: [
        ("I'm sorry Outlook is crashing. Does Outlook crash immediately after opening?", 1, 2, "Okay, when does Outlook crash - right away or after doing something?", None, False),
        ("Have you tried opening Outlook in Safe Mode? (Hold Ctrl while clicking Outlook)", 3, 4, "Let's try Safe Mode first. Hold Ctrl while opening Outlook.", None, False),
        ("Okay, does Outlook crash after a specific action (like sending an email or opening an attachment)?", 5, 6, "Okay, what are you doing when it crashes?", None, False),
        ("Great! Did opening in Safe Mode work?", 7, 8, "Let's see if Safe Mode helps.", None, False),
        ("Okay, let's try repairing your Office installation. Did that help?", 7, 8, "Let's try repairing Office via Control Panel.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.EMAIL: [
        ("I'm sorry you can't send emails. Can you receive emails okay?", 1, 2, "Okay, let's check both sending and receiving.", None, False),
        ("Okay, are you getting any error messages when trying to send?", 3, 4, "What error do you see?", None, False),
        ("Okay, let's check your internet connection first. Is it working?", 5, 6, "Let's check your internet first.", None, False),
        ("Okay, have you tried restarting Outlook/your email client?", 7, 8, "Let's try a quick restart.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.PASSWORD_RESET: [
        ("Okay, let's help you reset your password. Do you have access to your registered email or phone?", 1, 2, "No problem. Let's see what recovery options you have.", None, False),
        ("Great! Please use the self-service password reset tool at https://password-reset.company.com. Did that work?", 3, 4, "Let's use the self-service tool first.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.INTERNET: [
        ("I'm sorry you're having internet issues. Is this on Wi-Fi or Ethernet?", 1, 2, "Okay, are you using Wi-Fi or a wired connection?", None, False),
        ("Okay, have you tried restarting your router/modem?", 3, 4, "Let's try restarting your network equipment first.", None, False),
        ("Great! Did that restore your internet connection?", 5, 6, "Let's see if that fixed it.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.MONITOR: [
        ("I'm sorry your monitor isn't working. Is the monitor powered on?", 1, 2, "Okay, let's check the power first.", None, False),
        ("Okay, please turn the monitor on. Did that help?", 1, 3, "Let's get the monitor turned on first.", None, False),
        ("Good! Is the monitor connected to your computer properly?", 4, 5, "Okay, let's check the cable connections.", None, False),
        ("Great! Have you tried restarting your computer?", 6, 7, "Let's try a quick restart.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.KEYBOARD: [
        ("I'm sorry your keyboard isn't working. Is this a wired or wireless keyboard?", 1, 2, "Okay, what type of keyboard is it?", None, False),
        ("Okay, have you tried reconnecting it (unplug/plug or re-pair wireless)?", 3, 4, "Let's try reconnecting first.", None, False),
        ("Good! Have you tried restarting your computer?", 5, 6, "Let's try a quick restart.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
    IssueType.MOUSE: [
        ("I'm sorry your mouse isn't working. Is this a wired or wireless mouse?", 1, 2, "Okay, what type of mouse is it?", None, False),
        ("Okay, have you tried reconnecting it (unplug/plug or re-pair wireless)?", 3, 4, "Let's try reconnecting first.", None, False),
        ("Good! Have you tried restarting your computer?", 5, 6, "Let's try a quick restart.", None, False),
        ("Excellent! I'm glad that worked.", None, None, "Great! Let me know if you need anything else.", None, True),
    ],
}

# Add a final "ticket offer" step to each decision tree
for issue_type in DECISION_TREES:
    tree = DECISION_TREES[issue_type]
    # Add the ticket offer step first
    final_ticket_step = len(tree)
    tree.append((
        "I'm sorry we couldn't resolve the issue. Would you like me to create a support ticket?",
        None,
        None,
        "No problem. Let me know if you'd like a support ticket.",
        "Okay, let's create a ticket for you.",
        True
    ))
    # Now go through all steps and make any step that points to None (end) 
    # or a final success step instead point to the ticket offer step
    for i in range(len(tree)-1):  # don't modify the new ticket step itself
        step = list(tree[i])
        # If yes_step is None or points to a final success step, point to ticket offer instead
        if step[1] is None:
            step[1] = final_ticket_step
        else:
            # Check if yes_step points to a final success step
            if step[1] < len(tree)-1 and tree[step[1]][5] and "Excellent" in tree[step[1]][0]:
                step[1] = final_ticket_step
        # If no_step is None or points to a final success step, point to ticket offer instead
        if step[2] is None:
            step[2] = final_ticket_step
        else:
            if step[2] < len(tree)-1 and tree[step[2]][5] and "Excellent" in tree[step[2]][0]:
                step[2] = final_ticket_step
        tree[i] = tuple(step)
    DECISION_TREES[issue_type] = tree


# Keywords to detect issue type
ISSUE_KEYWORDS = {
    IssueType.LAPTOP: ["laptop", "computer won't start", "pc not working"],
    IssueType.VPN: ["vpn", "can't connect to vpn", "vpn not working"],
    IssueType.PRINTER: ["printer", "can't print", "printer not working"],
    IssueType.OUTLOOK: ["outlook", "outlook crashing", "outlook not working"],
    IssueType.EMAIL: ["email", "can't send email", "email not working"],
    IssueType.PASSWORD_RESET: ["password reset", "forgot password", "change password"],
    IssueType.INTERNET: ["internet", "wifi not working", "no internet", "ethernet not working"],
    IssueType.MONITOR: ["monitor", "screen not working", "display not working"],
    IssueType.KEYBOARD: ["keyboard", "keyboard not working", "keys not working"],
    IssueType.MOUSE: ["mouse", "mouse not working", "cursor not working"],
}


def detect_issue_type(question: str) -> Optional[IssueType]:
    """Detect the issue type from user's question."""
    question_lower = question.lower()
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in question_lower:
                return issue_type
    return None


def is_affirmative_answer(answer: str) -> bool:
    """Check if the answer is affirmative (confirmation to create ticket, etc.)."""
    answer_lower = answer.lower().strip()
    affirmative_words = [
        "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "please",
        "go ahead", "create", "create ticket", "confirm", "do it", "proceed"
    ]
    return any(word in answer_lower for word in affirmative_words)


def is_cancel_answer(answer: str) -> bool:
    """Check if the answer is a cancellation (don't create ticket)."""
    answer_lower = answer.lower().strip()
    cancel_words = [
        "no", "nope", "nah", "not now", "cancel", "don't create", "don't", "later"
    ]
    return any(word in answer_lower for word in cancel_words)


class TroubleshootingService:
    """Service to handle troubleshooting logic."""
    
    def get_next_step(self, issue_type: IssueType, current_step: int, user_answer: str) -> Tuple[str, int, bool, bool]:
        """
        Get the next question, step number, is final step, and is ticket offer step.
        
        Returns: (response_text, next_step, is_final_step, is_ticket_offer)
        """
        try:
            tree = DECISION_TREES.get(issue_type, [])
            if not tree or current_step >= len(tree):
                return ("I'm sorry, I can't help with this issue further. Would you like me to create a support ticket?", current_step, True, True)

            current_node = tree[current_step]
            question, yes_step, no_step, idk_response, ticket_prompt, is_final = current_node
            
            # Check if current step is the ticket offer
            is_ticket_offer = "Would you like me to create a support ticket?" in question
            
            if is_ticket_offer:
                if is_affirmative_answer(user_answer):
                    return ("Okay, let's create a ticket for you.", current_step, True, True)
                elif is_cancel_answer(user_answer):
                    return ("Okay, no problem! Let me know if you need anything else later.", current_step, True, False)
                else:
                    return (idk_response or "No problem. Let me know if you'd like a support ticket.", current_step, False, True)
            
            # Interpret the user's answer
            interpretation = answer_interpreter.interpret(user_answer, issue_type)
            logger.debug(f"Interpreted answer: {interpretation.interpreted_state}, confidence: {interpretation.confidence}")
            
            if interpretation.confidence < 0.3:
                # Low confidence, ask for clarification
                return (idk_response or "I'm not sure I understood. Can you please clarify?", current_step, False, False)
            
            # Map interpreted state to yes/no
            if interpretation.interpreted_state in [
                InterpretedState.YES,
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
                # Treat these as "yes" for the decision tree
                if yes_step is None:
                    return (question, current_step, True, False)
                if yes_step >= len(tree):
                    return ("Okay, let's create a ticket for you.", current_step, True, True)
                next_node = tree[yes_step]
                is_ticket_offer_for_next = "Would you like me to create a support ticket?" in next_node[0]
                return (next_node[0], yes_step, next_node[5], is_ticket_offer_for_next)
            elif interpretation.interpreted_state in [
                InterpretedState.NO,
                InterpretedState.NO_POWER,
            ]:
                # Treat these as "no" for the decision tree
                if no_step is None:
                    return (question, current_step, True, False)
                if no_step >= len(tree):
                    return ("Okay, let's create a ticket for you.", current_step, True, True)
                next_node = tree[no_step]
                is_ticket_offer_for_next = "Would you like me to create a support ticket?" in next_node[0]
                return (next_node[0], no_step, next_node[5], is_ticket_offer_for_next)
            else:
                # Unknown state, ask for clarification
                return (idk_response or "No problem. Can you provide more details?", current_step, False, False)
        except Exception as e:
            logger.error(f"Error in troubleshooting step: {str(e)}", exc_info=True)
            return ("I'm sorry, I encountered an issue. Can you please rephrase your answer?", current_step, False, False)

    def get_initial_response(self, issue_type: IssueType) -> Tuple[str, int, bool, bool]:
        """Get the initial response for an issue type.
        
        Returns: (response_text, initial_step, is_final, is_ticket_offer)
        """
        try:
            tree = DECISION_TREES.get(issue_type, [])
            if tree:
                return (tree[0][0], 0, tree[0][5], False)
            return ("Okay, let's help you with this issue!", 0, False, False)
        except Exception as e:
            logger.error(f"Error getting initial troubleshooting response: {str(e)}", exc_info=True)
            return ("Okay, let's help you with this issue!", 0, False, False)


# Singleton instance
troubleshooting_service = TroubleshootingService()
