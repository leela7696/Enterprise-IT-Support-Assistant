"""FastAPI application entry point."""
import time
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.middleware import RequestContextMiddleware
from app.config import settings
from app.models import HealthResponse, ApiResponse


# Record start time for uptime calculation
START_TIME = time.time()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routes
app.include_router(router, prefix="")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the chat UI home page."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(request: Request):
    """Health check endpoint to verify service is running."""
    uptime_seconds = time.time() - START_TIME
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        uptime=uptime_str
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
