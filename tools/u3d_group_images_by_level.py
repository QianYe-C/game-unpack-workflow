#!/usr/bin/env python3
"""Group exported U3D images by level id using PackageManifest config mapping."""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


LEVEL_FROM_ADDRESS_PATTERNS = (
    re.compile(r"^atlases/level_([a-z0-9_-]+)_atlas\.spriteatlas$", re.IGNORECASE),
    re.compile(r"^levels/level_([a-z0-9_-]+)\.asset$", re.IGNORECASE),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve_path(base: Path, arg: str) -> Path:
    p = Path(arg)
    return p if p.is_absolute() else (base / p)


def _iter_printable_strings(data: bytes, min_len: int = 6) -> Iterable[str]:
    buf = bytearray()
    for byte in data:
        if 32 <= byte <= 126:
            buf.append(byte)
            continue
        if len(buf) >= min_len:
            yield buf.decode("ascii", errors="ignore")
        buf.clear()
    if len(buf) >= min_len:
        yield buf.decode("ascii", errors="ignore")


def _extract_bundle_hash_pairs(manifest_path: Path) -> List[Tuple[str, str]]:
    lines: List[str] = []
    try:
        result = subprocess.run(
            ["strings", "-n", "6", str(manifest_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        lines = result.stdout.splitlines()
    except Exception:  # noqa: BLE001
        data = manifest_path.read_bytes()
        lines = list(_iter_printable_strings(data, min_len=6))

    pairs: List[Tuple[str, str]] = []
    pending_bundle: Optional[str] = None

    for token in lines:
        if pending_bundle:
            hash_match = re.search(r"([0-9a-f]{32})", token)
            if hash_match:
                pairs.append((pending_bundle, hash_match.group(1).lower()))
                pending_bundle = None
                continue

        bundle_match = re.search(r"([a-z0-9_]+\.unity3d)", token, re.IGNORECASE)
        if bundle_match:
            pending_bundle = bundle_match.group(1).lower()
            trailing = token[bundle_match.end() :]
            hash_match = re.search(r"([0-9a-f]{32})", trailing)
            if hash_match:
                pairs.append((pending_bundle, hash_match.group(1).lower()))
                pending_bundle = None

    return pairs


def _extract_level_id_from_address(asset_address: str) -> Optional[str]:
    for pattern in LEVEL_FROM_ADDRESS_PATTERNS:
        match = pattern.match(asset_address)
        if match:
            return match.group(1).upper()
    return None


def _is_ascii_bytes(data: bytes) -> bool:
    return bool(data) and all(32 <= x < 127 for x in data)


def _parse_asset_entries_from_offset(
    data: bytes, start: int
) -> Tuple[List[Tuple[str, str, int, List[int], List[str], int]], int]:
    pos = start
    items: List[Tuple[str, str, int, List[int], List[str], int]] = []

    while pos + 2 <= len(data):
        addr_len = struct.unpack_from("<H", data, pos)[0]
        if not (1 <= addr_len <= 256):
            break
        pos += 2
        if pos + addr_len > len(data):
            break
        addr_bytes = data[pos : pos + addr_len]
        if not _is_ascii_bytes(addr_bytes):
            break
        addr = addr_bytes.decode("ascii")
        pos += addr_len

        if pos + 2 > len(data):
            break
        path_len = struct.unpack_from("<H", data, pos)[0]
        if not (1 <= path_len <= 512):
            break
        pos += 2
        if pos + path_len > len(data):
            break
        path_bytes = data[pos : pos + path_len]
        if not _is_ascii_bytes(path_bytes):
            break
        path = path_bytes.decode("ascii")
        pos += path_len

        if pos + 4 > len(data):
            break
        unk = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        tag_count = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if tag_count > 32:
            break

        tags: List[str] = []
        tag_ok = True
        for _ in range(tag_count):
            if pos + 2 > len(data):
                tag_ok = False
                break
            tag_len = struct.unpack_from("<H", data, pos)[0]
            pos += 2
            if not (0 <= tag_len <= 128) or pos + tag_len > len(data):
                tag_ok = False
                break
            tag_bytes = data[pos : pos + tag_len]
            if tag_len > 0 and not _is_ascii_bytes(tag_bytes):
                tag_ok = False
                break
            tags.append(tag_bytes.decode("ascii") if tag_len else "")
            pos += tag_len
        if not tag_ok:
            break

        if pos + 6 > len(data):
            break
        bundle_index = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        dep_count = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if dep_count > 128 or pos + dep_count * 4 > len(data):
            break
        deps = [
            struct.unpack_from("<I", data, pos + i * 4)[0] for i in range(dep_count)
        ]
        pos += dep_count * 4

        items.append((addr, path, bundle_index, deps, tags, unk))

    return items, pos


def _parse_asset_entries(manifest_path: Path) -> List[Tuple[str, str, int, List[int], List[str], int]]:
    data = manifest_path.read_bytes()
    best_items: List[Tuple[str, str, int, List[int], List[str], int]] = []

    # Search header area for asset table start, then keep the longest valid parse.
    for start in range(0, min(256, len(data) - 2)):
        items, _ = _parse_asset_entries_from_offset(data, start)
        if len(items) > len(best_items):
            best_items = items

    return best_items


def _auto_detect_manifest(mapping: Dict) -> Optional[Path]:
    asset_dir_value = mapping.get("assetDir")
    if not isinstance(asset_dir_value, str) or not asset_dir_value:
        return None
    asset_dir = Path(asset_dir_value)
    if not asset_dir.is_dir():
        return None
    candidates = sorted(asset_dir.glob("PackageManifest_*_*.bytes"))
    if not candidates:
        return None
    # Stable preference: largest file then latest mtime.
    candidates.sort(key=lambda p: (p.stat().st_size, p.stat().st_mtime), reverse=True)
    return candidates[0]


def _cleanup_empty_dirs(images_dir: Path) -> int:
    removed = 0
    if not images_dir.is_dir():
        return removed
    for directory in sorted(images_dir.rglob("*"), reverse=True):
        if directory.is_dir():
            try:
                directory.rmdir()
                removed += 1
            except OSError:
                pass
    return removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Group images into images/<LEVEL_ID>/ based on PackageManifest "
            "bundle mapping instead of texture filename parsing."
        )
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="sourceImages project directory, e.g. sourceImages/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--mapping",
        default="image_mapping.json",
        help="Mapping file path relative to --source-root or absolute path.",
    )
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Manifest file path relative to --source-root or absolute path.",
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help=(
            "PackageManifest_*.bytes path. If omitted, auto-detect from mapping.assetDir."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).resolve()
    mapping_path = _resolve_path(source_root, args.mapping).resolve()
    manifest_path = _resolve_path(source_root, args.manifest).resolve()

    if not source_root.is_dir():
        raise SystemExit(f"source-root not found: {source_root}")
    if not mapping_path.is_file():
        raise SystemExit(f"mapping not found: {mapping_path}")

    with mapping_path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)
    if mapping.get("schema") not in ("u3d-image-mapping-v1", "u3d-source-images-v1"):
        raise SystemExit(f"Unsupported mapping schema: {mapping.get('schema')}")

    package_manifest_path: Optional[Path]
    if args.package_manifest:
        package_manifest_path = _resolve_path(source_root, args.package_manifest).resolve()
    else:
        package_manifest_path = _auto_detect_manifest(mapping)
    if not package_manifest_path or not package_manifest_path.is_file():
        raise SystemExit(
            "Package manifest not found. Provide --package-manifest "
            "or ensure mapping.assetDir contains PackageManifest_*_*.bytes."
        )

    bundle_hash_pairs = _extract_bundle_hash_pairs(package_manifest_path)
    if not bundle_hash_pairs:
        raise SystemExit(f"Failed to parse bundle/hash pairs from: {package_manifest_path}")

    asset_entries = _parse_asset_entries(package_manifest_path)
    if not asset_entries:
        raise SystemExit(f"Failed to parse asset entries from: {package_manifest_path}")

    hash_to_level_set: Dict[str, Set[str]] = defaultdict(set)
    level_to_bundle_items: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    unmatched_asset_addresses = 0
    invalid_bundle_indices = 0
    for asset_address, _asset_path, bundle_index, _deps, _tags, _unk in asset_entries:
        level_id = _extract_level_id_from_address(asset_address)
        if not level_id:
            unmatched_asset_addresses += 1
            continue
        if bundle_index >= len(bundle_hash_pairs):
            invalid_bundle_indices += 1
            continue
        bundle_name, bundle_hash = bundle_hash_pairs[bundle_index]
        hash_to_level_set[bundle_hash].add(level_id)
        level_to_bundle_items[level_id].append(
            {"bundleName": bundle_name, "hash": bundle_hash}
        )

    hash_to_level: Dict[str, str] = {}
    ambiguous_hash_levels: Dict[str, List[str]] = {}
    for bundle_hash, level_ids in hash_to_level_set.items():
        if len(level_ids) == 1:
            hash_to_level[bundle_hash] = next(iter(level_ids))
        elif len(level_ids) > 1:
            ambiguous_hash_levels[bundle_hash] = sorted(level_ids)

    entries = [
        entry
        for entry in mapping.get("entries", [])
        if entry.get("kind") == "Texture2D" and "exportPath" in entry and "bundleFile" in entry
    ]
    if not entries:
        print("[group] No exportable Texture2D entries found.")
        return 0

    images_dir = source_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    moved = 0
    unchanged = 0
    missing_files = 0
    root_images = 0
    grouped_images = 0
    level_image_counts: Dict[str, int] = defaultdict(int)

    for entry in entries:
        src_rel = Path(entry["exportPath"])
        src_abs = source_root / src_rel
        if not src_abs.is_file():
            missing_files += 1
            continue

        bundle_file = str(entry.get("bundleFile", ""))
        bundle_hash = bundle_file[:-8].lower() if bundle_file.lower().endswith(".unity3d") else ""
        level_id = hash_to_level.get(bundle_hash)

        if level_id:
            dst_rel = Path("images") / level_id / src_rel.name
            level_image_counts[level_id] += 1
            entry["levelId"] = level_id
            grouped_images += 1
        else:
            dst_rel = src_rel
            entry.pop("levelId", None)
            root_images += 1

        dst_abs = source_root / dst_rel
        if src_abs.resolve() == dst_abs.resolve():
            unchanged += 1
            entry["exportPath"] = dst_rel.as_posix()
            continue

        dst_abs.parent.mkdir(parents=True, exist_ok=True)
        src_abs.rename(dst_abs)
        entry["exportPath"] = dst_rel.as_posix()
        moved += 1

    removed_dirs = _cleanup_empty_dirs(images_dir)

    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    level_map = {
        "schema": "u3d-level-bundle-map-v2",
        "generatedAt": _utc_now(),
        "sourceRoot": str(source_root),
        "mappingFile": str(mapping_path),
        "packageManifestFile": str(package_manifest_path),
        "summary": {
            "assetEntryCount": len(asset_entries),
            "bundleHashPairCount": len(bundle_hash_pairs),
            "bundleHashUniqueCount": len({h for _, h in bundle_hash_pairs}),
            "bundleWithLevelCount": len(hash_to_level),
            "assetAddressWithoutLevelCount": unmatched_asset_addresses,
            "assetInvalidBundleIndexCount": invalid_bundle_indices,
            "ambiguousHashLevelCount": len(ambiguous_hash_levels),
            "levelCount": len(level_to_bundle_items),
            "groupedImages": grouped_images,
            "rootImages": root_images,
            "imagesMoved": moved,
            "imagesUnchanged": unchanged,
            "imagesMissing": missing_files,
        },
        "hashToLevel": dict(sorted(hash_to_level.items())),
        "ambiguousHashToLevels": ambiguous_hash_levels,
        "levels": [
            {
                "levelId": level_id,
                "imageCount": level_image_counts.get(level_id, 0),
                "bundleCount": len(level_to_bundle_items[level_id]),
                "bundles": sorted(
                    level_to_bundle_items[level_id], key=lambda item: item["bundleName"]
                ),
            }
            for level_id in sorted(level_to_bundle_items.keys())
        ],
    }
    level_map_path = source_root / "level_bundle_mapping.json"
    with level_map_path.open("w", encoding="utf-8") as f:
        json.dump(level_map, f, ensure_ascii=False, indent=2)

    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["levelGrouping"] = {
            "enabled": True,
            "groupedBy": "PackageManifest asset entries (address + bundleIndex)",
            "mappingFile": "level_bundle_mapping.json",
            "packageManifestFile": str(package_manifest_path),
            "levelFolderRoot": "images",
            "levelCount": len(level_to_bundle_items),
            "bundleWithLevelCount": len(hash_to_level),
            "groupedImages": grouped_images,
            "rootImages": root_images,
        }
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[group] source_root         : {source_root}")
    print(f"[group] package_manifest    : {package_manifest_path}")
    print(f"[group] mapping            : {mapping_path}")
    print(f"[group] level_map          : {level_map_path}")
    print(f"[group] asset entries      : {len(asset_entries)}")
    print(f"[group] bundle/hash parsed : {len(bundle_hash_pairs)} pairs")
    print(f"[group] unique hash count   : {len({h for _, h in bundle_hash_pairs})}")
    print(f"[group] bundle->level      : {len(hash_to_level)}")
    print(f"[group] levels             : {len(level_to_bundle_items)}")
    print(f"[group] grouped images     : {grouped_images}")
    print(f"[group] root images        : {root_images}")
    print(f"[group] moved              : {moved}")
    print(f"[group] unchanged          : {unchanged}")
    print(f"[group] missing files      : {missing_files}")
    print(f"[group] removed empty dirs : {removed_dirs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
