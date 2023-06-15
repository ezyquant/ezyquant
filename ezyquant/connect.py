import logging
import os
import os.path

import sqlalchemy as sa
from dotenv import load_dotenv

from ezyquant.errors import InputError
from ezyquant.reader import SETDataReader, _SETDataReaderCached

load_dotenv()

logger = logging.getLogger(__name__)


def connect_sqlite(sqlite_path: str):
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path: str
        SQLite database location path (e.g. C:/.../ezyquant.db)
    """
    if not os.path.isfile(sqlite_path):
        msg = f"{sqlite_path} is not found"
        raise InputError(msg)

    url = f"sqlite:///{sqlite_path}?mode=ro"
    return _set_engine(url)


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
    return _set_engine(url)


def _set_engine(url: str):
    engine = sa.create_engine(url)

    _SETDataReaderCached.cache_clear()
    SETDataReader._engine = engine

    return SETDataReader()


EZYQUANT_DATABASE_URI = os.getenv("EZYQUANT_DATABASE_URI")
if EZYQUANT_DATABASE_URI:
    logging.info(
        "EZYQUANT_DATABASE_URI was found in environment variables. Connecting to database..."
    )
    connect_sqlite(EZYQUANT_DATABASE_URI)
