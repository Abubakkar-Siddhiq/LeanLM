from sqlmodel import Session, SQLModel, create_engine, text
from config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)

def init_db():
    # Enable pgvector extension first
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()
    
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session

def SessionLocal():
    return Session(engine)