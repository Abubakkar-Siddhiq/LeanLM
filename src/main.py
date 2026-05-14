from fastapi import FastAPI
from api.chat.views import router as chat_router
from contextlib import asynccontextmanager
from db.session import create_db_and_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("Starting up the application...")
    yield
    print("Shutting down the application...")


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello World"}