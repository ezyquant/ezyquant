from . import reader as rd
from .reader import SETDataReader


def connect_sqlite(sqlite_path: str):
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path : str
        path to sqlite file e.g. /path/to/sqlite.db
    """
    rd._set_data_reader_cache.cache_clear()
    SETDataReader._sqlite_path = sqlite_path
    return SETDataReader()
