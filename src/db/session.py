from sqlmodel import Session, SQLModel, create_engine
import config

engine = create_engine(
    config.DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session