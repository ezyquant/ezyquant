from .reader import SETDataReader, _SETDataReaderCached


def connect_sqlite(sqlite_path: str):
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path : str
        path to sqlite file e.g. /path/to/sqlite.db
    """
    _SETDataReaderCached.cache_clear()
    SETDataReader._sqlite_path = sqlite_path
    return SETDataReader()
