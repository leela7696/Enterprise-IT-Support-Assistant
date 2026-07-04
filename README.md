# Enterprise IT Support Assistant

An AI-powered, offline-first IT support assistant built with Python and FastAPI. Accepts natural language questions, detects user intent using rule-based keyword matching with confidence scoring, and performs various business actions like ticket creation, ticket status checks, employee lookup, and policy search.

## Architecture

This project follows a clean layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│                   (API Routes, FastAPI)                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    Intent Classification Layer               │
│              (Intent detection, confidence scoring)          │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   Business Logic Layer                      │
│          (TicketService, EmployeeService, PolicyService)    │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                     Data Access Layer                       │
│              (JSON file storage, data loading/saving)        │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      JSON Storage Layer                      │
│              (employees.json, tickets.json, policies.json)  │
└─────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
enterprise-it-support-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Application settings and constants
│   ├── models.py               # Pydantic data models
│   ├── middleware.py           # Request ID and execution time middleware
│   ├── routes.py               # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intent_service.py       # Intent classification
│   │   ├── ticket_service.py       # Ticket management
│   │   ├── employee_service.py     # Employee lookup
│   │   ├── policy_service.py       # Policy search
│   │   ├── conversation_manager.py # Conversation state management
│   │   ├── troubleshooting_service.py  # Step-by-step troubleshooting
│   │   ├── answer_interpreter.py   # Natural language answer parsing
│   │   └── types.py                # Shared types and enums
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Structured logging
│   │   └── validators.py       # Input validation
│   ├── static/
│   │   └── index.html          # Web chat UI
│   ├── data/
│   │   ├── employees.json      # Employee dataset
│   │   ├── tickets.json        # Ticket storage
│   │   └── policies.json       # IT policies dataset
│   └── logs/
│       └── app.log             # Application logs
├── requirements.txt
└── README.md
```

## Features

- **Intent Classification**: Rule-based intent detection with confidence scoring and matched keywords
- **Natural Language Answer Parsing**: Understand natural language answers (not just yes/no) using AnswerInterpreter with issue-specific state detection
- **Conversational Troubleshooting**: Step-by-step troubleshooting with decision trees for 10+ common IT issues
- **Conversation State Management**: In-memory conversation storage (conversation_id, current_step, previous answers)
- **Ticket Management**: Create support tickets only after troubleshooting fails (or user requests it), with automatic priority, category, and assigned team
- **Employee Lookup**: Find employees by name with detailed information
- **Policy Search**: Search IT policies with best matching algorithm
- **Health Check**: Endpoint to verify service health and uptime
- **Structured Logging**: Comprehensive logging with request IDs, conversation IDs, execution times, and intent details
- **Standardized Responses**: Consistent API response format across all endpoints
- **Web UI**: Beautiful, responsive Bootstrap 5 chat interface
- **Comprehensive Documentation**: Swagger UI and Redoc for API exploration

## Installation

1. **Clone or navigate to the project directory**
2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # Or on Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally

```bash
uvicorn app.main:app --reload
```

The application will start at http://localhost:8000

Swagger UI is available at: http://localhost:8000/docs  
Redoc documentation: http://localhost:8000/redoc

## API Documentation

### Health Check
```http
GET /health
```

Returns service health status, version, and uptime.

### Ask Question
```http
POST /ask
Content-Type: application/json

{
  "question": "My VPN is not working"
}
```

Processes a natural language question and returns an appropriate response.

## Sample Requests & Responses

### 1. Create a Ticket
**Request**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question":"My VPN is not connecting"}'
```

**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-ABCD",
  "intent": "CREATE_TICKET",
  "confidence": 0.75,
  "timestamp": "2026-07-03T12:34:56.789Z",
  "execution_time_ms": 12.34,
  "data": {
    "ticket_id": "INC1001",
    "issue": "My VPN is not connecting",
    "priority": "Medium",
    "category": "Network",
    "assigned_team": "IT Infrastructure",
    "status": "Open",
    "created_at": "2026-07-03T12:34:56.789Z",
    "suggested_resolution": "Please reconnect to the VPN and verify your internet connection. If the problem persists, restart your computer.",
    "notes": null
  },
  "error": null,
  "message": "Ticket created successfully"
}
```

### 2. Employee Lookup
**Request**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question":"Show employee Sarah"}'
```

**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-EFGH",
  "intent": "EMPLOYEE_LOOKUP",
  "confidence": 0.8,
  "timestamp": "2026-07-03T12:35:00.123Z",
  "execution_time_ms": 8.45,
  "data": {
    "id": "EMP1001",
    "name": "Sarah Johnson",
    "department": "Engineering",
    "designation": "Senior Software Engineer",
    "manager": "David Chen",
    "email": "sarah.johnson@company.com",
    "phone": "+1-555-0101",
    "office_location": "Headquarters"
  },
  "error": null,
  "message": "Employee found"
}
```

### 3. Policy Search
**Request**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question":"What is the password policy?"}'
```

**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-IJKL",
  "intent": "POLICY_SEARCH",
  "confidence": 0.85,
  "timestamp": "2026-07-03T12:36:00.456Z",
  "execution_time_ms": 6.23,
  "data": {
    "id": "POL001",
    "title": "Password Policy",
    "description": "Passwords must be at least 12 characters long, include uppercase, lowercase, numbers, and special characters. Passwords expire every 90 days.",
    "matched_keywords": ["password"]
  },
  "error": null,
  "message": "Policy retrieved"
}
```

### 4. Ticket Status Check
**Request**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question":"Check ticket INC1001"}'
```

**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-MNOP",
  "intent": "CHECK_STATUS",
  "confidence": 0.7,
  "timestamp": "2026-07-03T12:37:00.789Z",
  "execution_time_ms": 9.12,
  "data": {
    "ticket_id": "INC1001",
    "issue": "My VPN is not connecting",
    "priority": "Medium",
    "category": "Network",
    "assigned_team": "IT Infrastructure",
    "status": "Open",
    "created_at": "2026-07-03T12:34:56.789Z",
    "suggested_resolution": "Please reconnect to the VPN and verify your internet connection. If the problem persists, restart your computer.",
    "notes": null
  },
  "error": null,
  "message": "Ticket status retrieved"
}
```

### 5. Conversational Troubleshooting (Laptop Issue)
**Turn 1 - User**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question":"My laptop won't start"}'
```
**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-QRST",
  "intent": "TROUBLESHOOT",
  "confidence": 0.9,
  "conversation_id": "CONV-ABC12345",
  "current_step": 0,
  "next_action": "WAIT_FOR_USER",
  "response": "I'm sorry you're facing this issue. Is the laptop completely dead or does it turn on but show an error?"
}
```

**Turn 2 - User**:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{
  "question": "It's completely dead",
  "conversation_id": "CONV-ABC12345"
}'
```
**Response**:
```json
{
  "success": true,
  "request_id": "REQ-20260703-UVWX",
  "intent": "TROUBLESHOOT",
  "confidence": 1.0,
  "conversation_id": "CONV-ABC12345",
  "current_step": 1,
  "next_action": "WAIT_FOR_USER",
  "response": "Is the charging adapter firmly connected to both the laptop and a power outlet?"
}
```

### 6. Health Check
**Request**:
```bash
curl -X GET "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "0:05:30"
}
```

## Engineering Decisions

- **Offline-only design**: No external APIs, completely self-contained
- **Rule-based intent detection**: Simple and effective for the scope, avoids dependencies on external LLMs; includes confidence scoring
- **JSON as mock database**: Quick to implement and avoids the overhead of a real database
- **Clean architecture**: Clear separation of concerns for maintainability
- **Structured logging**: Comprehensive logging with request IDs, execution times, and context
- **Standardized API responses**: Consistent response format across all endpoints
- **Comprehensive validation**: Checks for empty inputs, max length, and excessive special characters

## Tradeoffs

| Tradeoff | Reasoning |
|----------|-----------|
| No real database | Prioritizes simplicity and speed of implementation |
| Rule-based intent detection | Tradeoff for no external LLM dependencies; less flexible but more reliable and predictable |
| In-memory request state | Avoids database dependencies, but resets on server restart |

## Future Improvements

- Add a real database (PostgreSQL/MySQL)
- Implement user authentication and authorization
- Add more sophisticated intent classification (maybe NLP libraries like spaCy)
- Implement ticket update and resolution features
- Add more comprehensive test coverage
- Containerize with Docker
- Add async database operations
