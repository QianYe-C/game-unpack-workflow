#!/usr/bin/env python3
"""Extract SequentialLevelDataBase mapping from Unity bundles using manifest config."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import UnityPy


SCRIPT_CLASS = "SequentialLevelDataBase"
SCRIPT_NAMESPACE = "Game.Gameplay.Level.Addressable.Data"
LEVEL_ADDR_PREFIX = "levels/level_"
ATLAS_BUNDLE_PREFIX = "atlases_level_"
MAIN_LEVEL_PATTERN = re.compile(r"^NH(\d+)(.*)$", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def load_manifest_helpers(script_path: Path):
    spec = importlib.util.spec_from_file_location("u3d_group_images_by_level", script_path)
    module = importlib.util.module_from_spec(spec)
    if not spec.loader:
        raise RuntimeError(f"Failed to load script: {script_path}")
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract level mapping from MonoBehaviours whose script is "
            "Game.Gameplay.Level.Addressable.Data.SequentialLevelDataBase."
        )
    )
    parser.add_argument(
        "--asset-dir",
        required=True,
        help="Directory containing .unity3d bundles and PackageManifest_*.bytes.",
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help="Optional PackageManifest_*.bytes path. Auto-detect if omitted.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--helper-script",
        default="tools/u3d_group_images_by_level.py",
        help=(
            "Path to helper script that already implements PackageManifest parsing "
            "functions."
        ),
    )
    return parser.parse_args()


def auto_detect_manifest(asset_dir: Path) -> Optional[Path]:
    candidates = sorted(asset_dir.glob("PackageManifest_*_*.bytes"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: (p.stat().st_size, p.stat().st_mtime), reverse=True)
    return candidates[0]


def extract_main_level_info(board_id: Optional[str]) -> Dict[str, Any]:
    if not isinstance(board_id, str):
        return {"isMainLevel": False, "modeLevel": None, "variant": None}
    m = MAIN_LEVEL_PATTERN.match(board_id)
    if not m:
        return {"isMainLevel": False, "modeLevel": None, "variant": None}
    suffix = (m.group(2) or "").upper()
    return {
        "isMainLevel": True,
        "modeLevel": int(m.group(1)),
        "variant": "base" if not suffix else suffix,
    }


def read_script_info(mono) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        script_ptr = getattr(mono, "m_Script", None)
        if not script_ptr:
            return None, None, "m_Script is empty"
        script_obj = script_ptr.read()
        return (
            getattr(script_obj, "m_ClassName", None),
            getattr(script_obj, "m_Namespace", None),
            None,
        )
    except Exception as exc:  # noqa: BLE001
        return None, None, str(exc)


def resolve_atlas_name(bundle_path: Path, path_id: int) -> Optional[Dict[str, Any]]:
    if not bundle_path.is_file():
        return None
    try:
        env = UnityPy.load(str(bundle_path))
    except Exception:  # noqa: BLE001
        return None
    for obj in env.objects:
        if obj.path_id != path_id:
            continue
        item: Dict[str, Any] = {
            "resolvedObjectType": obj.type.name,
            "resolvedPathID": path_id,
        }
        try:
            d = obj.read()
            item["resolvedName"] = getattr(d, "m_Name", "")
        except Exception:  # noqa: BLE001
            pass
        return item
    return None


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()
    asset_dir = resolve_path(cwd, args.asset_dir).resolve()
    out_path = resolve_path(cwd, args.output).resolve()
    helper_script = resolve_path(cwd, args.helper_script).resolve()

    if not asset_dir.is_dir():
        raise SystemExit(f"asset-dir not found: {asset_dir}")
    if not helper_script.is_file():
        raise SystemExit(f"helper-script not found: {helper_script}")

    if args.package_manifest:
        package_manifest = resolve_path(cwd, args.package_manifest).resolve()
    else:
        package_manifest = auto_detect_manifest(asset_dir)
    if not package_manifest or not package_manifest.is_file():
        raise SystemExit("PackageManifest not found. Use --package-manifest.")

    helper = load_manifest_helpers(helper_script)
    bundle_hash_pairs: List[Tuple[str, str]] = helper._extract_bundle_hash_pairs(package_manifest)
    asset_entries = helper._parse_asset_entries(package_manifest)

    level_rows: List[Dict[str, Any]] = []
    bundle_error_count = 0
    script_mismatch_count = 0
    missing_sequential_count = 0

    atlas_resolve_cache: Dict[Tuple[str, int], Optional[Dict[str, Any]]] = {}

    for entry_index, (asset_address, _asset_path, bundle_index, deps, _tags, _unk) in enumerate(asset_entries):
        if not asset_address.startswith(LEVEL_ADDR_PREFIX):
            continue
        if bundle_index >= len(bundle_hash_pairs):
            continue

        level_bundle_name, level_bundle_hash = bundle_hash_pairs[bundle_index]
        level_bundle_path = asset_dir / f"{level_bundle_hash}.unity3d"
        row: Dict[str, Any] = {
            "entryIndex": entry_index,
            "assetAddress": asset_address,
            "bundleIndex": bundle_index,
            "levelBundleName": level_bundle_name,
            "levelBundleHash": level_bundle_hash,
            "levelBundleFile": level_bundle_path.name,
            "deps": [],
        }
        for dep in deps:
            if dep < len(bundle_hash_pairs):
                dep_name, dep_hash = bundle_hash_pairs[dep]
                row["deps"].append(
                    {
                        "depBundleIndex": dep,
                        "depBundleName": dep_name,
                        "depBundleHash": dep_hash,
                    }
                )

        if not level_bundle_path.is_file():
            bundle_error_count += 1
            row["error"] = f"Missing level bundle file: {level_bundle_path.name}"
            level_rows.append(row)
            continue

        try:
            env = UnityPy.load(str(level_bundle_path))
        except Exception as exc:  # noqa: BLE001
            bundle_error_count += 1
            row["error"] = f"Failed to load bundle: {exc}"
            level_rows.append(row)
            continue

        found_obj: Optional[Dict[str, Any]] = None
        has_mono_script_other = False

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue
            try:
                mono = obj.read()
                class_name, namespace, script_err = read_script_info(mono)
                if class_name != SCRIPT_CLASS or namespace != SCRIPT_NAMESPACE:
                    if class_name or namespace:
                        has_mono_script_other = True
                    continue

                tree = obj.read_typetree()
                board_json_raw = tree.get("boardDataJson", "")
                board_json_id: Optional[str] = None
                board_json_parse_error: Optional[str] = None
                try:
                    board_json = json.loads(board_json_raw) if isinstance(board_json_raw, str) else {}
                    board_json_id = board_json.get("id")
                except Exception as exc:  # noqa: BLE001
                    board_json_parse_error = str(exc)

                found_obj = {
                    "pathID": obj.path_id,
                    "monoName": tree.get("m_Name"),
                    "scriptClass": class_name,
                    "scriptNamespace": namespace,
                    "scriptReadError": script_err,
                    "boardDataJsonId": board_json_id,
                    "boardDataJsonLength": len(board_json_raw) if isinstance(board_json_raw, str) else None,
                    "boardDataJsonParseError": board_json_parse_error,
                    "itemSpriteAtlasRef": tree.get("itemSpriteAtlas"),
                }
                break
            except Exception:  # noqa: BLE001
                continue

        if not found_obj:
            missing_sequential_count += 1
            if has_mono_script_other:
                script_mismatch_count += 1
            row["sequentialLevelDataBase"] = None
            level_rows.append(row)
            continue

        row["sequentialLevelDataBase"] = found_obj

        main_info = extract_main_level_info(found_obj.get("boardDataJsonId"))
        row["mainLevel"] = main_info

        item_ref = found_obj.get("itemSpriteAtlasRef") or {}
        atlas_path_id = item_ref.get("m_PathID") if isinstance(item_ref, dict) else None
        atlas_candidates = [
            d for d in row["deps"] if d.get("depBundleName", "").startswith(ATLAS_BUNDLE_PREFIX)
        ]
        if isinstance(atlas_path_id, int):
            resolved_list: List[Dict[str, Any]] = []
            for dep in atlas_candidates:
                dep_hash = dep["depBundleHash"]
                dep_bundle = asset_dir / f"{dep_hash}.unity3d"
                key = (dep_hash, atlas_path_id)
                if key not in atlas_resolve_cache:
                    atlas_resolve_cache[key] = resolve_atlas_name(dep_bundle, atlas_path_id)
                resolved = atlas_resolve_cache[key]
                if resolved:
                    item = dict(dep)
                    item.update(
                        {
                            "atlasBundleFile": dep_bundle.name,
                            "resolvedPathID": resolved.get("resolvedPathID"),
                            "resolvedObjectType": resolved.get("resolvedObjectType"),
                            "resolvedName": resolved.get("resolvedName"),
                        }
                    )
                    resolved_list.append(item)
            row["resolvedAtlas"] = resolved_list
        level_rows.append(row)

    main_levels = [r for r in level_rows if r.get("mainLevel", {}).get("isMainLevel")]
    main_by_mode: Dict[int, List[str]] = defaultdict(list)
    for item in main_levels:
        mode_level = item.get("mainLevel", {}).get("modeLevel")
        level_id = (item.get("sequentialLevelDataBase") or {}).get("boardDataJsonId")
        if isinstance(mode_level, int) and isinstance(level_id, str):
            main_by_mode[mode_level].append(level_id)

    out = {
        "schema": "u3d-sequential-level-map-v1",
        "generatedAt": utc_now(),
        "classFilter": {
            "className": SCRIPT_CLASS,
            "namespace": SCRIPT_NAMESPACE,
        },
        "assetDir": str(asset_dir),
        "packageManifestFile": str(package_manifest),
        "summary": {
            "levelAssetEntryCount": len([e for e in asset_entries if e[0].startswith(LEVEL_ADDR_PREFIX)]),
            "mappedRowCount": len(level_rows),
            "bundleErrorCount": bundle_error_count,
            "missingSequentialLevelDataBaseCount": missing_sequential_count,
            "scriptMismatchCount": script_mismatch_count,
            "mainLevelCandidateCount": len(main_levels),
            "mainLevelDistinctModeCount": len(main_by_mode),
            "mainLevelMultiVariantCount": sum(1 for v in main_by_mode.values() if len(v) > 1),
        },
        "mainLevelVariantByModeLevel": {
            str(k): sorted(v) for k, v in sorted(main_by_mode.items(), key=lambda x: x[0])
        },
        "levels": level_rows,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[extract] package_manifest: {package_manifest}")
    print(f"[extract] output          : {out_path}")
    print(f"[extract] rows            : {len(level_rows)}")
    print(f"[extract] main levels     : {len(main_levels)}")
    print(f"[extract] main mode count : {len(main_by_mode)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
