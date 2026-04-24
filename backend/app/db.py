from sqlmodel import SQLModel, create_engine, Session
from app.config.settings import settings

# Engine using configured DATABASE URL
engine = create_engine(settings.genlogs_database_url, echo=False)

# Simple session factory for use in application code and scripts
def get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Create database tables from SQLModel metadata.

    Intended for use in development and tests. Production deployments should use
    Alembic migrations instead.
    """
    SQLModel.metadata.create_all(engine)
