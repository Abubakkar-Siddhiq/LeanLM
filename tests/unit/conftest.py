import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from sqlmodel import SQLModel, Session, create_engine


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)

    from db.usage import LLMUsageLog
    SQLModel.metadata.create_all(engine, tables=[LLMUsageLog.__table__])
    yield engine
    SQLModel.metadata.drop_all(engine, tables=[LLMUsageLog.__table__])


@pytest.fixture
def db_session(in_memory_db):
    with Session(in_memory_db) as session:
        yield session
