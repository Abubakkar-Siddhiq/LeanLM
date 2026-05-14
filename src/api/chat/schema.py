from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The input prompt for the chat model.")