from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.database import close_db
from routes.health import router as health_router
from routes.telegram import router as telegram_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 GlowUpBuddy starting...")
    yield
    close_db()
    print("🛑 GlowUpBuddy shut down.")


app = FastAPI(title="GlowUpBuddy API", lifespan=lifespan)

app.include_router(health_router)
app.include_router(telegram_router)
