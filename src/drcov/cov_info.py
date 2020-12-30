from ctypes import Structure, c_uint16, c_uint32
from dataclasses import dataclass, field
from typing import List


@dataclass
class CodeBlock:
    passed_rva: int = 0
    passed_size: int = 0

    def __str__(self) -> str:
        return f"rva: {self.passed_rva:#x}, size: {self.passed_size:#x}"


@dataclass
class CoverageInfo:
    name: str = ""
    base_addr: int = 0
    module_size: int = 0
    passed_blocks: List[CodeBlock] = field(default_factory=list)

    def __str__(self) -> str:
        module_info = f"module: {self.name}, base_addr: {self.base_addr:#x}, module_size: {self.module_size:#x}\n"
        blocks_info = "\n".join(str(b) for b in self.passed_blocks)
        return module_info + blocks_info


class BBEntry(Structure):
    """
    typedef struct _bb_entry_t {
        uint32_t start;  /* offset from the image base */
        uint16_t size;
        uint16_t mod_id;
    } bb_entry_t;
    """

    _fields_ = (("start", c_uint32), ("size", c_uint16), ("mod_id", c_uint16))
