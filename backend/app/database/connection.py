from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

from backend.app.config.settings import get_settings


def build_database_url() -> URL:
    settings = get_settings()

    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


def create_database_engine() -> Engine:
    return create_engine(
        build_database_url(),
        pool_pre_ping=True,
    )


engine = create_database_engine()