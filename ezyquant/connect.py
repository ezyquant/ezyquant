import logging
import os
import os.path
from typing import Union

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.engine import URL

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


EZYQUANT_DB_DRIVER = os.getenv("EZYQUANT_DB_DRIVER")
EZYQUANT_DB_USERNAME = os.getenv("EZYQUANT_DB_USERNAME")
EZYQUANT_DB_PASSWORD = os.getenv("EZYQUANT_DB_PASSWORD")
EZYQUANT_DB_HOST = os.getenv("EZYQUANT_DB_HOST")
EZYQUANT_DB_PORT = os.getenv("EZYQUANT_DB_PORT")
EZYQUANT_DB_DATABASE = os.getenv("EZYQUANT_DB_DATABASE")

EZYQUANT_DATABASE_URI = os.getenv("EZYQUANT_DATABASE_URI")

if EZYQUANT_DB_PORT is not None:
    EZYQUANT_DB_PORT = int(EZYQUANT_DB_PORT)

if EZYQUANT_DB_DRIVER is not None:
    logger.info("Environment variables are found. Connecting to database...")
    url = URL.create(
        drivername=EZYQUANT_DB_DRIVER,
        username=EZYQUANT_DB_USERNAME,
        password=EZYQUANT_DB_PASSWORD,
        host=EZYQUANT_DB_HOST,
        port=EZYQUANT_DB_PORT,
        database=EZYQUANT_DB_DATABASE,
    )
    _set_engine(url)

if EZYQUANT_DATABASE_URI is not None:
    logger.critical("Environment variables are found. Connecting to database...")
    url = EZYQUANT_DATABASE_URI
    _set_engine(url)
