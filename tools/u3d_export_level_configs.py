#!/usr/bin/env python3
"""Export readable/editable level config JSON files from U3D bundles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import UnityPy


SCRIPT_NAMESPACE = "Game.Gameplay.Level.Addressable.Data"
MAIN_CLASS = "SequentialLevelDataBase"
STORY_CLASS = "StoryLevelDataBase"
LEVEL_ADDR_PREFIX = "levels/level_"
STORY_ADDR_PREFIX = "storylevels/level_"
MAIN_LEVEL_PATTERN = re.compile(r"^NH(\d+)(.*)$", re.IGNORECASE)
ASSET_ROOT_PREFIX = "assets/gameres/bundleres/"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def _safe_name(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return "unnamed"
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    value = value.strip("._-")
    return value[:96] or "unnamed"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _extract_main_info(board_id: Optional[str]) -> Dict[str, Any]:
    if not isinstance(board_id, str):
        return {"isMainLevel": False, "modeLevel": None, "variant": None}
    match = MAIN_LEVEL_PATTERN.match(board_id)
    if not match:
        return {"isMainLevel": False, "modeLevel": None, "variant": None}
    suffix = (match.group(2) or "").upper()
    return {
        "isMainLevel": True,
        "modeLevel": int(match.group(1)),
        "variant": "base" if not suffix else suffix,
    }


def _load_manifest_helpers(script_path: Path):
    spec = importlib.util.spec_from_file_location("u3d_group_images_by_level", script_path)
    module = importlib.util.module_from_spec(spec)
    if not spec.loader:
        raise RuntimeError(f"failed to load helper script: {script_path}")
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _to_asset_key(asset_address: str) -> str:
    return asset_address.strip().lower()


def _normalize_container_key(key: str) -> str:
    k = key.replace("\\", "/").strip().lower()
    if k.startswith(ASSET_ROOT_PREFIX):
        return k[len(ASSET_ROOT_PREFIX) :]
    return k


def _ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}__dup{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _default_output_root(project_root: Path) -> Path:
    # New layout: myprojects/<project>/webprojects
    if project_root.name == "webprojects":
        return (project_root.parent / "sourceConfigs").resolve()
    # Legacy layout: webprojects/<project>
    return (project_root.parent.parent / "sourceConfigs" / project_root.name).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export level configuration JSON files from MonoBehaviours in level bundles, "
            "grouped as Main_Level_N / Story_N / Others."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root path, e.g. webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--asset-dir",
        default="StreamingAssets/WebGL/ljpx2_lt",
        help="Bundle directory relative to --project-root.",
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help="Optional PackageManifest_*.bytes path. Auto-detect if omitted.",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help=(
            "Output directory. Default: "
            "new layout => <project-root-parent>/sourceConfigs, "
            "legacy => <workspace>/sourceConfigs/<project-name>/"
        ),
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete output-root before export.",
    )
    parser.add_argument(
        "--helper-script",
        default="tools/u3d_group_images_by_level.py",
        help="Helper script that provides PackageManifest parsing functions.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    project_root = _resolve(cwd, args.project_root).resolve()
    asset_dir = (project_root / args.asset_dir).resolve()
    helper_script = _resolve(cwd, args.helper_script).resolve()

    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")
    if not asset_dir.is_dir():
        raise SystemExit(f"asset-dir not found: {asset_dir}")
    if not helper_script.is_file():
        raise SystemExit(f"helper-script not found: {helper_script}")

    if args.output_root:
        output_root = _resolve(cwd, args.output_root).resolve()
    else:
        output_root = _default_output_root(project_root)
    configs_root = output_root / "configs"

    if args.clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    configs_root.mkdir(parents=True, exist_ok=True)

    helper = _load_manifest_helpers(helper_script)
    if args.package_manifest:
        manifest_path = _resolve(cwd, args.package_manifest).resolve()
    else:
        manifest_path = helper._auto_detect_manifest({"assetDir": str(asset_dir)})
        manifest_path = manifest_path.resolve() if manifest_path else None
    if not manifest_path or not manifest_path.is_file():
        raise SystemExit("PackageManifest not found. Use --package-manifest.")

    bundle_hash_pairs: List[Tuple[str, str]] = helper._extract_bundle_hash_pairs(manifest_path)
    asset_entries = helper._parse_asset_entries(manifest_path)

    story_index_by_addr: Dict[str, int] = {}
    story_order: List[Dict[str, Any]] = []
    story_index = 0
    for entry_index, (asset_address, _asset_path, _bundle_idx, _deps, _tags, _unk) in enumerate(asset_entries):
        if asset_address.startswith(STORY_ADDR_PREFIX) and asset_address.endswith(".asset"):
            story_index += 1
            key = _to_asset_key(asset_address)
            story_index_by_addr[key] = story_index
            story_order.append(
                {
                    "storyIndex": story_index,
                    "entryIndex": entry_index,
                    "assetAddress": asset_address,
                }
            )

    target_asset_rows: List[Tuple[int, str, str, int, List[int]]] = []
    for entry_index, (asset_address, _asset_path, bundle_index, deps, _tags, _unk) in enumerate(asset_entries):
        if asset_address.startswith(LEVEL_ADDR_PREFIX) and asset_address.endswith(".asset"):
            target_asset_rows.append((entry_index, "level", asset_address, bundle_index, deps))
            continue
        if asset_address.startswith(STORY_ADDR_PREFIX) and asset_address.endswith(".asset"):
            target_asset_rows.append((entry_index, "story", asset_address, bundle_index, deps))

    env_cache: Dict[str, Any] = {}
    container_cache: Dict[str, Dict[str, Any]] = {}

    exported_entries: List[Dict[str, Any]] = []
    errors: List[str] = []
    folder_count: Dict[str, int] = defaultdict(int)

    for entry_index, entry_type, asset_address, bundle_index, deps in target_asset_rows:
        if bundle_index >= len(bundle_hash_pairs):
            errors.append(f"bundle index out of range: entry={entry_index}, addr={asset_address}")
            continue

        bundle_name, bundle_hash = bundle_hash_pairs[bundle_index]
        bundle_file = f"{bundle_hash}.unity3d"
        bundle_path = asset_dir / bundle_file
        bundle_rel = (Path(args.asset_dir) / bundle_file).as_posix()

        if not bundle_path.is_file():
            errors.append(f"bundle file missing: {bundle_path}")
            continue

        if bundle_hash not in env_cache:
            try:
                env_cache[bundle_hash] = UnityPy.load(str(bundle_path))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"bundle load failed: {bundle_path.name} ({exc})")
                continue
        env = env_cache[bundle_hash]

        if bundle_hash not in container_cache:
            by_addr: Dict[str, Any] = {}
            for key, obj in env.container.items():
                by_addr[_normalize_container_key(str(key))] = obj
            container_cache[bundle_hash] = by_addr
        container_map = container_cache[bundle_hash]

        asset_key = _to_asset_key(asset_address)
        obj = container_map.get(asset_key)
        if obj is None:
            errors.append(f"asset not found in container: {bundle_path.name} :: {asset_address}")
            continue

        if obj.type.name != "MonoBehaviour":
            errors.append(
                f"asset object type is not MonoBehaviour: {bundle_path.name} :: {asset_address} :: {obj.type.name}"
            )
            continue

        try:
            mono = obj.read()
            script = mono.m_Script.read() if getattr(mono, "m_Script", None) else None
            script_class = getattr(script, "m_ClassName", None) if script else None
            script_namespace = getattr(script, "m_Namespace", None) if script else None
            tree = obj.read_typetree()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"failed reading typetree: {bundle_path.name} :: {asset_address} :: {exc}")
            continue

        if script_namespace != SCRIPT_NAMESPACE or script_class not in (MAIN_CLASS, STORY_CLASS):
            errors.append(
                f"unexpected script class: {bundle_path.name} :: {asset_address} :: "
                f"{script_namespace}.{script_class}"
            )
            continue

        board_raw = tree.get("boardDataJson")
        if not isinstance(board_raw, str):
            errors.append(f"boardDataJson missing/non-string: {bundle_path.name} :: {asset_address}")
            continue

        board_obj: Dict[str, Any]
        board_parse_error: Optional[str] = None
        try:
            board_obj = json.loads(board_raw)
            if not isinstance(board_obj, dict):
                board_obj = {"__rawValue": board_obj}
        except Exception as exc:  # noqa: BLE001
            board_parse_error = str(exc)
            board_obj = {
                "__parseError": board_parse_error,
                "__rawBoardDataJson": board_raw,
            }

        board_id = board_obj.get("id") if isinstance(board_obj, dict) else None
        main_info = _extract_main_info(board_id if isinstance(board_id, str) else None)

        story_idx = story_index_by_addr.get(asset_key)
        if entry_type == "story":
            folder = f"Story_{story_idx}" if isinstance(story_idx, int) else "Others"
        elif main_info.get("isMainLevel"):
            folder = f"Main_Level_{main_info.get('modeLevel')}"
        else:
            folder = "Others"

        base_name = ""
        if isinstance(board_id, str) and board_id:
            base_name = board_id
        elif isinstance(tree.get("m_Name"), str) and tree.get("m_Name"):
            base_name = str(tree.get("m_Name"))
        else:
            base_name = Path(asset_address).stem

        rel_config_path = Path("configs") / folder / f"{_safe_name(base_name)}.json"
        abs_config_path = output_root / rel_config_path
        abs_config_path.parent.mkdir(parents=True, exist_ok=True)
        abs_config_path = _ensure_unique_path(abs_config_path)
        rel_config_path = abs_config_path.relative_to(output_root)

        abs_config_path.write_text(
            json.dumps(board_obj, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        deps_info: List[Dict[str, Any]] = []
        for dep_index in deps:
            if dep_index >= len(bundle_hash_pairs):
                continue
            dep_name, dep_hash = bundle_hash_pairs[dep_index]
            deps_info.append(
                {
                    "depBundleIndex": dep_index,
                    "depBundleName": dep_name,
                    "depBundleHash": dep_hash,
                    "depBundleFile": f"{dep_hash}.unity3d",
                }
            )

        exported_entry = {
            "entryIndex": entry_index,
            "assetAddress": asset_address,
            "entryType": entry_type,
            "bundleIndex": bundle_index,
            "bundleName": bundle_name,
            "bundleHash": bundle_hash,
            "bundleFile": bundle_file,
            "bundleRelPath": bundle_rel,
            "deps": deps_info,
            "pathId": int(obj.path_id),
            "monoName": tree.get("m_Name"),
            "scriptClass": script_class,
            "scriptNamespace": script_namespace,
            "boardDataJsonField": "boardDataJson",
            "boardDataId": board_id if isinstance(board_id, str) else None,
            "boardDataJsonLength": len(board_raw),
            "boardDataJsonParseError": board_parse_error,
            "mainLevel": main_info,
            "storyIndex": story_idx if isinstance(story_idx, int) else None,
            "modeFolder": folder,
            "exportPath": rel_config_path.as_posix(),
            "sha256": _sha256_file(abs_config_path),
            "byteSize": abs_config_path.stat().st_size,
        }
        exported_entries.append(exported_entry)
        folder_count[folder] += 1

    main_count = sum(1 for e in exported_entries if str(e.get("modeFolder", "")).startswith("Main_Level_"))
    story_count = sum(1 for e in exported_entries if str(e.get("modeFolder", "")).startswith("Story_"))
    others_count = sum(1 for e in exported_entries if str(e.get("modeFolder", "")) == "Others")

    mapping_doc = {
        "schema": "u3d-level-config-mapping-v1",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "assetDir": str(asset_dir),
        "packageManifestFile": str(manifest_path),
        "sourceRoot": str(output_root),
        "summary": {
            "assetEntryCount": len(target_asset_rows),
            "exportedCount": len(exported_entries),
            "mainCount": main_count,
            "storyCount": story_count,
            "othersCount": others_count,
            "errorCount": len(errors),
        },
        "folderFileCount": dict(sorted(folder_count.items())),
        "storyOrder": story_order,
        "entries": exported_entries,
        "errors": errors,
    }

    mapping_path = output_root / "config_mapping.json"
    mapping_path.write_text(
        json.dumps(mapping_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[cfg-export] project_root   : {project_root}")
    print(f"[cfg-export] asset_dir      : {asset_dir}")
    print(f"[cfg-export] output_root    : {output_root}")
    print(f"[cfg-export] package_manifest: {manifest_path}")
    print(f"[cfg-export] exported_count : {len(exported_entries)}")
    print(f"[cfg-export] main/story/others: {main_count}/{story_count}/{others_count}")
    print(f"[cfg-export] error_count    : {len(errors)}")
    print(f"[cfg-export] mapping        : {mapping_path}")
    if errors:
        print("[cfg-export] note           : some assets were skipped, see mapping.errors")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
