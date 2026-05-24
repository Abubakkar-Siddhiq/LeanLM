# reset_db.py

from sqlmodel import SQLModel
from db.session import engine

# import all models so metadata registers tables
from db.models import User, Conversation, Message
from db.provider_keys import ProviderKey
from db.usage import LLMUsageLog

print("Dropping all tables...")
SQLModel.metadata.drop_all(engine)

print("Creating fresh tables...")
SQLModel.metadata.create_all(engine)

print("Database reset complete.")