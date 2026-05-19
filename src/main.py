from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.chat.views import router as chat_router
from api.conversation.views import router as conversation_router
from db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Starting up the application...")
    yield
    print("Shutting down the application...")


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello World"}