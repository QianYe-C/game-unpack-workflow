#!/usr/bin/env python3
"""Helpers to sync Unity bundle CRC values in PackageManifest files."""

from __future__ import annotations

import re
import shutil
import struct
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

import UnityPy


_HEX32_RE = re.compile(rb"^[0-9a-f]{32}$")
_MANIFEST_GLOB = "PackageManifest_*_*.bytes"


def auto_detect_package_manifest(project_root: Path) -> Optional[Path]:
    candidates = sorted(project_root.rglob(_MANIFEST_GLOB))
    if not candidates:
        return None
    candidates.sort(key=lambda p: (p.stat().st_size, p.stat().st_mtime), reverse=True)
    return candidates[0]


def parse_manifest_bundle_rows(manifest_path: Path) -> List[Dict]:
    data = manifest_path.read_bytes()
    rows: List[Dict] = []

    for pos in range(0, len(data) - 40):
        name_len = struct.unpack_from("<H", data, pos)[0]
        if name_len < 8 or name_len > 192:
            continue

        name_start = pos + 2
        name_end = name_start + name_len
        if name_end + 4 + 2 + 32 > len(data):
            continue

        name_bytes = data[name_start:name_end]
        if not name_bytes.endswith(b".unity3d"):
            continue
        if any(byte < 32 or byte > 126 for byte in name_bytes):
            continue

        crc_offset = name_end
        hash_len = struct.unpack_from("<H", data, crc_offset + 4)[0]
        if hash_len != 32:
            continue

        hash_start = crc_offset + 6
        hash_end = hash_start + 32
        bundle_hash = data[hash_start:hash_end]
        if not _HEX32_RE.match(bundle_hash):
            continue

        rows.append(
            {
                "entryOffset": pos,
                "bundleName": name_bytes.decode("ascii"),
                "bundleHash": bundle_hash.decode("ascii"),
                "manifestCrc": struct.unpack_from("<I", data, crc_offset)[0],
                "crcOffset": crc_offset,
            }
        )

    return rows


def _bundle_payload_bytes(file_obj) -> Optional[bytes]:
    payload = getattr(file_obj, "bytes", None)
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)

    save = getattr(file_obj, "save", None)
    if callable(save):
        saved = save()
        if isinstance(saved, (bytes, bytearray)):
            return bytes(saved)
    return None


def calculate_bundle_content_crc(bundle_path: Path) -> int:
    env = UnityPy.load(str(bundle_path))

    crc = 0
    chunk_count = 0
    for _, file_obj in env.file.files.items():
        payload = _bundle_payload_bytes(file_obj)
        if payload is None:
            continue
        crc = zlib.crc32(payload, crc)
        chunk_count += 1

    if chunk_count == 0:
        # Fallback for unexpected bundle structure.
        crc = zlib.crc32(bundle_path.read_bytes())

    return crc & 0xFFFFFFFF


def extract_bundle_hashes(bundle_rel_paths: Sequence[str]) -> Set[str]:
    hashes: Set[str] = set()
    for rel in bundle_rel_paths:
        name = Path(rel).name.lower()
        if name.endswith(".unity3d") and len(name) >= 40:
            stem = name[:-8]
            if len(stem) == 32 and all(c in "0123456789abcdef" for c in stem):
                hashes.add(stem)
    return hashes


def sync_manifest_bundle_crc(
    manifest_path: Path,
    *,
    asset_dir: Optional[Path] = None,
    bundle_hashes: Optional[Set[str]] = None,
    dry_run: bool = False,
    backup: bool = True,
) -> Dict:
    if asset_dir is None:
        asset_dir = manifest_path.parent

    original = manifest_path.read_bytes()
    rows = parse_manifest_bundle_rows(manifest_path)
    hash_filter = {h.lower() for h in bundle_hashes} if bundle_hashes else None

    updates: List[Dict] = []
    missing: List[str] = []
    errors: List[str] = []
    checked = 0
    patched = bytearray(original)

    for row in rows:
        bundle_hash = row["bundleHash"].lower()
        if hash_filter and bundle_hash not in hash_filter:
            continue

        checked += 1
        bundle_path = asset_dir / f"{bundle_hash}.unity3d"
        if not bundle_path.is_file():
            missing.append(bundle_path.name)
            continue

        try:
            calculated = calculate_bundle_content_crc(bundle_path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{bundle_path.name}: {exc}")
            continue

        manifest_crc = int(row["manifestCrc"])
        if calculated == manifest_crc:
            continue

        struct.pack_into("<I", patched, int(row["crcOffset"]), calculated)
        updates.append(
            {
                "bundleName": row["bundleName"],
                "bundleHash": bundle_hash,
                "oldCrcHex": f"{manifest_crc:08x}",
                "newCrcHex": f"{calculated:08x}",
                "crcOffset": int(row["crcOffset"]),
            }
        )

    backup_path: Optional[Path] = None
    if updates and not dry_run:
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = manifest_path.with_name(
                f"{manifest_path.name}.bak_crcsync_{timestamp}"
            )
            shutil.copy2(manifest_path, backup_path)
        manifest_path.write_bytes(patched)

    return {
        "manifestPath": str(manifest_path),
        "assetDir": str(asset_dir),
        "bundleRowCount": len(rows),
        "checkedBundleCount": checked,
        "updatedBundleCount": len(updates),
        "missingBundleCount": len(missing),
        "errorCount": len(errors),
        "backupPath": str(backup_path) if backup_path else None,
        "updates": updates,
        "missingBundles": missing,
        "errors": errors,
    }
