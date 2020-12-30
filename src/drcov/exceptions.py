class DrCovBaseException(Exception):
    pass


class InvalidHeader(DrCovBaseException):
    def __init__(self, header: str) -> None:
        self.header = header

    def __str__(self) -> str:
        return f"{self.header} is not valid DrCov header"


class InvalidVersionString(DrCovBaseException):
    def __init__(self, version: str) -> None:
        self.version = version

    def __str__(self) -> str:
        return f"{self.version} is not valid DrCov version"


class InvalidModuleTableHeader(DrCovBaseException):
    def __init__(self, header: str) -> None:
        self.header = header

    def __str__(self) -> str:
        return f"{self.header} is not valid module table header"


class InvalidModuleTableEntry(DrCovBaseException):
    def __init__(self, entry: str) -> None:
        self.entry = entry

    def __str__(self) -> str:
        return f"{self.entry} is not valid module table entry"


class InvalidBBTableHeader(DrCovBaseException):
    def __init__(self, header: str) -> None:
        self.header = header

    def __str__(self) -> str:
        return f"{self.header} is not valid BB table header"
