from .reader import SETDataReader, _SETDataReaderCached


def connect_sqlite(sqlite_path: str):
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path: str
        SQLite database location path (e.g. C:/.../ezyquant.db)
    """
    _SETDataReaderCached.cache_clear()
    SETDataReader._sqlite_path = sqlite_path
    return SETDataReader()
