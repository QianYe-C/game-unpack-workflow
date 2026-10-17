#!/usr/bin/env python3
"""Export level avatar->material map from sourceConfigs + sourceImages mappings."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build per-level mapping: group -> avatar item IDs -> material paths, "
            "and common type key(ct)."
        )
    )
    parser.add_argument(
        "--source-config-root",
        required=True,
        help="sourceConfigs project directory, e.g. sourceConfigs/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--source-image-root",
        required=True,
        help="sourceImages project directory, e.g. sourceImages/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--config-mapping",
        default="config_mapping.json",
        help="Config mapping path relative to --source-config-root or absolute.",
    )
    parser.add_argument(
        "--image-mapping",
        default="image_mapping.json",
        help="Image mapping path relative to --source-image-root or absolute.",
    )
    parser.add_argument(
        "--ct-term-map",
        default="",
        help=(
            "Optional JSON file path: {\"<ct>\": \"中文文案\"}. "
            "Used to fill commonTypeTerm."
        ),
    )
    parser.add_argument(
        "--output",
        default="level_avatar_material_mapping.json",
        help="Output JSON path relative to --source-config-root or absolute.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    source_config_root = _resolve(cwd, args.source_config_root).resolve()
    source_image_root = _resolve(cwd, args.source_image_root).resolve()
    config_mapping_path = _resolve(source_config_root, args.config_mapping).resolve()
    image_mapping_path = _resolve(source_image_root, args.image_mapping).resolve()
    out_path = _resolve(source_config_root, args.output).resolve()

    if not source_config_root.is_dir():
        raise SystemExit(f"source-config-root not found: {source_config_root}")
    if not source_image_root.is_dir():
        raise SystemExit(f"source-image-root not found: {source_image_root}")
    if not config_mapping_path.is_file():
        raise SystemExit(f"config mapping not found: {config_mapping_path}")
    if not image_mapping_path.is_file():
        raise SystemExit(f"image mapping not found: {image_mapping_path}")

    config_map = _load_json(config_mapping_path)
    image_map = _load_json(image_mapping_path)

    ct_term_map: Dict[str, str] = {}
    if args.ct_term_map:
        ct_term_path = _resolve(cwd, args.ct_term_map).resolve()
        if not ct_term_path.is_file():
            raise SystemExit(f"ct-term-map not found: {ct_term_path}")
        loaded = _load_json(ct_term_path)
        for k, v in loaded.items():
            if isinstance(v, str):
                ct_term_map[str(k)] = v

    # Build sprite indices from split slices.
    global_sprite_paths: Dict[str, List[str]] = defaultdict(list)
    mode_sprite_paths: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    for entry in image_map.get("entries", []):
        if entry.get("kind") != "Texture2D":
            continue
        mode = str(entry.get("modeFolder") or "Root")
        slices = entry.get("spriteAtlasSlices")
        if not isinstance(slices, list):
            continue
        for item in slices:
            if not isinstance(item, dict):
                continue
            sprite_name = str(item.get("spriteName"))
            export_path = item.get("exportPath")
            if not isinstance(export_path, str) or not export_path:
                continue
            global_sprite_paths[sprite_name].append(export_path)
            mode_sprite_paths[mode][sprite_name].append(export_path)

    def pick_sprite(mode: str, sprite_name: str) -> Optional[str]:
        mode_list = mode_sprite_paths.get(mode, {}).get(sprite_name, [])
        if mode_list:
            return mode_list[0]
        global_list = global_sprite_paths.get(sprite_name, [])
        if global_list:
            return global_list[0]
        return None

    levels: List[Dict[str, Any]] = []
    unresolved_material_items = 0
    unresolved_common_type_sprite = 0
    resolved_common_type_term = 0

    for entry in config_map.get("entries", []):
        config_rel = entry.get("exportPath")
        if not isinstance(config_rel, str) or not config_rel:
            continue
        config_abs = source_config_root / config_rel
        if not config_abs.is_file():
            continue

        try:
            level_cfg = _load_json(config_abs)
        except Exception:  # noqa: BLE001
            continue

        raw_items = level_cfg.get("it")
        items: List[Dict[str, Any]] = []
        if isinstance(raw_items, list):
            items = [x for x in raw_items if isinstance(x, dict)]
        elif isinstance(raw_items, dict):
            # Story format: {"0":[...], "1":[...]}
            for _, arr in sorted(raw_items.items(), key=lambda x: str(x[0])):
                if isinstance(arr, list):
                    items.extend(x for x in arr if isinstance(x, dict))

        group_meta: Dict[str, Dict[str, Any]] = {}
        raw_groups = level_cfg.get("grs")
        if isinstance(raw_groups, list):
            for g in raw_groups:
                if not isinstance(g, dict):
                    continue
                gid = g.get("id")
                if gid is None:
                    continue
                group_meta[str(gid)] = g

        grouped_items: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        mode = str(entry.get("modeFolder") or "Root")
        for item in items:
            iid = item.get("id")
            gid = item.get("g")
            if iid is None or gid is None:
                continue
            iid_text = str(iid)
            gid_text = str(gid)
            sprite_path = pick_sprite(mode, iid_text)
            if not sprite_path:
                unresolved_material_items += 1
            grouped_items[gid_text].append(
                {
                    "itemId": iid_text,
                    "spriteName": iid_text,
                    "materialPath": sprite_path,
                }
            )

        group_rows: List[Dict[str, Any]] = []
        for gid in sorted(grouped_items.keys()):
            meta = group_meta.get(gid, {})
            ct = meta.get("ct")
            ct_text = str(ct) if ct is not None else None
            ct_sprite_path = pick_sprite(mode, ct_text) if ct_text is not None else None
            if ct_text is not None and not ct_sprite_path:
                unresolved_common_type_sprite += 1
            ct_term = ct_term_map.get(ct_text) if ct_text is not None else None
            if ct_term:
                resolved_common_type_term += 1

            group_rows.append(
                {
                    "groupId": gid,
                    "commonTypeCt": ct,
                    "commonTypeTerm": ct_term,
                    "commonTypeSpriteName": ct_text,
                    "commonTypeSpritePath": ct_sprite_path,
                    "items": grouped_items[gid],
                }
            )

        levels.append(
            {
                "boardDataId": entry.get("boardDataId"),
                "modeFolder": mode,
                "assetAddress": entry.get("assetAddress"),
                "configPath": config_rel,
                "groups": group_rows,
            }
        )

    out_doc = {
        "schema": "u3d-level-avatar-material-map-v1",
        "generatedAt": _utc_now(),
        "sourceConfigRoot": str(source_config_root),
        "sourceImageRoot": str(source_image_root),
        "configMappingFile": str(config_mapping_path),
        "imageMappingFile": str(image_mapping_path),
        "ctTermMapFile": args.ct_term_map if args.ct_term_map else "",
        "summary": {
            "levelCount": len(levels),
            "resolvedCommonTypeTermCount": resolved_common_type_term,
            "unresolvedMaterialItemCount": unresolved_material_items,
            "unresolvedCommonTypeSpriteCount": unresolved_common_type_sprite,
        },
        "levels": levels,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[avatar-map] source_config_root : {source_config_root}")
    print(f"[avatar-map] source_image_root  : {source_image_root}")
    print(f"[avatar-map] level_count        : {len(levels)}")
    print(f"[avatar-map] resolved_ct_term   : {resolved_common_type_term}")
    print(f"[avatar-map] unresolved_item    : {unresolved_material_items}")
    print(f"[avatar-map] unresolved_ct_icon : {unresolved_common_type_sprite}")
    print(f"[avatar-map] output            : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
