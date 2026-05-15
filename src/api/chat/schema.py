from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The input prompt for the chat model.")
    conversation_id: Optional[UUID] = Field(None, description="The ID of the conversation to which this message belongs.")