#!/usr/bin/env python3
"""Regroup exported U3D images by mode folders: Main_Level_N / Story_N / Others."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def load_helper(script_path: Path):
    spec = importlib.util.spec_from_file_location("u3d_group_images_by_level", script_path)
    module = importlib.util.module_from_spec(spec)
    if not spec.loader:
        raise RuntimeError(f"Failed to load helper script: {script_path}")
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Group images to images/Main_Level_N, images/Story_N, images/Others "
            "based on SequentialLevelDataBase + PackageManifest story config."
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
        help="Mapping file path (relative to --source-root or absolute).",
    )
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Manifest file path (relative to --source-root or absolute).",
    )
    parser.add_argument(
        "--sequential-map",
        default="sequential_level_data_map.json",
        help="Sequential map JSON path (relative to --source-root or absolute).",
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help=(
            "PackageManifest_*.bytes path (relative/absolute). If omitted, use "
            "sequential_map.packageManifestFile."
        ),
    )
    parser.add_argument(
        "--helper-script",
        default="tools/u3d_group_images_by_level.py",
        help="Helper script that provides PackageManifest parsing functions.",
    )
    return parser.parse_args()


def cleanup_empty_dirs(images_dir: Path) -> int:
    removed = 0
    if not images_dir.is_dir():
        return removed
    for directory in sorted(images_dir.rglob("*"), reverse=True):
        if not directory.is_dir():
            continue
        try:
            directory.rmdir()
            removed += 1
        except OSError:
            pass
    return removed


def story_rows_from_manifest(
    asset_entries: List[Tuple[str, str, int, List[int], List[str], int]],
    bundle_hash_pairs: List[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    story_index = 0
    for entry_index, (address, _asset_path, bundle_index, deps, _tags, _unk) in enumerate(asset_entries):
        if not (address.startswith("storylevels/level_") and address.endswith(".asset")):
            continue
        story_index += 1
        level_name, level_hash = bundle_hash_pairs[bundle_index]
        atlas_items: List[Dict[str, Any]] = []
        for dep_index in deps:
            if dep_index >= len(bundle_hash_pairs):
                continue
            dep_name, dep_hash = bundle_hash_pairs[dep_index]
            if dep_name.startswith("atlases_level_"):
                atlas_items.append(
                    {
                        "depBundleIndex": dep_index,
                        "atlasBundleName": dep_name,
                        "atlasBundleHash": dep_hash,
                    }
                )
        rows.append(
            {
                "storyIndex": story_index,
                "entryIndex": entry_index,
                "assetAddress": address,
                "levelBundleName": level_name,
                "levelBundleHash": level_hash,
                "atlasItems": atlas_items,
            }
        )
    return rows


def ensure_unique_destination(dst_abs: Path) -> Path:
    if not dst_abs.exists():
        return dst_abs
    stem = dst_abs.stem
    suffix = dst_abs.suffix
    parent = dst_abs.parent
    index = 1
    while True:
        candidate = parent / f"{stem}__dup{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()

    source_root = resolve_path(cwd, args.source_root).resolve()
    mapping_path = resolve_path(source_root, args.mapping).resolve()
    manifest_path = resolve_path(source_root, args.manifest).resolve()
    sequential_map_path = resolve_path(source_root, args.sequential_map).resolve()
    helper_script_path = resolve_path(cwd, args.helper_script).resolve()

    if not source_root.is_dir():
        raise SystemExit(f"source-root not found: {source_root}")
    if not mapping_path.is_file():
        raise SystemExit(f"mapping file not found: {mapping_path}")
    if not sequential_map_path.is_file():
        raise SystemExit(f"sequential map not found: {sequential_map_path}")
    if not helper_script_path.is_file():
        raise SystemExit(f"helper-script not found: {helper_script_path}")

    with mapping_path.open("r", encoding="utf-8") as f:
        mapping = json.load(f)
    with sequential_map_path.open("r", encoding="utf-8") as f:
        sequential_map = json.load(f)

    if args.package_manifest:
        package_manifest_path = resolve_path(cwd, args.package_manifest).resolve()
    else:
        from_seq = sequential_map.get("packageManifestFile", "")
        package_manifest_path = Path(from_seq).resolve() if isinstance(from_seq, str) and from_seq else None
    if not package_manifest_path or not package_manifest_path.is_file():
        raise SystemExit("PackageManifest not found. Use --package-manifest.")

    helper = load_helper(helper_script_path)
    bundle_hash_pairs = helper._extract_bundle_hash_pairs(package_manifest_path)
    asset_entries = helper._parse_asset_entries(package_manifest_path)

    # hash -> folder mappings
    hash_to_folder: Dict[str, str] = {}
    collisions: Dict[str, List[str]] = defaultdict(list)

    def add_hash_folder(bundle_hash: Optional[str], folder: str) -> None:
        if not bundle_hash:
            return
        old = hash_to_folder.get(bundle_hash)
        if old and old != folder:
            collisions[bundle_hash].extend([old, folder])
            hash_to_folder.pop(bundle_hash, None)
            return
        hash_to_folder[bundle_hash] = folder

    # Any bundle hash referenced by a level row (level bundle + deps) is treated
    # as level-related. Unmapped level-related textures fall into Others.
    level_related_hashes: set[str] = set()
    for row in sequential_map.get("levels", []):
        level_hash = row.get("levelBundleHash")
        if isinstance(level_hash, str) and level_hash:
            level_related_hashes.add(level_hash.lower())
        for dep in row.get("deps") or []:
            dep_hash = dep.get("depBundleHash") if isinstance(dep, dict) else None
            if isinstance(dep_hash, str) and dep_hash:
                level_related_hashes.add(dep_hash.lower())
        for atlas_item in row.get("resolvedAtlas") or []:
            atlas_hash = atlas_item.get("depBundleHash") if isinstance(atlas_item, dict) else None
            if isinstance(atlas_hash, str) and atlas_hash:
                level_related_hashes.add(atlas_hash.lower())

    # Main_Level_N from SequentialLevelDataBase
    main_rows: List[Dict[str, Any]] = []
    for row in sequential_map.get("levels", []):
        main = row.get("mainLevel") or {}
        if not main.get("isMainLevel"):
            continue
        mode_level = main.get("modeLevel")
        if not isinstance(mode_level, int):
            continue
        folder = f"Main_Level_{mode_level}"
        level_hash = row.get("levelBundleHash")
        add_hash_folder(level_hash, folder)
        for atlas_item in row.get("resolvedAtlas") or []:
            add_hash_folder(atlas_item.get("depBundleHash"), folder)
        main_rows.append(
            {
                "assetAddress": row.get("assetAddress"),
                "modeLevel": mode_level,
                "levelBundleHash": level_hash,
                "folder": folder,
            }
        )

    # Story_N from PackageManifest storylevels/level_*.asset order.
    story_rows = story_rows_from_manifest(asset_entries, bundle_hash_pairs)
    story_atlas_hash_to_index: Dict[str, int] = {}
    story_ambiguous_hashes: Dict[str, List[int]] = defaultdict(list)
    for story in story_rows:
        folder = f"Story_{story['storyIndex']}"
        # Do not map shared story level bundle hash (same bundle carries all stories).
        for atlas_item in story.get("atlasItems", []):
            atlas_hash = atlas_item.get("atlasBundleHash")
            if not atlas_hash:
                continue
            old_idx = story_atlas_hash_to_index.get(atlas_hash)
            if old_idx is not None and old_idx != story["storyIndex"]:
                story_ambiguous_hashes[atlas_hash].extend([old_idx, story["storyIndex"]])
                continue
            story_atlas_hash_to_index[atlas_hash] = story["storyIndex"]
            add_hash_folder(atlas_hash, folder)

    # Clean ambiguous story hashes out of mapping.
    for bundle_hash, index_list in story_ambiguous_hashes.items():
        hash_to_folder.pop(bundle_hash, None)
        collisions[bundle_hash].extend([f"Story_{i}" for i in index_list])

    entries = [
        entry
        for entry in mapping.get("entries", [])
        if entry.get("kind") == "Texture2D" and "exportPath" in entry and "bundleFile" in entry
    ]

    images_dir = source_root / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    moved = 0
    unchanged = 0
    missing = 0
    mode_counts: Dict[str, int] = defaultdict(int)
    collision_renamed = 0

    for entry in entries:
        src_rel = Path(entry["exportPath"])
        src_abs = source_root / src_rel
        if not src_abs.is_file():
            missing += 1
            continue

        bundle_file = str(entry.get("bundleFile", ""))
        bundle_hash = bundle_file[:-8].lower() if bundle_file.lower().endswith(".unity3d") else ""
        folder = hash_to_folder.get(bundle_hash)
        if folder is None:
            folder = "Others" if bundle_hash in level_related_hashes else ""

        if folder:
            dst_rel = Path("images") / folder / src_abs.name
            mode_key = folder
        else:
            dst_rel = Path("images") / src_abs.name
            mode_key = "Root"
        dst_abs = source_root / dst_rel
        if src_abs.resolve() == dst_abs.resolve():
            unchanged += 1
            entry["exportPath"] = dst_rel.as_posix()
            entry["modeFolder"] = mode_key
            mode_counts[mode_key] += 1
            continue

        dst_abs.parent.mkdir(parents=True, exist_ok=True)
        if dst_abs.exists() and src_abs.resolve() != dst_abs.resolve():
            dst_abs = ensure_unique_destination(dst_abs)
            dst_rel = dst_abs.relative_to(source_root)
            collision_renamed += 1
        src_abs.rename(dst_abs)
        entry["exportPath"] = dst_rel.as_posix()
        entry["modeFolder"] = mode_key
        moved += 1
        mode_counts[mode_key] += 1

    removed_dirs = cleanup_empty_dirs(images_dir)

    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    mode_map = {
        "schema": "u3d-mode-folder-map-v1",
        "generatedAt": utc_now(),
        "sourceRoot": str(source_root),
        "mappingFile": str(mapping_path),
        "sequentialMapFile": str(sequential_map_path),
        "packageManifestFile": str(package_manifest_path),
        "summary": {
            "textureEntryCount": len(entries),
            "mainRowCount": len(main_rows),
            "storyRowCount": len(story_rows),
            "hashToFolderCount": len(hash_to_folder),
            "levelRelatedHashCount": len(level_related_hashes),
            "collisionHashCount": len(collisions),
            "imagesMoved": moved,
            "imagesUnchanged": unchanged,
            "imagesMissing": missing,
            "renameCollisionCount": collision_renamed,
            "removedEmptyDirs": removed_dirs,
        },
        "modeFolderImageCount": dict(sorted(mode_counts.items())),
        "collisions": {
            key: sorted(set(value)) for key, value in sorted(collisions.items())
        },
        "storyOrder": [
            {
                "storyIndex": story["storyIndex"],
                "assetAddress": story["assetAddress"],
                "atlasItems": story["atlasItems"],
            }
            for story in story_rows
        ],
    }

    mode_map_path = source_root / "mode_folder_mapping.json"
    with mode_map_path.open("w", encoding="utf-8") as f:
        json.dump(mode_map, f, ensure_ascii=False, indent=2)

    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["modeGrouping"] = {
            "enabled": True,
            "groupedBy": (
                "SequentialLevelDataBase(main) + PackageManifest story asset order"
            ),
            "mappingFile": "mode_folder_mapping.json",
            "sourceSequentialMap": str(sequential_map_path),
            "packageManifestFile": str(package_manifest_path),
            "folders": {
                "main": "images/Main_Level_N",
                "story": "images/Story_N",
                "others": "images/Others",
                "root": "images/*.png (non-level resources)",
            },
            "mainCount": len(main_rows),
            "storyCount": len(story_rows),
        }
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[mode-group] source_root       : {source_root}")
    print(f"[mode-group] mapping          : {mapping_path}")
    print(f"[mode-group] sequential_map   : {sequential_map_path}")
    print(f"[mode-group] package_manifest : {package_manifest_path}")
    print(f"[mode-group] mode_map         : {mode_map_path}")
    print(f"[mode-group] hash->folder     : {len(hash_to_folder)}")
    print(f"[mode-group] moved            : {moved}")
    print(f"[mode-group] unchanged        : {unchanged}")
    print(f"[mode-group] missing          : {missing}")
    print(f"[mode-group] folder counts    : {dict(sorted(mode_counts.items()))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
