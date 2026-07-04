"""API routes for the Enterprise IT Support Assistant."""
import time
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from app.models import (
    AskRequest,
    ApiResponse,
    Intent,
    ErrorDetail,
    NextAction,
)
from app.services.intent_service import IntentService
from app.services.ticket_service import TicketService
from app.services.employee_service import EmployeeService
from app.services.policy_service import PolicyService
from app.services.conversation_manager import (
    ConversationManager,
    conversation_manager,
    ConversationStateEnum,
    NextAction as ConvNextAction,
)
from app.services.troubleshooting_service import (
    TroubleshootingService,
    troubleshooting_service,
    IssueType,
    detect_issue_type,
    is_affirmative_answer,
    is_cancel_answer,
    DECISION_TREES,
)
from app.utils.logger import setup_logger, log_with_context
from app.utils.validators import validate_question
from app.config import ErrorCode, CONFIDENCE_THRESHOLD


router = APIRouter(tags=["IT Support"])
logger = setup_logger()

# Initialize services
intent_service = IntentService()
ticket_service = TicketService()
employee_service = EmployeeService()
policy_service = PolicyService()


def build_response(
    success: bool,
    request_id: str,
    intent: Intent,
    confidence: float,
    execution_time_ms: float,
    data=None,
    error=None,
    response=None,
    message=None,
    conversation_id=None,
    current_step=None,
    next_action=None,
) -> ApiResponse:
    """Build a standardized API response."""
    return ApiResponse(
        success=success,
        request_id=request_id,
        intent=intent,
        confidence=confidence,
        conversation_id=conversation_id,
        current_step=current_step,
        next_action=next_action,
        timestamp=datetime.now(),
        execution_time_ms=execution_time_ms,
        data=data,
        error=error,
        response=response,
        message=message or response,
    )


@router.post("/ask", response_model=ApiResponse)
async def ask(request: Request, ask_request: AskRequest):
    """Process user's natural language question and return appropriate response."""
    start_time = time.perf_counter()
    request_id = request.state.request_id

    try:
        # Log incoming request
        log_with_context(
            logger,
            logging.INFO,
            "Received new request",
            request_id=request_id,
            question=ask_request.question[:100],
            conversation_id=ask_request.conversation_id,
        )

        # Validate input
        is_valid, error_msg = validate_question(ask_request.question)
        if not is_valid:
            execution_time = (time.perf_counter() - start_time) * 1000
            log_with_context(
                logger,
                logging.WARNING,
                "Validation failed",
                request_id=request_id,
                error=error_msg,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=False,
                request_id=request_id,
                intent=Intent.UNKNOWN,
                confidence=0.0,
                execution_time_ms=execution_time,
                error=ErrorDetail(code=ErrorCode.VALIDATION_ERROR, message=error_msg),
                response=error_msg,
            )

        # Check if we have an existing conversation
        conversation = None
        if ask_request.conversation_id:
            conversation = conversation_manager.get_conversation(ask_request.conversation_id)

        if conversation:
            # Continue existing conversation
            return await handle_existing_conversation(
                request_id,
                start_time,
                conversation,
                ask_request.question,
            )

        # New conversation - classify intent
        classification_result = intent_service.classify_intent(ask_request.question)
        log_with_context(
            logger,
            logging.INFO,
            "Intent classified",
            request_id=request_id,
            intent=classification_result.intent.value,
            confidence=classification_result.confidence,
            matched_keywords=",".join(classification_result.matched_keywords),
        )

        # Detect issue type for troubleshooting
        issue_type = detect_issue_type(ask_request.question)

        if issue_type and issue_type != IssueType.UNKNOWN:
            # Start new troubleshooting conversation
            return await start_troubleshooting(
                request_id,
                start_time,
                issue_type,
                ask_request.question,
                classification_result,
            )

        # Handle other intents
        return await handle_other_intents(
            request_id,
            start_time,
            ask_request.question,
            classification_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.exception(f"Unexpected error processing request {request_id}")
        return build_response(
            success=False,
            request_id=request_id,
            intent=Intent.UNKNOWN,
            confidence=0.0,
            execution_time_ms=execution_time,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred. Please try again later.",
            ),
            response="An unexpected error occurred. Please try again later.",
        )


async def handle_existing_conversation(
    request_id: str,
    start_time: float,
    conversation,
    user_answer: str,
) -> ApiResponse:
    """Handle an existing conversation with proper state machine transitions."""
    # First check if ticket is already created
    if conversation.ticket_created and conversation.created_ticket:
        execution_time = (time.perf_counter() - start_time) * 1000
        # Handle post-ticket-creation questions
        if is_affirmative_answer(user_answer):
            # User is trying to create another ticket
            response_text = "A ticket has already been created for this issue."
        else:
            ticket = conversation.created_ticket
            response_text = f"Your ticket {ticket['ticket_id']} is currently {ticket['status']} and assigned to {ticket['assigned_team']}."
        log_with_context(
            logger,
            logging.INFO,
            "Post-ticket conversation",
            request_id=request_id,
            conversation_id=conversation.conversation_id,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=Intent.TROUBLESHOOT,
            confidence=1.0,
            execution_time_ms=execution_time,
            conversation_id=conversation.conversation_id,
            current_step=conversation.current_step,
            next_action=NextAction.WAIT_FOR_USER,
            response=response_text,
        )
    
    issue_type = IssueType(conversation.issue_type)
    current_state = conversation.current_state
    
    # Handle state machine transitions
    if current_state == ConversationStateEnum.TROUBLESHOOTING:
        # First check if we're already on the ticket offer step
        tree = DECISION_TREES.get(issue_type, [])
        is_currently_ticket_offer = False
        if conversation.current_step < len(tree):
            current_question = tree[conversation.current_step][0]
            is_currently_ticket_offer = "Would you like me to create a support ticket?" in current_question
        
        if is_currently_ticket_offer:
            # Check if user is confirming or cancelling
            if is_affirmative_answer(user_answer):
                # Create ticket
                ticket = ticket_service.create_ticket(
                    conversation.issue_summary or f"Support needed for {issue_type.value}"
                )
                ticket_dict = ticket.model_dump()
                # Update conversation
                conversation_manager.update_conversation(
                    conversation.conversation_id,
                    current_state=ConversationStateEnum.TICKET_CREATED,
                    ticket_created=True,
                    created_ticket=ticket_dict,
                    previous_answer={"step": conversation.current_step, "answer": user_answer},
                )
                execution_time = (time.perf_counter() - start_time) * 1000
                log_with_context(
                    logger,
                    logging.INFO,
                    "Created ticket from conversation",
                    request_id=request_id,
                    conversation_id=conversation.conversation_id,
                    ticket_id=ticket.ticket_id,
                    execution_time_ms=execution_time,
                )
                return build_response(
                    success=True,
                    request_id=request_id,
                    intent=Intent.CREATE_TICKET,
                    confidence=1.0,
                    execution_time_ms=execution_time,
                    conversation_id=conversation.conversation_id,
                    current_step=conversation.current_step,
                    next_action=NextAction.WAIT_FOR_USER,
                    data=ticket_dict,
                    response=f"Your support ticket has been created successfully. Ticket ID: {ticket.ticket_id}",
                )
            elif is_cancel_answer(user_answer):
                # Cancel ticket creation
                conversation_manager.update_conversation(
                    conversation.conversation_id,
                    current_state=ConversationStateEnum.END,
                    previous_answer={"step": conversation.current_step, "answer": user_answer},
                )
                execution_time = (time.perf_counter() - start_time) * 1000
                return build_response(
                    success=True,
                    request_id=request_id,
                    intent=Intent.TROUBLESHOOT,
                    confidence=1.0,
                    execution_time_ms=execution_time,
                    conversation_id=conversation.conversation_id,
                    current_step=conversation.current_step,
                    next_action=NextAction.WAIT_FOR_USER,
                    response="Okay, no problem! Let me know if you need anything else later.",
                )
            else:
                # Unclear answer
                execution_time = (time.perf_counter() - start_time) * 1000
                return build_response(
                    success=True,
                    request_id=request_id,
                    intent=Intent.TROUBLESHOOT,
                    confidence=1.0,
                    execution_time_ms=execution_time,
                    conversation_id=conversation.conversation_id,
                    current_step=conversation.current_step,
                    next_action=NextAction.WAIT_FOR_USER,
                    response="No problem. Let me know if you'd like a support ticket.",
                )
        
        # Otherwise, continue troubleshooting
        next_response, next_step, is_final, is_ticket_offer = troubleshooting_service.get_next_step(
            issue_type, conversation.current_step, user_answer
        )
        
        # Update conversation with previous answer
        conversation_manager.update_conversation(
            conversation.conversation_id,
            previous_answer={"step": conversation.current_step, "answer": user_answer},
            current_step=next_step
        )
        
        if is_ticket_offer:
            # Transition to waiting for ticket confirmation
            conversation_manager.update_conversation(
                conversation.conversation_id,
                current_state=ConversationStateEnum.WAITING_FOR_TICKET_CONFIRMATION
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            log_with_context(
                logger,
                logging.INFO,
                "Transition to WAITING_FOR_TICKET_CONFIRMATION",
                request_id=request_id,
                conversation_id=conversation.conversation_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=True,
                request_id=request_id,
                intent=Intent.TROUBLESHOOT,
                confidence=1.0,
                execution_time_ms=execution_time,
                conversation_id=conversation.conversation_id,
                current_step=next_step,
                next_action=NextAction.WAIT_FOR_USER,
                response=next_response,
            )
        
        if is_final and not is_ticket_offer:
            # Issue resolved!
            conversation_manager.update_conversation(
                conversation.conversation_id,
                current_state=ConversationStateEnum.ISSUE_RESOLVED
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            log_with_context(
                logger,
                logging.INFO,
                "Issue resolved!",
                request_id=request_id,
                conversation_id=conversation.conversation_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=True,
                request_id=request_id,
                intent=Intent.TROUBLESHOOT,
                confidence=1.0,
                execution_time_ms=execution_time,
                conversation_id=conversation.conversation_id,
                current_step=next_step,
                next_action=NextAction.WAIT_FOR_USER,
                response=next_response,
            )
        
        # Continue troubleshooting
        execution_time = (time.perf_counter() - start_time) * 1000
        log_with_context(
            logger,
            logging.INFO,
            "Continuing troubleshooting",
            request_id=request_id,
            conversation_id=conversation.conversation_id,
            issue_type=issue_type.value,
            current_step=next_step,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=Intent.TROUBLESHOOT,
            confidence=1.0,
            execution_time_ms=execution_time,
            conversation_id=conversation.conversation_id,
            current_step=next_step,
            next_action=NextAction.WAIT_FOR_USER,
            response=next_response,
        )
    
    elif current_state == ConversationStateEnum.WAITING_FOR_TICKET_CONFIRMATION:
        if is_affirmative_answer(user_answer):
            # Create ticket!
            ticket = ticket_service.create_ticket(conversation.issue_summary or f"Support needed for {issue_type.value}")
            ticket_dict = ticket.model_dump()
            conversation_manager.update_conversation(
                conversation.conversation_id,
                current_state=ConversationStateEnum.TICKET_CREATED,
                ticket_created=True,
                created_ticket=ticket_dict
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            log_with_context(
                logger,
                logging.INFO,
                "Created ticket from conversation",
                request_id=request_id,
                conversation_id=conversation.conversation_id,
                ticket_id=ticket.ticket_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=True,
                request_id=request_id,
                intent=Intent.CREATE_TICKET,
                confidence=1.0,
                execution_time_ms=execution_time,
                conversation_id=conversation.conversation_id,
                current_step=conversation.current_step,
                next_action=NextAction.WAIT_FOR_USER,
                data=ticket_dict,
                response=f"Your support ticket has been created successfully. Ticket ID: {ticket.ticket_id}",
            )
        else:
            # User declined ticket
            conversation_manager.update_conversation(
                conversation.conversation_id,
                current_state=ConversationStateEnum.END
            )
            execution_time = (time.perf_counter() - start_time) * 1000
            return build_response(
                success=True,
                request_id=request_id,
                intent=Intent.TROUBLESHOOT,
                confidence=1.0,
                execution_time_ms=execution_time,
                conversation_id=conversation.conversation_id,
                current_step=conversation.current_step,
                next_action=NextAction.WAIT_FOR_USER,
                response="Okay, no problem! Let me know if you need anything else later.",
            )
    
    elif current_state == ConversationStateEnum.ISSUE_RESOLVED or current_state == ConversationStateEnum.END:
        execution_time = (time.perf_counter() - start_time) * 1000
        return build_response(
            success=True,
            request_id=request_id,
            intent=Intent.TROUBLESHOOT,
            confidence=1.0,
            execution_time_ms=execution_time,
            conversation_id=conversation.conversation_id,
            current_step=conversation.current_step,
            next_action=NextAction.WAIT_FOR_USER,
            response="Is there anything else I can help you with today?",
        )
    
    # If none of the above, default to continuing troubleshooting
    next_response, next_step, is_final, is_ticket_offer = troubleshooting_service.get_next_step(
        issue_type, conversation.current_step, user_answer
    )
    conversation_manager.update_conversation(
        conversation.conversation_id,
        previous_answer={"step": conversation.current_step, "answer": user_answer},
        current_step=next_step
    )
    execution_time = (time.perf_counter() - start_time) * 1000
    return build_response(
        success=True,
        request_id=request_id,
        intent=Intent.TROUBLESHOOT,
        confidence=1.0,
        execution_time_ms=execution_time,
        conversation_id=conversation.conversation_id,
        current_step=next_step,
        next_action=NextAction.WAIT_FOR_USER,
        response=next_response,
    )


async def start_troubleshooting(
    request_id: str,
    start_time: float,
    issue_type: IssueType,
    question: str,
    classification_result,
) -> ApiResponse:
    """Start a new troubleshooting conversation."""
    # Create new conversation
    conversation = conversation_manager.create_conversation()
    initial_response, initial_step, is_final, is_ticket_offer = troubleshooting_service.get_initial_response(issue_type)
    conversation_manager.update_conversation(
        conversation.conversation_id,
        issue_type=issue_type.value,
        issue_summary=question,
        current_state=ConversationStateEnum.TROUBLESHOOTING,
        current_step=initial_step,
    )
    execution_time = (time.perf_counter() - start_time) * 1000
    log_with_context(
        logger,
        logging.INFO,
        "Started new troubleshooting conversation",
        request_id=request_id,
        conversation_id=conversation.conversation_id,
        issue_type=issue_type.value,
        execution_time_ms=execution_time,
    )
    return build_response(
        success=True,
        request_id=request_id,
        intent=Intent.TROUBLESHOOT,
        confidence=classification_result.confidence,
        execution_time_ms=execution_time,
        conversation_id=conversation.conversation_id,
        current_step=initial_step,
        next_action=NextAction.WAIT_FOR_USER,
        response=initial_response,
    )


async def handle_other_intents(
    request_id: str,
    start_time: float,
    question: str,
    classification_result,
) -> ApiResponse:
    """Handle non-troubleshooting intents."""
    # Handle greeting
    if classification_result.intent == Intent.GREETING:
        execution_time = (time.perf_counter() - start_time) * 1000
        log_with_context(
            logger,
            logging.INFO,
            "Handled greeting",
            request_id=request_id,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=classification_result.intent,
            confidence=classification_result.confidence,
            execution_time_ms=execution_time,
            response="Hello! How can I assist you today with IT support?\n\nI can help with:\n- Laptop issues\n- VPN problems\n- Printer issues\n- Outlook/Email problems\n- Password reset\n- And more!",
        )

    # Handle ticket status
    if classification_result.intent == Intent.CHECK_STATUS:
        ticket_id = intent_service.extract_ticket_id(question)
        if not ticket_id:
            execution_time = (time.perf_counter() - start_time) * 1000
            response_text = "Please provide a ticket ID (e.g., INC1001)"
            log_with_context(
                logger,
                logging.INFO,
                "Ticket ID not provided - clarification requested",
                request_id=request_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=True,
                request_id=request_id,
                intent=classification_result.intent,
                confidence=classification_result.confidence,
                execution_time_ms=execution_time,
                response=response_text,
            )

        ticket = ticket_service.get_ticket(ticket_id)
        execution_time = (time.perf_counter() - start_time) * 1000
        if not ticket:
            log_with_context(
                logger,
                logging.WARNING,
                "Ticket not found",
                request_id=request_id,
                ticket_id=ticket_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=False,
                request_id=request_id,
                intent=classification_result.intent,
                confidence=classification_result.confidence,
                execution_time_ms=execution_time,
                error=ErrorDetail(code=ErrorCode.NOT_FOUND, message=f"Ticket {ticket_id} not found"),
                response=f"Ticket {ticket_id} not found",
            )

        log_with_context(
            logger,
            logging.INFO,
            "Ticket status retrieved",
            request_id=request_id,
            ticket_id=ticket_id,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=classification_result.intent,
            confidence=classification_result.confidence,
            execution_time_ms=execution_time,
            data=ticket.model_dump(),
            response="Ticket status retrieved",
        )

    # Handle employee lookup
    if classification_result.intent == Intent.EMPLOYEE_LOOKUP:
        employee_name = intent_service.extract_employee_name(question)
        if not employee_name:
            execution_time = (time.perf_counter() - start_time) * 1000
            response_text = "Please provide an employee name to look up"
            log_with_context(
                logger,
                logging.INFO,
                "Employee name not provided - clarification requested",
                request_id=request_id,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=True,
                request_id=request_id,
                intent=classification_result.intent,
                confidence=classification_result.confidence,
                execution_time_ms=execution_time,
                response=response_text,
            )

        employee = employee_service.find_employee_by_name(employee_name)
        execution_time = (time.perf_counter() - start_time) * 1000
        if not employee:
            log_with_context(
                logger,
                logging.WARNING,
                "Employee not found",
                request_id=request_id,
                employee_name=employee_name,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=False,
                request_id=request_id,
                intent=classification_result.intent,
                confidence=classification_result.confidence,
                execution_time_ms=execution_time,
                error=ErrorDetail(code=ErrorCode.NOT_FOUND, message=f"Employee '{employee_name}' not found"),
                response=f"Employee '{employee_name}' not found",
            )

        log_with_context(
            logger,
            logging.INFO,
            "Employee found",
            request_id=request_id,
            employee_id=employee.id,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=classification_result.intent,
            confidence=classification_result.confidence,
            execution_time_ms=execution_time,
            data=employee.model_dump(),
            response="Employee found",
        )

    # Handle policy search
    if classification_result.intent == Intent.POLICY_SEARCH:
        policy_topic = intent_service.extract_policy_topic(question)
        policy = policy_service.find_policy(policy_topic)
        execution_time = (time.perf_counter() - start_time) * 1000

        if not policy:
            log_with_context(
                logger,
                logging.WARNING,
                "Policy not found",
                request_id=request_id,
                policy_topic=policy_topic,
                execution_time_ms=execution_time,
            )
            return build_response(
                success=False,
                request_id=request_id,
                intent=classification_result.intent,
                confidence=classification_result.confidence,
                execution_time_ms=execution_time,
                error=ErrorDetail(code=ErrorCode.NOT_FOUND, message="Policy not found"),
                response="Policy not found",
            )

        log_with_context(
            logger,
            logging.INFO,
            "Policy retrieved",
            request_id=request_id,
            policy_id=policy.id,
            execution_time_ms=execution_time,
        )
        return build_response(
            success=True,
            request_id=request_id,
            intent=classification_result.intent,
            confidence=classification_result.confidence,
            execution_time_ms=execution_time,
            data=policy.model_dump(),
            response="Policy retrieved",
        )

    # Fallback
    execution_time = (time.perf_counter() - start_time) * 1000
    response_text = "I couldn't determine your request. You can ask about IT issues like laptop, VPN, printer, etc., or about tickets, employees, or IT policies."
    log_with_context(
        logger,
        logging.INFO,
        "Intent unknown - clarification requested",
        request_id=request_id,
        execution_time_ms=execution_time,
    )
    return build_response(
        success=True,
        request_id=request_id,
        intent=Intent.UNKNOWN,
        confidence=0.0,
        execution_time_ms=execution_time,
        response=response_text,
    )
