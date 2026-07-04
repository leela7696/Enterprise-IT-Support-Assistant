import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_ticket():
    response = client.post(
        "/ask",
        json={"question": "My VPN is not working"}
    )
    print("Test 1 - Create Ticket:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


def test_employee_lookup():
    response = client.post(
        "/ask",
        json={"question": "Show employee Sarah"}
    )
    print("Test 2 - Employee Lookup:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


def test_policy_search():
    response = client.post(
        "/ask",
        json={"question": "What is the password policy?"}
    )
    print("Test 3 - Policy Search:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


def test_vague_issue():
    response = client.post(
        "/ask",
        json={"question": "My system isn't working"}
    )
    print("Test 4 - Vague Issue:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


def test_empty_question():
    response = client.post(
        "/ask",
        json={"question": ""}
    )
    print("Test 5 - Empty Question:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


def test_greeting():
    response = client.post(
        "/ask",
        json={"question": "Hello"}
    )
    print("Test 6 - Greeting:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print("-" * 50)


if __name__ == "__main__":
    test_create_ticket()
    test_employee_lookup()
    test_policy_search()
    test_vague_issue()
    test_empty_question()
    test_greeting()
