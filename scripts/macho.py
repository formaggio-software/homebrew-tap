"""Read Mach-O slices without executing binaries or requiring macOS tools."""

from __future__ import annotations

import struct
from typing import BinaryIO

CPU_NAMES = {0x1000007: "x86_64", 0x100000C: "arm64"}
UNIVERSAL2 = {"x86_64", "arm64"}
THIN = {b"\xcf\xfa\xed\xfe": "<", b"\xfe\xed\xfa\xcf": ">"}
FAT = {
    b"\xca\xfe\xba\xbe": (">", False),
    b"\xbe\xba\xfe\xca": ("<", False),
    b"\xca\xfe\xba\xbf": (">", True),
    b"\xbf\xba\xfe\xca": ("<", True),
}


def slices(stream: BinaryIO) -> list[tuple[str, int, int, str]]:
    stream.seek(0, 2)
    length = stream.tell()
    stream.seek(0)
    header = stream.read(8)
    if len(header) != 8:
        raise ValueError("Truncated Mach-O header")
    magic = header[:4]
    if magic in THIN:
        endian = THIN[magic]
        cpu = struct.unpack(endian + "I", header[4:])[0]
        if cpu not in CPU_NAMES:
            raise ValueError("Unsupported Mach-O CPU")
        return [(CPU_NAMES[cpu], 0, length, endian)]
    if magic not in FAT:
        raise ValueError("Expected a 64-bit Mach-O executable or universal2 fat binary")
    endian, wide = FAT[magic]
    count = struct.unpack(endian + "I", header[4:])[0]
    if count != 2:
        raise ValueError("Universal2 must contain exactly two architecture slices")
    entry_size = 32 if wide else 20
    table_end = 8 + count * entry_size
    records = stream.read(count * entry_size)
    if len(records) != count * entry_size:
        raise ValueError("Truncated universal2 architecture table")
    result = []
    for index in range(count):
        entry = records[index * entry_size : (index + 1) * entry_size]
        cpu = struct.unpack(endian + "I", entry[:4])[0]
        offset, size = struct.unpack(
            endian + ("QQ" if wide else "II"), entry[8 : 24 if wide else 16]
        )
        if cpu not in CPU_NAMES or offset < table_end or size < 8 or offset + size > length:
            raise ValueError("Invalid universal2 architecture slice")
        stream.seek(offset)
        thin = stream.read(8)
        if thin[:4] not in THIN:
            raise ValueError("Universal2 slice is not a 64-bit Mach-O binary")
        thin_endian = THIN[thin[:4]]
        if struct.unpack(thin_endian + "I", thin[4:])[0] != cpu:
            raise ValueError("Universal2 architecture table disagrees with its slice")
        result.append((CPU_NAMES[cpu], offset, size, thin_endian))
    if {entry[0] for entry in result} != UNIVERSAL2:
        raise ValueError("Universal2 requires both x86_64 and arm64 slices")
    first, second = sorted(result, key=lambda entry: entry[1])
    if first[1] + first[2] > second[1]:
        raise ValueError("Overlapping universal2 architecture slices")
    return result


def architectures(stream: BinaryIO) -> set[str]:
    return {entry[0] for entry in slices(stream)}


def minimum_versions(stream: BinaryIO) -> dict[str, tuple[int, int, int]]:
    versions = {}
    for name, offset, size, endian in slices(stream):
        stream.seek(offset)
        header = stream.read(32)
        if len(header) != 32:
            raise ValueError("Truncated Mach-O load-command header")
        count, command_bytes = struct.unpack(endian + "II", header[16:24])
        if 32 + command_bytes > size or count > command_bytes // 8:
            raise ValueError("Invalid Mach-O load-command table")
        cursor = offset + 32
        found = []
        for _ in range(count):
            if cursor + 8 > offset + 32 + command_bytes:
                raise ValueError("Truncated Mach-O load-command table")
            stream.seek(cursor)
            command, command_size = struct.unpack(endian + "II", stream.read(8))
            if command_size < 8 or cursor + command_size > offset + 32 + command_bytes:
                raise ValueError("Invalid Mach-O load command")
            if command in (0x24, 0x32):  # LC_VERSION_MIN_MACOSX, LC_BUILD_VERSION
                if command_size < (16 if command == 0x24 else 24):
                    raise ValueError("Truncated minimum macOS version command")
                if command == 0x32:
                    platform = struct.unpack(endian + "I", stream.read(4))[0]
                    if platform != 1:
                        raise ValueError("Mach-O slice does not target macOS")
                value = struct.unpack(endian + "I", stream.read(4))[0]
                found.append((value >> 16, (value >> 8) & 255, value & 255))
            cursor += command_size
        if not found:
            raise ValueError(f"Missing minimum macOS version for {name}")
        versions[name] = max(found)
    return versions
