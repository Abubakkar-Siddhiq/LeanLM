from fastapi import FastAPI
from api.chat.views import router as chat_router

app = FastAPI()
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Hello World"}