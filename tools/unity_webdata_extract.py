#!/usr/bin/env python3
import sys
from pathlib import Path

HEADER = b"UnityWebData1.0\0"


def extract(data_path: Path, out_dir: Path):
    data = data_path.read_bytes()
    if not data.startswith(HEADER):
        raise SystemExit("unknown data format (missing UnityWebData1.0 header)")

    # layout per Unity loader.js
    # offset 0: header
    # next uint32: directory table end offset (o)
    # then entries until n < o
    def u32_le(offset):
        return int.from_bytes(data[offset:offset+4], "little", signed=False)

    n = len(HEADER)
    o = u32_le(n)
    n += 4

    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    while n < o:
        data_offset = u32_le(n)
        n += 4
        data_length = u32_le(n)
        n += 4
        path_length = u32_le(n)
        n += 4
        rel_bytes = data[n:n+path_length]
        # Some entries contain null padding or binary data; trim at first null.
        if b"\x00" in rel_bytes:
            rel_bytes = rel_bytes.split(b"\x00", 1)[0]
        rel_path = rel_bytes.decode("utf-8", errors="ignore")
        n += path_length

        if not rel_path:
            continue

        # normalize to forward slashes, remove leading slash
        rel_path = rel_path.lstrip("/")
        out_path = out_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data[data_offset:data_offset+data_length])
        count += 1

    return count


def main(argv):
    if len(argv) != 3:
        print("usage: unity_webdata_extract.py <WebGL_*.data> <out_dir>")
        return 2
    data_path = Path(argv[1])
    out_dir = Path(argv[2])
    count = extract(data_path, out_dir)
    print(f"extracted {count} files to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
