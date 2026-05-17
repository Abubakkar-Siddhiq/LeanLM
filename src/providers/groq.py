from dotenv import load_dotenv
import os
from groq import Groq
from config.prompts import Prompts

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=api_key)

class GroqProvider:
    def __init__(self):
        pass

    async def generate(self, model: str, messages: list):
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )

        return completion.choices[0].message.content