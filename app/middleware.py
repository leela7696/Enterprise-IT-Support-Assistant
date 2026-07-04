"""Request middleware for request ID generation and execution time measurement."""
import time
import uuid
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import REQUEST_ID_PREFIX


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to attach request ID, start time, and other context to requests."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        date_str = datetime.now().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:4].upper()
        request_id = f"{REQUEST_ID_PREFIX}-{date_str}-{random_suffix}"
        
        # Record start time
        start_time = time.perf_counter()
        
        # Attach to request state
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
