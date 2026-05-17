# reset_db.py

from sqlmodel import SQLModel
from db.session import engine

# import all models so metadata registers tables
from db.models import Conversation, Message

print("Dropping all tables...")
SQLModel.metadata.drop_all(engine)

print("Creating fresh tables...")
SQLModel.metadata.create_all(engine)

print("Database reset complete.")