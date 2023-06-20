import logging
import os
import os.path
from typing import Union

import sqlalchemy as sa
from dotenv import find_dotenv, load_dotenv
from sqlalchemy.engine import URL

from ezyquant.errors import InputError
from ezyquant.reader import SETDataReader, _SETDataReaderCached

dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

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

    url = URL.create(drivername="sqlite", database=sqlite_path, query={"mode": "ro"})

    return _set_engine(url)


def connect_postgres(host: str, username: str, password: str, port: int, database: str):
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
    url = URL.create(
        drivername="postgresql",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return _set_engine(url)


def _set_engine(url: Union[str, URL]):
    engine = sa.create_engine(url)

    _SETDataReaderCached.cache_clear()
    SETDataReader._engine = engine

    return SETDataReader()


EZYQUANT_DATABASE_DRIVER = os.getenv("EZYQUANT_DATABASE_DRIVER")
"""Environment variable for database driver."""
EZYQUANT_DATABASE_USERNAME = os.getenv("EZYQUANT_DATABASE_USERNAME")
"""Environment variable for database username."""
EZYQUANT_DATABASE_PASSWORD = os.getenv("EZYQUANT_DATABASE_PASSWORD")
"""Environment variable for database password."""
EZYQUANT_DATABASE_HOST = os.getenv("EZYQUANT_DATABASE_HOST")
"""Environment variable for database host."""
EZYQUANT_DATABASE_PORT = os.getenv("EZYQUANT_DATABASE_PORT")
"""Environment variable for database port."""
EZYQUANT_DATABASE_NAME = os.getenv("EZYQUANT_DATABASE_NAME")
"""Environment variable for database name."""

EZYQUANT_DATABASE_URI = os.getenv("EZYQUANT_DATABASE_URI")
"""Environment variable for database URI."""

if EZYQUANT_DATABASE_PORT is not None:
    EZYQUANT_DATABASE_PORT = int(EZYQUANT_DATABASE_PORT)

if EZYQUANT_DATABASE_DRIVER is not None:
    logger.info("Environment variables are found. Connecting to database...")
    url = URL.create(
        drivername=EZYQUANT_DATABASE_DRIVER,
        username=EZYQUANT_DATABASE_USERNAME,
        password=EZYQUANT_DATABASE_PASSWORD,
        host=EZYQUANT_DATABASE_HOST,
        port=EZYQUANT_DATABASE_PORT,
        database=EZYQUANT_DATABASE_NAME,
    )
    _set_engine(url)

if EZYQUANT_DATABASE_URI is not None:
    logger.info("Environment variables are found. Connecting to database...")
    url = EZYQUANT_DATABASE_URI
    _set_engine(url)
