import sys
import os
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from sqlmodel import SQLModel, Session, create_engine

from db.models import User, Conversation


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)

    from db.usage import LLMUsageLog
    from db.provider_keys import ProviderKey
    SQLModel.metadata.create_all(engine, tables=[
        User.__table__,
        Conversation.__table__,
        ProviderKey.__table__,
        LLMUsageLog.__table__,
    ])
    yield engine
    SQLModel.metadata.drop_all(engine, tables=[
        User.__table__,
        Conversation.__table__,
        ProviderKey.__table__,
        LLMUsageLog.__table__,
    ])


@pytest.fixture
def db_session(in_memory_db):
    with Session(in_memory_db) as session:
        yield session


@pytest.fixture
def test_user_id(db_session: Session) -> UUID:
    user = User(supabase_user_id="test-supabase-user", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user.id
