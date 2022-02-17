class SETDataReader:
    def __init__(self, sqlite_path: str) -> None:
        """
        The __init__ function is called when an instance of a class is created

        :param sqlite_path: The path to the SQLite database file
        :type sqlite_path: str
        """
        self.__sqlite_path = sqlite_path
