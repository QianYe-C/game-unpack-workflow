#!/usr/bin/env python3
"""Split atlas textures into editable sprite PNG slices (all folders)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import UnityPy


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return "unnamed"
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", value)
    value = value.strip("._-")
    return value[:96] or "unnamed"


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path)


def _parse_render_data_item(item) -> Tuple[Dict, Dict]:
    if isinstance(item, tuple) and len(item) == 2:
        return item[0], item[1]
    if isinstance(item, list) and len(item) == 2:
        return item[0], item[1]
    if isinstance(item, dict):
        # Fallback for unexpected serialization
        return {}, item
    return {}, {}


def _render_key_tuple(raw_key) -> Tuple[int, int, int, int] | None:
    if not raw_key:
        return None
    key_dict = None
    if isinstance(raw_key, tuple) and raw_key:
        key_dict = raw_key[0]
    elif isinstance(raw_key, list) and raw_key:
        key_dict = raw_key[0]
    elif isinstance(raw_key, dict):
        key_dict = raw_key
    if not isinstance(key_dict, dict):
        return None
    try:
        return (
            int(key_dict.get("data[0]", 0)),
            int(key_dict.get("data[1]", 0)),
            int(key_dict.get("data[2]", 0)),
            int(key_dict.get("data[3]", 0)),
        )
    except Exception:  # noqa: BLE001
        return None


def _collect_bundle_atlas_slices(bundle_path: Path) -> Dict[int, List[Dict]]:
    env = UnityPy.load(str(bundle_path))
    slices_by_tex: Dict[int, List[Dict]] = defaultdict(list)
    sprite_name_by_atlas_key: Dict[int, Dict[Tuple[int, int, int, int], str]] = defaultdict(dict)
    sprite_name_by_tag_key: Dict[str, Dict[Tuple[int, int, int, int], str]] = defaultdict(dict)

    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        tree = obj.read_typetree()
        sprite_name = str(tree.get("m_Name") or f"sprite_{obj.path_id}")
        key_tuple = _render_key_tuple(tree.get("m_RenderDataKey"))
        if key_tuple is None:
            continue

        atlas_ref = tree.get("m_SpriteAtlas") or {}
        atlas_pid = int(atlas_ref.get("m_PathID", 0) or 0)
        if atlas_pid:
            sprite_name_by_atlas_key[atlas_pid][key_tuple] = sprite_name

        for tag in tree.get("m_AtlasTags") or []:
            tag_name = str(tag or "").strip()
            if tag_name:
                sprite_name_by_tag_key[tag_name][key_tuple] = sprite_name

    for obj in env.objects:
        if obj.type.name != "SpriteAtlas":
            continue

        tree = obj.read_typetree()
        atlas_name = str(tree.get("m_Name") or f"SpriteAtlas_{obj.path_id}")
        atlas_pid = int(obj.path_id)
        names = tree.get("m_PackedSpriteNamesToIndex") or []
        render_map = tree.get("m_RenderDataMap") or []

        for idx, raw_item in enumerate(render_map):
            key_data, value = _parse_render_data_item(raw_item)
            if not isinstance(value, dict):
                continue

            texture_ref = value.get("texture") or {}
            rect = value.get("textureRect") or {}

            tex_pid = int(texture_ref.get("m_PathID", 0) or 0)
            if tex_pid == 0:
                continue

            try:
                x = int(round(float(rect.get("x", 0))))
                y = int(round(float(rect.get("y", 0))))
                width = int(round(float(rect.get("width", 0))))
                height = int(round(float(rect.get("height", 0))))
            except Exception:  # noqa: BLE001
                continue

            if width <= 0 or height <= 0:
                continue

            key_tuple = _render_key_tuple(key_data)
            sprite_name = None
            if key_tuple is not None:
                sprite_name = sprite_name_by_atlas_key.get(atlas_pid, {}).get(key_tuple)
                if not sprite_name:
                    sprite_name = sprite_name_by_tag_key.get(atlas_name, {}).get(key_tuple)
            if not sprite_name:
                sprite_name = str(names[idx]) if idx < len(names) else f"sprite_{idx:04d}"

            slices_by_tex[tex_pid].append(
                {
                    "atlasName": atlas_name,
                    "spriteName": sprite_name,
                    "x": x,
                    "y": y,  # Unity bottom-left origin
                    "width": width,
                    "height": height,
                    "atlasIndex": idx,
                }
            )

    return slices_by_tex


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split atlas textures into sprite slices and augment "
            "image_mapping.json with spriteAtlasSlices metadata."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root path, e.g. webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="sourceImages project directory, e.g. sourceImages/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--mapping",
        default="image_mapping.json",
        help="Mapping path relative to --source-root or absolute.",
    )
    parser.add_argument(
        "--slice-root",
        default="",
        help=(
            "Optional slice output root (relative to source-root). "
            "Default empty: write slices next to each atlas image."
        ),
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Overwrite existing slice PNG files.",
    )
    parser.add_argument(
        "--keep-base-atlas",
        action="store_true",
        help=(
            "Keep exported atlas PNG after splitting. "
            "Default is to remove base atlas and keep only slices."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only, do not write files and mapping.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()
    project_root = _resolve(cwd, args.project_root).resolve()
    source_root = _resolve(cwd, args.source_root).resolve()
    mapping_path = _resolve(source_root, args.mapping).resolve()
    slice_root: Optional[Path] = (
        _resolve(source_root, args.slice_root).resolve() if args.slice_root else None
    )

    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")
    if not source_root.is_dir():
        raise SystemExit(f"source-root not found: {source_root}")
    if not mapping_path.is_file():
        raise SystemExit(f"mapping not found: {mapping_path}")

    mapping_doc = json.loads(mapping_path.read_text(encoding="utf-8"))
    schema = mapping_doc.get("schema")
    if schema not in ("u3d-image-mapping-v1", "u3d-source-images-v1"):
        raise SystemExit(f"Unsupported mapping schema: {schema}")

    entries = []
    for item in mapping_doc.get("entries", []):
        if item.get("kind") != "Texture2D":
            continue
        if "bundleRelPath" not in item:
            continue
        export_path = item.get("exportPath")
        if not isinstance(export_path, str) or not export_path.strip():
            continue
        entries.append(item)
    if not entries:
        print("[split] no bundle texture entries found, nothing to do.")
        return 0

    print(f"[split] project_root : {project_root}")
    print(f"[split] source_root  : {source_root}")
    print(f"[split] mapping      : {mapping_path}")
    print(f"[split] texture_entries : {len(entries)}")
    print(f"[split] slice_layout    : {'custom-root' if slice_root else 'sibling'}")
    if slice_root:
        print(f"[split] slice_root      : {slice_root}")

    by_bundle: Dict[str, List[Dict]] = defaultdict(list)
    for entry in entries:
        by_bundle[str(entry["bundleRelPath"])].append(entry)

    report = {
        "schema": "u3d-atlas-split-report-v2",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "sourceRoot": str(source_root),
        "mapping": str(mapping_path),
        "sliceRoot": str(slice_root) if slice_root else "",
        "sliceLayout": "custom-root" if slice_root else "sibling",
        "dryRun": bool(args.dry_run),
        "summary": {
            "textureEntryCount": len(entries),
            "bundleCount": len(by_bundle),
            "atlasTextureCount": 0,
            "sliceCount": 0,
            "writtenSliceCount": 0,
            "keptExistingSliceCount": 0,
            "missingAtlasImageCount": 0,
            "removedBaseAtlasCount": 0,
            "skippedAlreadySplitCount": 0,
        },
        "bundles": [],
        "errors": [],
    }

    total_atlas_texture = 0
    total_slice = 0
    total_written = 0
    total_kept = 0
    total_missing = 0
    total_removed_base = 0
    total_skipped_split = 0

    for bundle_rel, bundle_entries in sorted(by_bundle.items()):
        bundle_path = project_root / bundle_rel
        if not bundle_path.is_file():
            report["errors"].append(f"bundle not found: {bundle_path}")
            continue

        atlas_slices_by_tex = _collect_bundle_atlas_slices(bundle_path)
        bundle_item = {
            "bundleRelPath": bundle_rel,
            "textureCount": len(bundle_entries),
            "atlasTextureCount": 0,
            "sliceCount": 0,
            "writtenSliceCount": 0,
            "keptExistingSliceCount": 0,
            "missingAtlasImageCount": 0,
            "removedBaseAtlasCount": 0,
            "skippedAlreadySplitCount": 0,
        }

        for entry in bundle_entries:
            path_id = int(entry["pathId"])
            slices = atlas_slices_by_tex.get(path_id, [])
            if len(slices) < 1:
                entry.pop("spriteAtlasSlices", None)
                continue

            atlas_image_path = source_root / str(entry["exportPath"])
            if not atlas_image_path.is_file():
                existing_slices = entry.get("spriteAtlasSlices")
                if isinstance(existing_slices, list) and existing_slices:
                    all_exist = True
                    for s in existing_slices:
                        if not isinstance(s, dict):
                            all_exist = False
                            break
                        p = s.get("exportPath")
                        if not isinstance(p, str) or not p:
                            all_exist = False
                            break
                        if not (source_root / p).is_file():
                            all_exist = False
                            break
                    if all_exist:
                        bundle_item["skippedAlreadySplitCount"] += 1
                        total_skipped_split += 1
                        continue
                bundle_item["missingAtlasImageCount"] += 1
                total_missing += 1
                report["errors"].append(
                    f"atlas image missing for split: {atlas_image_path}"
                )
                continue

            from PIL import Image  # Lazy import to reduce startup overhead.

            with Image.open(atlas_image_path) as atlas_im:
                atlas_image = atlas_im.convert("RGBA")
            atlas_w, atlas_h = atlas_image.size

            atlas_export_rel = Path(str(entry["exportPath"]))
            atlas_stem = atlas_export_rel.stem

            used_rel_paths = set()
            mapped_slices: List[Dict] = []

            for idx, slice_item in enumerate(slices):
                x = int(slice_item["x"])
                y = int(slice_item["y"])
                width = int(slice_item["width"])
                height = int(slice_item["height"])

                # Clamp to valid atlas region.
                x = max(0, min(x, atlas_w - 1))
                y = max(0, min(y, atlas_h - 1))
                width = max(1, min(width, atlas_w - x))
                height = max(1, min(height, atlas_h - y))
                top = atlas_h - (y + height)
                top = max(0, min(top, atlas_h - 1))
                height = min(height, atlas_h - top)

                if slice_root:
                    base_rel_dir = (slice_root / atlas_stem).relative_to(source_root)
                    base_filename = f"{idx:04d}_{_safe_name(slice_item['spriteName'])}.png"
                else:
                    base_rel_dir = atlas_export_rel.parent
                    base_filename = (
                        f"{atlas_stem}__{idx:04d}_{_safe_name(slice_item['spriteName'])}.png"
                    )

                rel_path = base_rel_dir / base_filename
                if rel_path.as_posix() in used_rel_paths:
                    suffix = 1
                    while True:
                        if slice_root:
                            candidate_name = (
                                f"{idx:04d}_{_safe_name(slice_item['spriteName'])}_{suffix}.png"
                            )
                        else:
                            candidate_name = (
                                f"{atlas_stem}__{idx:04d}_{_safe_name(slice_item['spriteName'])}_{suffix}.png"
                            )
                        candidate = base_rel_dir / candidate_name
                        if candidate.as_posix() not in used_rel_paths:
                            rel_path = candidate
                            break
                        suffix += 1
                used_rel_paths.add(rel_path.as_posix())
                abs_path = source_root / rel_path

                if abs_path.is_file() and not args.overwrite_existing:
                    kept_existing = True
                else:
                    kept_existing = False
                    if not args.dry_run:
                        abs_path.parent.mkdir(parents=True, exist_ok=True)
                        tile = atlas_image.crop((x, top, x + width, top + height))
                        tile.save(abs_path, format="PNG")

                sha = _sha256_file(abs_path) if abs_path.is_file() else ""
                mapped_slices.append(
                    {
                        "atlasName": slice_item["atlasName"],
                        "spriteName": slice_item["spriteName"],
                        "atlasIndex": int(slice_item["atlasIndex"]),
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "exportPath": rel_path.as_posix(),
                        "sha256": sha,
                    }
                )

                if kept_existing:
                    bundle_item["keptExistingSliceCount"] += 1
                    total_kept += 1
                else:
                    bundle_item["writtenSliceCount"] += 1
                    total_written += 1

            entry["spriteAtlasSlices"] = mapped_slices
            if not args.keep_base_atlas and atlas_image_path.is_file():
                if not args.dry_run:
                    atlas_image_path.unlink()
                bundle_item["removedBaseAtlasCount"] += 1
                total_removed_base += 1
            bundle_item["atlasTextureCount"] += 1
            bundle_item["sliceCount"] += len(mapped_slices)
            total_atlas_texture += 1
            total_slice += len(mapped_slices)

        report["bundles"].append(bundle_item)

    report["summary"]["atlasTextureCount"] = total_atlas_texture
    report["summary"]["sliceCount"] = total_slice
    report["summary"]["writtenSliceCount"] = total_written
    report["summary"]["keptExistingSliceCount"] = total_kept
    report["summary"]["missingAtlasImageCount"] = total_missing
    report["summary"]["removedBaseAtlasCount"] = total_removed_base
    report["summary"]["skippedAlreadySplitCount"] = total_skipped_split

    report_path = source_root / "split_atlas_report.json"
    if not args.dry_run:
        mapping_path.write_text(
            json.dumps(mapping_doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(f"[split] atlas_textures : {total_atlas_texture}")
    print(f"[split] slice_count    : {total_slice}")
    print(f"[split] written_slices : {total_written}")
    print(f"[split] kept_existing  : {total_kept}")
    print(f"[split] skipped_split  : {total_skipped_split}")
    print(f"[split] missing_atlas  : {total_missing}")
    print(f"[split] removed_base  : {total_removed_base}")
    if not args.dry_run:
        print(f"[split] updated mapping: {mapping_path}")
        print(f"[split] report         : {report_path}")
    if report["errors"]:
        print(f"[split] errors         : {len(report['errors'])}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
