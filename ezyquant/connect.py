from . import utils
from .reader import SETDataReader

SETDataReaderCached = utils.wrap_cache_class(SETDataReader)

sdr = None


def connect_sqlite(sqlite_path: str) -> SETDataReader:
    """Connect to SQLite database.

    Parameters
    ----------
    sqlite_path : str
        path to sqlite file e.g. /path/to/sqlite.db
    """
    global sdr
    sdr = SETDataReaderCached(sqlite_path)
    return sdr  # type: ignore


def _get_sdr() -> SETDataReader:
    """Return SETDataReader instance."""
    if sdr is None:
        raise RuntimeError("Please connect to SQLite database first")
    return sdr  # type: ignore
