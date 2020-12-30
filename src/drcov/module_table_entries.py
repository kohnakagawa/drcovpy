from dataclasses import asdict, dataclass
from typing import ClassVar, Type, Union, cast

from .cov_info import CoverageInfo
from .exceptions import InvalidModuleTableEntry, InvalidModuleTableHeader


@dataclass
class ModuleTableEntry:
    @classmethod
    def from_instance(cls, instance) -> "ModuleTableEntry":  # type: ignore
        return cls(**asdict(instance))  # type: ignore

    @classmethod
    def from_line(cls, data: bytes) -> "ModuleTableEntry":
        def convert_proper_type(e: bytes) -> Union[int, str]:
            if e.isdigit():
                return int(e)
            elif e.startswith(b"0x"):
                return int(e, 16)
            else:
                return e.decode("utf-8")

        values = [convert_proper_type(i.strip()) for i in data.split(b",")]
        keys = asdict(cls()).keys()
        if len(values) != len(keys):
            raise InvalidModuleTableEntry(data.decode("utf-8"))
        return cls(**dict(zip(keys, values)))  # type: ignore

    def __str__(self) -> str:
        def print_column(k: str, e: Union[str, int]) -> str:
            if k == "id":
                return str(e)
            elif k == "checksum" or k == "timestamp":
                return f"{e:#08x}"
            elif k == "entry":
                return f"{e:#016x}"
            elif k == "path":
                return cast(str, e)
            else:
                return f"{e:#x}"

        return ", ".join(print_column(k, v) for k, v in asdict(self).items())

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo()


def get_proper_module_table_entry_cls(column_header: bytes) -> Type[ModuleTableEntry]:
    column_header = column_header.strip()
    h_to_e = {
        c().column_header: c
        for c in (
            ModuleTableEntryV2Win,
            ModuleTableEntryV3Win,
            ModuleTableEntryV4Win,
            ModuleTableEntryV2Unix,
            ModuleTableEntryV3Unix,
            ModuleTableEntryV4Unix,
        )
    }
    if column_header not in h_to_e.keys():
        raise InvalidModuleTableHeader(column_header.decode("utf-8"))
    return h_to_e[column_header]


@dataclass
class ModuleTableEntryV2Win(ModuleTableEntry):
    # DynamoRIO v7.0.0-RC1, table version 2
    # Columns: id, base, end, entry, checksum, timestamp, path
    id: int = 0
    base: int = 0
    end: int = 0
    entry: int = 0
    checksum: int = 0
    timestamp: int = 0
    path: str = ""
    column_header: ClassVar[
        bytes
    ] = b"Columns: id, base, end, entry, checksum, timestamp, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.base,
            self.end - self.base,
            [],
        )


@dataclass
class ModuleTableEntryV2Unix(ModuleTableEntry):
    # DynamoRIO v7.0.0-RC1, table version 2
    # Columns: id, base, end, entry, path
    id: int = 0
    base: int = 0
    end: int = 0
    entry: int = 0
    path: str = ""
    column_header: ClassVar[bytes] = b"Columns: id, base, end, entry, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.base,
            self.end - self.base,
            [],
        )


@dataclass
class ModuleTableEntryV3Win(ModuleTableEntry):
    # DynamoRIO v7.0.17594B, table version 3
    # Columns: id, containing_id, start, end, entry, checksum, timestamp, path
    id: int = 0
    containing_id: int = 0
    start: int = 0
    end: int = 0
    entry: int = 0
    checksum: int = 0
    timestamp: int = 0
    path: str = ""
    column_header: ClassVar[
        bytes
    ] = b"Columns: id, containing_id, start, end, entry, checksum, timestamp, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.start,
            self.end - self.start,
            [],
        )


@dataclass
class ModuleTableEntryV3Unix(ModuleTableEntry):
    # DynamoRIO v7.0.17594B, table version 3
    # Columns: id, containing_id, start, end, entry, path
    id: int = 0
    containing_id: int = 0
    start: int = 0
    end: int = 0
    entry: int = 0
    path: str = ""
    column_header: ClassVar[
        bytes
    ] = b"Columns: id, containing_id, start, end, entry, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.start,
            self.end - self.start,
            [],
        )


@dataclass
class ModuleTableEntryV4Win(ModuleTableEntry):
    # DynamoRIO v7.0.17640, table version 4
    # Columns: id, containing_id, start, end, entry, offset, checksum, timestamp, path
    id: int = 0
    containing_id: int = 0
    start: int = 0
    end: int = 0
    entry: int = 0
    offset: int = 0
    checksum: int = 0
    timestamp: int = 0
    path: str = ""
    column_header: ClassVar[
        bytes
    ] = b"Columns: id, containing_id, start, end, entry, offset, checksum, timestamp, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.start,
            self.end - self.start,
            [],
        )


@dataclass
class ModuleTableEntryV4Unix(ModuleTableEntry):
    # DynamoRIO v7.0.17640, table version 4
    # Columns: id, containing_id, start, end, entry, offset, path
    id: int = 0
    containing_id: int = 0
    start: int = 0
    end: int = 0
    entry: int = 0
    offset: int = 0
    path: str = ""
    column_header: ClassVar[
        bytes
    ] = b"Columns: id, containing_id, start, end, entry, offset, path"

    def to_coverage_info(self) -> CoverageInfo:
        return CoverageInfo(
            self.path,
            self.start,
            self.end - self.start,
            [],
        )
