#!/usr/bin/env python3
import sys
from pathlib import Path

HEADER = b"UnityWebData1.0\0"


def pack(src_dir: Path, out_path: Path):
    # collect files
    files = []
    for p in sorted(src_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(src_dir).as_posix()
            files.append((rel, p.read_bytes()))

    # build header + directory table
    # We'll build entries then append file data.
    # Offsets are absolute in the final file.

    # placeholder for header and directory table
    entries = []
    dir_blob = bytearray()

    # reserved placeholder for o and reserved
    # We'll compute o after building entries.
    # We need to know data offsets, which come after directory table.

    # First pass: compute directory table size
    for rel, content in files:
        rel_bytes = rel.encode("utf-8")
        entry_size = 4 + 4 + 4 + len(rel_bytes)
        entries.append((rel, content, rel_bytes, entry_size))

    # directory table layout: HEADER + o(u32) + entries
    dir_size = len(HEADER) + 4 + sum(e[3] for e in entries)

    # data section starts at dir_size
    data_offset = dir_size

    for rel, content, rel_bytes, entry_size in entries:
        # write entry: offset, length, path_length, path
        dir_blob += data_offset.to_bytes(4, "little")
        dir_blob += len(content).to_bytes(4, "little")
        dir_blob += len(rel_bytes).to_bytes(4, "little")
        dir_blob += rel_bytes
        data_offset += len(content)

    o = len(HEADER) + 4 + len(dir_blob)

    out = bytearray()
    out += HEADER
    out += o.to_bytes(4, "little")
    out += dir_blob

    # append file data in same order
    for rel, content, rel_bytes, entry_size in entries:
        out += content

    out_path.write_bytes(out)
    return len(files)


def main(argv):
    if len(argv) != 3:
        print("usage: unity_webdata_pack.py <src_dir> <out_data_path>")
        return 2
    src_dir = Path(argv[1])
    out_path = Path(argv[2])
    count = pack(src_dir, out_path)
    print(f"packed {count} files into {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
