from . import utils
from .reader import SETDataReader

SETDataReaderCached = utils.wrap_cache_class(SETDataReader)

sdrc = None


def connect_sqlite(sqlite_path: str) -> SETDataReader:
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path : str
        path to sqlite file e.g. /path/to/sqlite.db
    """
    global sdrc
    sdrc = SETDataReaderCached(sqlite_path)
    return sdrc  # type: ignore


def get_sdrc() -> SETDataReader:
    """Return SETDataReader instance."""
    if sdrc is None:
        raise RuntimeError("Please connect to SQLite database first")
    return sdrc  # type: ignore
