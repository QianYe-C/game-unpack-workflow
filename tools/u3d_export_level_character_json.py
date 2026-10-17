#!/usr/bin/env python3
"""Export per-level character json with item id, split png, and category zh name."""

from __future__ import annotations

import argparse
import json
import re
import struct
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import UnityPy


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _auto_detect_data_unity3d(project_root: Path) -> Path:
    candidates = [
        project_root / "_extracted" / "data.unity3d",
        project_root / "_extracted_webdata" / "WebGL_0309_1459" / "data.unity3d",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(
        "data.unity3d not found. Expected _extracted/data.unity3d or "
        "_extracted_webdata/WebGL_0309_1459/data.unity3d"
    )


def _auto_detect_data_file(project_root: Path) -> Path:
    build_dir = project_root / "Build"
    candidates = sorted(build_dir.glob("*.data"))
    if not candidates:
        raise FileNotFoundError(f"No *.data under: {build_dir}")
    candidates.sort(key=lambda p: (p.stat().st_size, p.stat().st_mtime), reverse=True)
    return candidates[0]


def _extract_id_to_key(data_unity3d_path: Path) -> Dict[str, str]:
    env = UnityPy.load(str(data_unity3d_path))
    out: Dict[str, str] = {}

    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        try:
            d = obj.read()
        except Exception:
            continue

        name = getattr(d, "m_Name", None)
        script = getattr(d, "m_Script", None)
        if not (isinstance(name, str) and name.isdigit() and isinstance(script, str)):
            continue

        try:
            doc = json.loads(script)
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue

        for k, v in doc.items():
            if isinstance(k, str) and k.isdigit() and isinstance(v, str):
                out[k] = v

    return out


def _align4(offset: int) -> int:
    return (offset + 3) & ~3


def _read_u32_le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _read_aligned_utf8_string(data: bytes, offset: int, max_len: int = 2_000_000) -> Tuple[str, int]:
    if offset + 4 > len(data):
        raise ValueError("offset out of range for string length")
    length = _read_u32_le(data, offset)
    offset += 4
    if length > max_len or offset + length > len(data):
        raise ValueError(f"invalid string length {length} at {offset - 4}")
    value = data[offset : offset + length].decode("utf-8", errors="ignore")
    offset = _align4(offset + length)
    return value, offset


def _read_raw_object_bytes(obj: Any) -> bytes:
    af = obj.assets_file
    old_pos = af.reader.Position
    af.reader.Position = obj.byte_start
    raw = af.reader.read_bytes(obj.byte_size)
    af.reader.Position = old_pos
    return raw


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _parse_i2_term_record_from_key_anchor(raw: bytes, key_pos: int) -> Optional[Tuple[str, str, List[str]]]:
    """Parse one I2 term record by anchoring on key string position.

    Layout (observed in this project, local I2 source object):
      [u32 key_len][key_utf8][align4]
      [u32 desc_len][desc_utf8][align4]
      [u32 lang_count]
      repeated lang_count * [u32 len][utf8][align4]
      [u32 flags_count]
      repeated flags_count * [i32]
    """

    if key_pos < 4:
        return None
    try:
        key_len = _read_u32_le(raw, key_pos - 4)
    except Exception:
        return None

    if key_len <= 0 or key_len > 1024 or key_pos + key_len > len(raw):
        return None

    key = raw[key_pos : key_pos + key_len].decode("utf-8", errors="ignore")
    if not (key.startswith("Categories/") or key.startswith("StoryCategories/")):
        return None

    try:
        offset = _align4(key_pos + key_len)
        _desc, offset = _read_aligned_utf8_string(raw, offset)
        lang_count = _read_u32_le(raw, offset)
        offset += 4
        if lang_count > 16:
            return None

        langs: List[str] = []
        for _ in range(lang_count):
            text, offset = _read_aligned_utf8_string(raw, offset)
            langs.append(text)

        flag_count = _read_u32_le(raw, offset)
        offset += 4
        if flag_count > 16:
            return None
        if offset + 4 * flag_count > len(raw):
            return None
        offset += 4 * flag_count
    except Exception:
        return None

    return key, key[len("Categories/") :] if key.startswith("Categories/") else key[len("StoryCategories/") :], langs


def _extract_key_to_zh_from_i2_local_source(data_unity3d_path: Path) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Any]]:
    """Extract key->zh from local I2 terms embedded in data.unity3d.

    Returns:
      (category_suffix_to_zh, story_suffix_to_zh, meta)
    """

    env = UnityPy.load(str(data_unity3d_path))

    candidates: List[Tuple[Any, bytes, int]] = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        try:
            raw = _read_raw_object_bytes(obj)
        except Exception:
            continue

        cat_hits = raw.count(b"Categories/")
        story_hits = raw.count(b"StoryCategories/")
        score = cat_hits + story_hits
        if score <= 0:
            continue
        candidates.append((obj, raw, score))

    candidates.sort(key=lambda x: x[2], reverse=True)

    category_map: Dict[str, str] = {}
    story_map: Dict[str, str] = {}
    seen_full_keys: set[str] = set()
    selected: List[Dict[str, Any]] = []

    for obj, raw, score in candidates:
        selected.append(
            {
                "assetsFile": str(getattr(obj.assets_file, "name", "")),
                "pathId": int(getattr(obj, "path_id", 0)),
                "byteSize": int(getattr(obj, "byte_size", 0)),
                "score": int(score),
                "categoriesHitCount": int(raw.count(b"Categories/")),
                "storyCategoriesHitCount": int(raw.count(b"StoryCategories/")),
            }
        )

        for prefix in (b"Categories/", b"StoryCategories/"):
            pos = 0
            while True:
                found = raw.find(prefix, pos)
                if found < 0:
                    break
                pos = found + 1
                parsed = _parse_i2_term_record_from_key_anchor(raw, found)
                if not parsed:
                    continue
                full_key, suffix, langs = parsed
                if not suffix or full_key in seen_full_keys:
                    continue
                seen_full_keys.add(full_key)

                zh = ""
                for text in langs:
                    if _contains_cjk(text):
                        zh = text.strip()
                        if zh:
                            break

                if full_key.startswith("Categories/"):
                    if suffix not in category_map:
                        category_map[suffix] = zh
                elif full_key.startswith("StoryCategories/"):
                    if suffix not in story_map:
                        story_map[suffix] = zh

    meta = {
        "candidateCount": len(candidates),
        "selectedObjects": selected[:5],
        "parsedRecordCount": len(seen_full_keys),
        "categoriesCount": len(category_map),
        "storyCategoriesCount": len(story_map),
    }
    return category_map, story_map, meta


def _extract_key_to_zh_from_build_data_sparse(data_file: Path) -> Dict[str, str]:
    """Best-effort fallback from Build/*.data nearby text windows."""

    data = data_file.read_bytes()
    key_regex = re.compile(rb"(?:Categories|StoryCategories)/([A-Za-z0-9_]+)")
    zh_regex = re.compile(r"[\u4e00-\u9fff]{2,}")

    out: Dict[str, str] = {}
    for m in key_regex.finditer(data):
        key = m.group(1).decode("utf-8", errors="ignore")
        if not key:
            continue
        window = data[m.start() : min(len(data), m.start() + 700)]
        text = window.decode("utf-8", errors="ignore")
        zh_hits = zh_regex.findall(text)
        if not zh_hits:
            continue

        # Keep first non-trivial chinese phrase as candidate.
        phrase = ""
        for z in zh_hits:
            if len(z) >= 2:
                phrase = z
                break
        if phrase:
            out[key] = phrase

    return out


def _build_slice_indices(image_mapping_doc: Dict[str, Any]) -> Tuple[Dict[Tuple[str, str], List[str]], Dict[Tuple[str, str], List[str]]]:
    """Build indices for (bundleHash,spriteName) and (modeFolder,spriteName)."""

    by_bundle_sprite: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    by_mode_sprite: Dict[Tuple[str, str], List[str]] = defaultdict(list)

    for entry in image_mapping_doc.get("entries", []):
        if entry.get("kind") != "Texture2D":
            continue
        slices = entry.get("spriteAtlasSlices")
        if not isinstance(slices, list):
            continue

        mode = str(entry.get("modeFolder") or "")
        bundle_rel = str(entry.get("bundleRelPath") or "")
        bundle_hash = Path(bundle_rel).stem if bundle_rel else ""

        for s in slices:
            if not isinstance(s, dict):
                continue
            sprite_name = str(s.get("spriteName") or "")
            export_path = s.get("exportPath")
            if not sprite_name or not isinstance(export_path, str) or not export_path:
                continue

            if bundle_hash:
                by_bundle_sprite[(bundle_hash, sprite_name)].append(export_path)
            if mode:
                by_mode_sprite[(mode, sprite_name)].append(export_path)

    return by_bundle_sprite, by_mode_sprite


def _collect_item_rows(level_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_items = level_cfg.get("it")
    rows: List[Dict[str, Any]] = []
    if isinstance(raw_items, list):
        rows = [x for x in raw_items if isinstance(x, dict)]
    elif isinstance(raw_items, dict):
        for _, arr in sorted(raw_items.items(), key=lambda kv: str(kv[0])):
            if isinstance(arr, list):
                rows.extend(x for x in arr if isinstance(x, dict))
    return rows


def _collect_group_meta(level_cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for g in level_cfg.get("grs", []):
        if not isinstance(g, dict):
            continue
        gid = g.get("id")
        if gid is None:
            continue
        out[str(gid)] = g
    return out


def _translate_key_to_zh(
    key: str,
    session: requests.Session,
    cache: Dict[str, str],
    pause_sec: float,
) -> str:
    if not key:
        return ""

    if key in cache:
        return cache[key]

    phrase = key.replace("_", " ").strip()
    if not phrase:
        cache[key] = ""
        return ""

    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "zh-CN",
        "dt": "t",
        "q": phrase,
    }

    zh = ""
    try:
        resp = session.get(url, params=params, timeout=12)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            parts: List[str] = []
            for seg in payload[0]:
                if isinstance(seg, list) and seg and isinstance(seg[0], str):
                    parts.append(seg[0])
            zh = "".join(parts).strip()
    except Exception:
        zh = ""

    if pause_sec > 0:
        time.sleep(pause_sec)

    if not zh:
        zh = phrase

    cache[key] = zh
    return zh


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export per-level json including item id, split png path, and category zh name."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root, e.g. webprojects/drgm_ljpx2_lt",
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
        help="Path relative to source-config-root or absolute.",
    )
    parser.add_argument(
        "--image-mapping",
        default="image_mapping.json",
        help="Path relative to source-image-root or absolute.",
    )
    parser.add_argument(
        "--data-unity3d",
        default="",
        help="Optional data.unity3d path. Auto-detect if omitted.",
    )
    parser.add_argument(
        "--build-data",
        default="",
        help=(
            "Optional Build/*.data path for sparse fallback extraction. "
            "By default, chinese names are resolved from local I2 terms in data.unity3d."
        ),
    )
    parser.add_argument(
        "--output-root",
        default="",
        help=(
            "Output root. Default: <source-config-root>/levelCharacterJson"
        ),
    )
    parser.add_argument(
        "--translate-missing",
        action="store_true",
        help=(
            "Translate missing keys via Google endpoint (disabled by default; "
            "local I2 terms are used first)."
        ),
    )
    parser.add_argument(
        "--translation-cache",
        default="translation_cache.json",
        help="Cache path relative to output-root or absolute.",
    )
    parser.add_argument(
        "--translate-pause-sec",
        type=float,
        default=0.02,
        help="Sleep seconds between translation requests.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()

    project_root = _resolve(cwd, args.project_root).resolve()
    source_config_root = _resolve(cwd, args.source_config_root).resolve()
    source_image_root = _resolve(cwd, args.source_image_root).resolve()
    config_mapping_path = _resolve(source_config_root, args.config_mapping).resolve()
    image_mapping_path = _resolve(source_image_root, args.image_mapping).resolve()

    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")
    if not source_config_root.is_dir():
        raise SystemExit(f"source-config-root not found: {source_config_root}")
    if not source_image_root.is_dir():
        raise SystemExit(f"source-image-root not found: {source_image_root}")
    if not config_mapping_path.is_file():
        raise SystemExit(f"config mapping not found: {config_mapping_path}")
    if not image_mapping_path.is_file():
        raise SystemExit(f"image mapping not found: {image_mapping_path}")

    if args.data_unity3d:
        data_unity3d_path = _resolve(cwd, args.data_unity3d).resolve()
    else:
        data_unity3d_path = _auto_detect_data_unity3d(project_root)
    if not data_unity3d_path.is_file():
        raise SystemExit(f"data.unity3d not found: {data_unity3d_path}")

    build_data_path: Optional[Path] = None
    if args.build_data:
        build_data_path = _resolve(cwd, args.build_data).resolve()
        if not build_data_path.is_file():
            raise SystemExit(f"build data file not found: {build_data_path}")

    if args.output_root:
        output_root = _resolve(cwd, args.output_root).resolve()
    else:
        output_root = (source_config_root / "levelCharacterJson").resolve()

    output_root.mkdir(parents=True, exist_ok=True)
    translation_cache_path = _resolve(output_root, args.translation_cache).resolve()

    config_map = _load_json(config_mapping_path)
    image_map = _load_json(image_mapping_path)

    id_to_key = _extract_id_to_key(data_unity3d_path)
    key_to_zh_category_local, key_to_zh_story_local, i2_local_meta = _extract_key_to_zh_from_i2_local_source(
        data_unity3d_path
    )
    key_to_zh_local_all: Dict[str, str] = {}
    key_to_zh_local_all.update({k: v for k, v in key_to_zh_category_local.items() if v})
    for k, v in key_to_zh_story_local.items():
        if v and k not in key_to_zh_local_all:
            key_to_zh_local_all[k] = v

    translation_cache: Dict[str, str] = {}
    if translation_cache_path.is_file():
        try:
            doc = _load_json(translation_cache_path)
            for k, v in doc.items():
                if isinstance(v, str):
                    translation_cache[str(k)] = v
        except Exception:
            pass

    # Local I2 mapping has highest priority.
    translation_cache.update(key_to_zh_local_all)

    # Optional fallback: sparse extraction from Build/*.data
    key_to_zh_sparse: Dict[str, str] = {}
    if build_data_path is not None:
        key_to_zh_sparse = _extract_key_to_zh_from_build_data_sparse(build_data_path)
        for k, v in key_to_zh_sparse.items():
            if v and not translation_cache.get(k):
                translation_cache[k] = v

    by_bundle_sprite, by_mode_sprite = _build_slice_indices(image_map)

    # First pass: parse level configs and collect needed category keys.
    parsed_levels: List[Dict[str, Any]] = []
    needed_ct_keys: Dict[str, str] = {}  # ct -> key

    for entry in config_map.get("entries", []):
        export_rel = entry.get("exportPath")
        if not isinstance(export_rel, str) or not export_rel:
            continue
        cfg_path = source_config_root / export_rel
        if not cfg_path.is_file():
            continue

        try:
            level_cfg = _load_json(cfg_path)
        except Exception:
            continue

        board_id = str(entry.get("boardDataId") or cfg_path.stem)
        mode_folder = str(entry.get("modeFolder") or "Others")
        deps = entry.get("deps") if isinstance(entry.get("deps"), list) else []

        atlas_hashes: List[str] = []
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            dep_name = str(dep.get("depBundleName") or "").lower()
            dep_hash = str(dep.get("depBundleHash") or "")
            if not dep_hash:
                continue
            if "atlas" in dep_name:
                atlas_hashes.append(dep_hash)

        items = _collect_item_rows(level_cfg)
        groups = _collect_group_meta(level_cfg)

        for g in groups.values():
            ct = g.get("ct")
            if ct is None:
                continue
            ct_str = str(ct)
            key = id_to_key.get(ct_str, "")
            if key:
                needed_ct_keys[ct_str] = key

        parsed_levels.append(
            {
                "entry": entry,
                "boardId": board_id,
                "modeFolder": mode_folder,
                "atlasHashes": atlas_hashes,
                "items": items,
                "groups": groups,
                "configPath": cfg_path,
                "configRel": export_rel,
            }
        )

    # Translate missing category keys on demand.
    if args.translate_missing:
        session = requests.Session()
        for key in sorted(set(needed_ct_keys.values())):
            if key in translation_cache and translation_cache[key]:
                continue
            _translate_key_to_zh(
                key=key,
                session=session,
                cache=translation_cache,
                pause_sec=max(0.0, float(args.translate_pause_sec)),
            )

    # persist cache
    translation_cache_path.parent.mkdir(parents=True, exist_ok=True)
    translation_cache_path.write_text(
        json.dumps(translation_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Second pass: export per-level json
    written = 0
    unresolved_item_image = 0
    unresolved_category_key = 0
    unresolved_category_zh = 0

    manifest_rows: List[Dict[str, Any]] = []

    for level in parsed_levels:
        entry = level["entry"]
        board_id = level["boardId"]
        mode_folder = level["modeFolder"]
        atlas_hashes: List[str] = level["atlasHashes"]
        items: List[Dict[str, Any]] = level["items"]
        group_meta: Dict[str, Dict[str, Any]] = level["groups"]

        grouped_items: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for it in items:
            iid = it.get("id")
            gid = it.get("g")
            if iid is None or gid is None:
                continue
            iid_str = str(iid)
            gid_str = str(gid)

            image_path = ""
            for h in atlas_hashes:
                bucket = by_bundle_sprite.get((h, iid_str), [])
                if bucket:
                    image_path = bucket[0]
                    break
            if not image_path:
                fallback = by_mode_sprite.get((mode_folder, iid_str), [])
                if fallback:
                    image_path = fallback[0]
            if not image_path:
                unresolved_item_image += 1

            grouped_items[gid_str].append(
                {
                    "itemId": iid_str,
                    "imagePng": image_path,
                }
            )

        group_rows: List[Dict[str, Any]] = []
        flat_rows: List[Dict[str, Any]] = []

        for gid in sorted(grouped_items.keys()):
            meta = group_meta.get(gid, {})
            ct = meta.get("ct")
            ct_str = str(ct) if ct is not None else ""
            key = id_to_key.get(ct_str, "")
            zh = ""
            key_scope = ""
            if key:
                if mode_folder.startswith("Story_"):
                    if key in key_to_zh_story_local:
                        zh = key_to_zh_story_local[key]
                        key_scope = "StoryCategories"
                    elif key in key_to_zh_category_local:
                        zh = key_to_zh_category_local[key]
                        key_scope = "Categories"
                else:
                    if key in key_to_zh_category_local:
                        zh = key_to_zh_category_local[key]
                        key_scope = "Categories"
                    elif key in key_to_zh_story_local:
                        zh = key_to_zh_story_local[key]
                        key_scope = "StoryCategories"

                if not zh:
                    zh = translation_cache.get(key, "")
                    if zh:
                        key_scope = "Cache"

            if ct_str and not key:
                unresolved_category_key += 1
            if key and not zh:
                unresolved_category_zh += 1

            group_row = {
                "groupId": gid,
                "categoryTypeId": ct,
                "categoryKey": key,
                "categoryTermScope": key_scope,
                "categoryNameZh": zh,
                "metaMi": meta.get("mi"),
                "items": grouped_items[gid],
            }
            group_rows.append(group_row)

            for item_row in grouped_items[gid]:
                flat_rows.append(
                    {
                        "itemId": item_row["itemId"],
                        "imagePng": item_row["imagePng"],
                        "groupId": gid,
                        "categoryTypeId": ct,
                        "categoryKey": key,
                        "categoryTermScope": key_scope,
                        "categoryNameZh": zh,
                    }
                )

        out_doc = {
            "schema": "u3d-level-character-json-v1",
            "generatedAt": _utc_now(),
            "boardDataId": board_id,
            "modeFolder": mode_folder,
            "assetAddress": entry.get("assetAddress"),
            "configPath": level["configRel"],
            "atlasBundleHashes": atlas_hashes,
            "groups": group_rows,
            "characters": flat_rows,
        }

        mode_dir = output_root / mode_folder
        mode_dir.mkdir(parents=True, exist_ok=True)
        out_path = mode_dir / f"{board_id}.json"
        out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        written += 1

        manifest_rows.append(
            {
                "boardDataId": board_id,
                "modeFolder": mode_folder,
                "outputPath": str(out_path.relative_to(output_root)),
                "characterCount": len(flat_rows),
                "groupCount": len(group_rows),
            }
        )

    summary = {
        "schema": "u3d-level-character-json-summary-v1",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "sourceConfigRoot": str(source_config_root),
        "sourceImageRoot": str(source_image_root),
        "dataUnity3d": str(data_unity3d_path),
        "buildData": str(build_data_path) if build_data_path is not None else "",
        "outputRoot": str(output_root),
        "writtenLevelJsonCount": written,
        "idToKeyCount": len(id_to_key),
        "i2LocalMeta": i2_local_meta,
        "i2LocalCategoryKeyCount": len(key_to_zh_category_local),
        "i2LocalStoryKeyCount": len(key_to_zh_story_local),
        "i2LocalAllKeyCount": len(key_to_zh_local_all),
        "sparseKeyZhCount": len(key_to_zh_sparse),
        "translationCacheCount": len(translation_cache),
        "unresolved": {
            "itemImage": unresolved_item_image,
            "categoryKey": unresolved_category_key,
            "categoryZh": unresolved_category_zh,
        },
        "levels": manifest_rows,
    }

    summary_path = output_root / "level_character_manifest.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[level-character] project_root        : {project_root}")
    print(f"[level-character] source_config_root  : {source_config_root}")
    print(f"[level-character] source_image_root   : {source_image_root}")
    print(f"[level-character] data_unity3d        : {data_unity3d_path}")
    print(f"[level-character] build_data          : {build_data_path or ''}")
    print(f"[level-character] written level jsons : {written}")
    print(f"[level-character] id->key count       : {len(id_to_key)}")
    print(f"[level-character] i2 local category   : {len(key_to_zh_category_local)}")
    print(f"[level-character] i2 local story      : {len(key_to_zh_story_local)}")
    print(f"[level-character] sparse key->zh      : {len(key_to_zh_sparse)}")
    print(f"[level-character] translation cache   : {len(translation_cache)}")
    print(f"[level-character] unresolved image    : {unresolved_item_image}")
    print(f"[level-character] unresolved ct key   : {unresolved_category_key}")
    print(f"[level-character] unresolved ct zh    : {unresolved_category_zh}")
    print(f"[level-character] manifest            : {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
