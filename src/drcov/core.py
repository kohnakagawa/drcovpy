import io
import os
import re
from dataclasses import dataclass, field
from typing import BinaryIO, Dict, Tuple, cast

from .cov_info import BBEntry, CodeBlock, CoverageInfo
from .exceptions import InvalidBBTableHeader, InvalidHeader, InvalidModuleTableHeader
from .module_table_entries import get_proper_module_table_entry_cls


@dataclass
class DrCov:
    cov_infos: Dict[int, CoverageInfo] = field(default_factory=dict)

    def __str__(self) -> str:
        return "\n\n".join(
            f"module_id: {i}\n" + str(cov_info)
            for i, cov_info in self.cov_infos.items()
        )

    def import_from_file(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{file_path} does not exist")
        with open(file_path, "rb") as fin:
            self.import_from_binaryio(fin)

    def import_from_bytes(self, data: bytes) -> None:
        self.import_from_binaryio(io.BytesIO(data))

    @staticmethod
    def _is_supported_drcov_version(version: int) -> bool:
        return 2 <= version <= 3

    def import_from_binaryio(self, bio: BinaryIO) -> None:
        version, _ = self._read_header(bio)
        if not self._is_supported_drcov_version(version):
            raise InvalidHeader(f"DRCOV VERSION: {version} is not supported yet")
        self._read_module_table(bio)
        self._read_bb_table(cast(io.BytesIO, bio))

    @staticmethod
    def _read_header(bio: BinaryIO) -> Tuple[int, bytes]:
        version_header = bio.readline()
        if not version_header.startswith(b"DRCOV VERSION:"):
            raise InvalidHeader(version_header.decode("utf-8"))
        flavor_header = bio.readline()
        if not flavor_header.startswith(b"DRCOV FLAVOR: drcov"):
            raise InvalidHeader(flavor_header.decode("utf-8"))

        version = version_header.split(b":")[-1].strip()
        flavor = flavor_header.split(b":")[-1].strip()
        return int(version), flavor

    @staticmethod
    def _is_supported_module_table_ver(mod_table_ver: int) -> bool:
        return 2 <= mod_table_ver <= 5

    @staticmethod
    def _parse_module_table_header(module_table_header_line: bytes) -> Tuple[int, int]:
        # Module Table: version {ver}, count {n_modules}
        mobj = re.fullmatch(
            r"Module Table: version (\d+), count (\d+)", module_table_header_line.decode("utf-8").strip()
        )
        if mobj is None:
            raise InvalidModuleTableHeader(module_table_header_line.decode("utf-8"))
        ver = int(mobj.group(1))
        n_modules = int(mobj.group(2))
        return ver, n_modules

    def _read_module_table(self, bio: BinaryIO) -> None:
        module_table_header_line = bio.readline()
        ver, n_modules = self._parse_module_table_header(module_table_header_line)

        if not self._is_supported_module_table_ver(ver):
            raise InvalidModuleTableHeader(f"Module Table version {ver} is not supported")

        column_header = bio.readline()
        module_table_entry_cls = get_proper_module_table_entry_cls(column_header)
        for _ in range(n_modules):
            module_table_entry = module_table_entry_cls().from_line(bio.readline())
            self.cov_infos[
                module_table_entry.id  # type: ignore
            ] = module_table_entry.to_coverage_info()

    def _read_bb_table(self, bio: io.BytesIO) -> None:
        # BB Table: {count} bbs
        bb_table_header = bio.readline()
        mobj = re.fullmatch(
            r"BB Table: (\d+) bbs", bb_table_header.decode("utf-8").strip()
        )
        if mobj is None:
            raise InvalidBBTableHeader(bb_table_header.decode("utf-8"))
        n_bb_entries = int(mobj.group(1))

        for _ in range(n_bb_entries):
            bb_entry = BBEntry()
            bio.readinto(bb_entry)  # type: ignore
            self.cov_infos[bb_entry.mod_id].passed_blocks.append(
                CodeBlock(bb_entry.start, bb_entry.size)
            )

    def export_specific_module_to_file(self, module_name: str, file_path: str) -> None:
        with open(file_path, "wb") as fout:
            self.export_specific_module_to_binaryio(fout, module_name)

    def export_specific_module_to_binaryio(
        self, bio: BinaryIO, module_name: str
    ) -> None:
        target_mod_id = next(
            i for i, cov_info in self.cov_infos.items() if module_name in cov_info.name
        )
        if target_mod_id is None:
            print(f"{module_name} is not found")
            return
        DrCov.export_to_binaryio(bio, {target_mod_id: self.cov_infos[target_mod_id]})

    def export_to_file(self, file_path: str) -> None:
        with open(file_path, "wb") as fout:
            self.export_to_binaryio(fout, self.cov_infos)

    @staticmethod
    def export_to_binaryio(bio: BinaryIO, cov_infos: Dict[int, CoverageInfo]) -> None:
        DrCov._write_header(bio)
        DrCov._write_module_table(bio, cov_infos)
        DrCov._write_bb_table(bio, cov_infos)

    @staticmethod
    def _write_header(bio: BinaryIO) -> None:
        bio.write(b"DRCOV VERSION: 2\n")
        bio.write(b"DRCOV FLAVOR: drcov\n")

    @staticmethod
    def _write_module_table(bio: BinaryIO, cov_infos: Dict[int, CoverageInfo]) -> None:
        DrCov._write_module_table_header(bio, len(cov_infos))
        for idx, cov_info in cov_infos.items():
            DrCov._write_module_table_entry(bio, idx, cov_info)

    @staticmethod
    def _write_module_table_header(bio: BinaryIO, count: int) -> None:
        bio.write(f"Module Table: version 2, count {count}\n".encode("utf-8"))
        bio.write(b"Columns: id, base, end, entry, checksum, timestamp, path\n")

    @staticmethod
    def _write_module_table_entry(
        bio: BinaryIO, idx: int, cov_info: CoverageInfo
    ) -> None:
        end_addr = cov_info.base_addr + cov_info.module_size
        bio.write(
            f"{idx}, {cov_info.base_addr:#x}, {end_addr:#x}, {0:#016x}, {0:#08x}, {0:#08x}, {cov_info.name}\n".encode(
                "utf-8"
            )
        )

    @staticmethod
    def _write_bb_table(bio: BinaryIO, cov_infos: Dict[int, CoverageInfo]) -> None:
        DrCov._write_bb_table_header(
            bio, sum(len(cov_info.passed_blocks) for _, cov_info in cov_infos.items())
        )

        for idx, cov_info in cov_infos.items():
            for passed_block in cov_info.passed_blocks:
                DrCov._write_bb_table_entry(
                    cast(io.BytesIO, bio),
                    passed_block.passed_rva,
                    passed_block.passed_size,
                    idx,
                )

    @staticmethod
    def _write_bb_table_header(bio: BinaryIO, count: int) -> None:
        bio.write(f"BB Table: {count} bbs\n".encode("utf-8"))

    @staticmethod
    def _write_bb_table_entry(
        bio: io.BytesIO, start_rva: int, bb_size: int, mod_id: int
    ) -> None:
        buffer_ = io.BytesIO()
        buffer_.write(BBEntry(start_rva, bb_size, mod_id))  # type: ignore
        bio.write(buffer_.getvalue())
