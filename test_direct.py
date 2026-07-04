import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.intent_service import IntentService
from app.services.ticket_service import TicketService
from app.services.employee_service import EmployeeService
from app.services.policy_service import PolicyService
from app.utils.validators import validate_question
from app.utils.logger import setup_logger

logger = setup_logger()


def run_direct_tests():
    print("=== Direct Tests\n")

    print("1. Test validate_question:")
    tests = [
        ("My VPN is not working", True, None),
        ("", False, "Question cannot be empty"),
        (None, False, "Question field is mandatory"),
        ("a" * 600, False, "Question cannot be longer than 500 characters"),
    ]
    for q, expected_valid, expected_msg in tests:
        is_valid, msg = validate_question(q)
        print(f"  Question: {q[:50]}...")
        print(f"  Valid: {is_valid} (expected {expected_valid}), Message: {msg}")

    print("\n2. Test IntentService:")
    intent_service = IntentService()
    intent_tests = [
        ("My VPN is not working", "CREATE_TICKET"),
        ("Check ticket INC1001", "CHECK_STATUS"),
        ("Show employee Sarah", "EMPLOYEE_LOOKUP"),
        ("What's the password policy?", "POLICY_SEARCH"),
        ("Hello!", "GREETING"),
        ("Blah blah", "UNKNOWN"),
    ]
    for q, expected_intent in intent_tests:
        intent = intent_service.detect_intent(q)
        print(f"  Question: {q}")
        print(f"  Detected intent: {intent} (expected {expected_intent})")

    print("\n3. Test TicketService:")
    ticket_service = TicketService()
    ticket = ticket_service.create_ticket("My VPN is not working")
    print(f"  Created ticket: {ticket}")
    retrieved = ticket_service.get_ticket(ticket.id)
    print(f"  Retrieved ticket: {retrieved}")

    print("\n4. Test EmployeeService:")
    employee_service = EmployeeService()
    emp = employee_service.find_employee_by_name("Sarah")
    print(f"  Found employee: {emp}")

    print("\n5. Test PolicyService:")
    policy_service = PolicyService()
    policy = policy_service.find_policy("password")
    print(f"  Found policy: {policy}")

    print("\n✅ All direct tests complete!")


if __name__ == "__main__":
    run_direct_tests()
