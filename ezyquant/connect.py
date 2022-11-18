import os.path

import sqlalchemy as sa

from .errors import InputError
from .reader import SETDataReader, _SETDataReaderCached


def connect_sqlite(sqlite_path: str):
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path: str
        SQLite database location path (e.g. C:/.../ezyquant.db)
    """
    if not os.path.isfile(sqlite_path):
        raise InputError(f"{sqlite_path} is not found")

    engine = sa.create_engine(f"sqlite:///{sqlite_path}")

    _SETDataReaderCached.cache_clear()
    SETDataReader._engine = engine

    return SETDataReader()


def connect_postgres(host: str, username: str, password: str, port: str, database: str):
    """Connect to PostgreSQL database.

    Parameters
    ----------
    host: str
        PostgreSQL host (e.g. localhost)
    username: str
        PostgreSQL username (e.g. postgres)
    password: str
        PostgreSQL password (e.g. password)
    port: str
        PostgreSQL port (e.g. 5432)
    database: str
        PostgreSQL database name (e.g. ezyquant)
    """
    url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    engine = sa.create_engine(url)

    _SETDataReaderCached.cache_clear()
    SETDataReader._engine = engine
    return SETDataReader()
