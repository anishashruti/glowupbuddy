"""FastAPI entry point for GlowUpBuddy ADK backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from google.adk.runners import InMemoryRunner

from config.database import close_db
from flows.morning_flow import morning_flow
from routes.telegram import router as telegram_router

_runner: InMemoryRunner | None = None


def get_runner() -> InMemoryRunner:
    """Return the singleton ADK runner for the morning flow."""
    global _runner
    if _runner is None:
        _runner = InMemoryRunner(agent=morning_flow, app_name="glowupbuddy")
    return _runner


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the runner on startup
    get_runner()
    yield
    close_db()


app = FastAPI(title="GlowUpBuddy ADK", lifespan=lifespan)
app.include_router(telegram_router)


@app.get("/health")
async def health():
    return {"status": "ok", "backend": "adk"}
