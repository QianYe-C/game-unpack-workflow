#!/usr/bin/env python3
"""Export cocos images to sourceImages as decoded full textures."""

from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from cocos_image_utils import (
    BundleConfig,
    build_import_index,
    build_native_image_index,
    decode_netease_bytes,
    decode_uuid,
    discover_bundle_configs,
    extract_spriteframe_from_entry,
    is_netease_encrypted,
    load_json,
    sanitize_rel_component,
    save_json,
    sha256_bytes,
    strip_uuid_suffix,
)


def _arg() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export cocos decoded images as full textures.")
    p.add_argument(
        "--project",
        default="/Users/jiaojian/Documents/localweb/doomsdayroom_web-mobile1",
        help="Cocos web build root.",
    )
    p.add_argument(
        "--out",
        default="/Users/jiaojian/Documents/localweb/sourceImages",
        help="Output source image directory.",
    )
    p.add_argument(
        "--clean",
        action="store_true",
        help="Delete output directory before export.",
    )
    return p.parse_args()


def _version_get(version_map: Dict[Any, str], idx_or_key: Any) -> Optional[str]:
    if idx_or_key in version_map:
        return version_map[idx_or_key]
    k = str(idx_or_key)
    if k in version_map:
        return version_map[k]
    return None


def _resolve_native(
    native_index,
    texture_uuid: str,
    native_hash: Optional[str],
) -> Optional[Path]:
    candidates = [texture_uuid, texture_uuid.replace("-", "")]
    for cid in candidates:
        hit = native_index.resolve(cid, native_hash)
        if hit:
            return hit
    for cid in candidates:
        hit = native_index.resolve(cid, None)
        if hit:
            return hit
    return None


def _resolve_import(import_index, asset_id: str, import_hash: Optional[str]) -> Optional[Path]:
    hit = import_index.resolve(asset_id, import_hash)
    if hit:
        return hit
    if "-" in asset_id:
        compact = asset_id.replace("-", "")
        hit = import_index.resolve(compact, import_hash)
        if hit:
            return hit
        hit = import_index.resolve(compact, None)
        if hit:
            return hit
    return import_index.resolve(asset_id, None)


def _to_int_list(v: Any, length: int, default: int = 0) -> List[int]:
    if not isinstance(v, list):
        return [default] * length
    out = []
    for i in range(length):
        if i < len(v):
            try:
                out.append(int(round(float(v[i]))))
            except Exception:
                out.append(default)
        else:
            out.append(default)
    return out


def _load_spriteframes_for_bundle(bundle_cfg: BundleConfig) -> List[Dict[str, Any]]:
    cfg = bundle_cfg.cfg
    types = cfg.get("types", [])
    paths = cfg.get("paths", {})
    uuids = cfg.get("uuids", [])
    packs = cfg.get("packs", {})

    import_index = build_import_index(bundle_cfg.bundle_dir, bundle_cfg.import_base)
    pack_pos: Dict[int, Tuple[str, int]] = {}
    for pack_id, idxs in packs.items():
        for pos, idx in enumerate(idxs):
            pack_pos[int(idx)] = (str(pack_id), pos)

    pack_cache: Dict[str, Any] = {}
    sf_path_by_index: Dict[int, str] = {}
    for idx_str, raw_path_entry in paths.items():
        idx = int(idx_str)
        if not isinstance(raw_path_entry, list) or len(raw_path_entry) < 2:
            continue
        type_idx = raw_path_entry[1]
        if type_idx < 0 or type_idx >= len(types) or types[type_idx] != "cc.SpriteFrame":
            continue
        sf_path_by_index[idx] = str(raw_path_entry[0])

    out: List[Dict[str, Any]] = []
    seen_indices: set[int] = set()

    def _append_spriteframe(idx: int, sf_path: Optional[str]) -> bool:
        if idx < 0 or idx >= len(uuids):
            return False
        sf_uuid = strip_uuid_suffix(decode_uuid(uuids[idx]))
        entry: Optional[Any] = None
        root_uuids: List[Any] = []
        if idx in pack_pos:
            pack_id, pos = pack_pos[idx]
            if pack_id not in pack_cache:
                pack_hash = _version_get(bundle_cfg.versions_import, pack_id)
                pack_file = _resolve_import(import_index, pack_id, pack_hash)
                if not pack_file:
                    return False
                try:
                    pack_cache[pack_id] = (pack_file, load_json(pack_file))
                except Exception:
                    return False
            _, pack_root = pack_cache[pack_id]
            if (
                isinstance(pack_root, list)
                and len(pack_root) >= 6
                and isinstance(pack_root[1], list)
                and isinstance(pack_root[5], list)
                and pos < len(pack_root[5])
            ):
                entry = pack_root[5][pos]
                root_uuids = pack_root[1]
        else:
            sf_hash = _version_get(bundle_cfg.versions_import, idx)
            sf_file = _resolve_import(import_index, sf_uuid, sf_hash)
            if not sf_file:
                return False
            try:
                root = load_json(sf_file)
            except Exception:
                return False
            entry = root
            if isinstance(root, list) and len(root) >= 2 and isinstance(root[1], list):
                root_uuids = root[1]

        frame, tex_uuid = extract_spriteframe_from_entry(entry, root_uuids)
        if not frame or not tex_uuid:
            return False
        path_hint = sf_path or f"__untracked__/{sf_uuid}"
        out.append(
            {
                "sfIndex": idx,
                "sfUuid": sf_uuid,
                "sfPath": path_hint,
                "frameName": frame.get("name") or path_hint.split("/")[-1],
                "rect": _to_int_list(frame.get("rect"), 4),
                "rotated": bool(frame.get("rotated", 0)),
                "originalSize": _to_int_list(frame.get("originalSize"), 2),
                "offset": _to_int_list(frame.get("offset"), 2),
                "textureUuid": strip_uuid_suffix(tex_uuid),
            }
        )
        return True

    for idx in sorted(sf_path_by_index.keys()):
        if _append_spriteframe(idx, sf_path_by_index[idx]):
            seen_indices.add(idx)

    # Some bundles keep SpriteFrame imports only in versions.import (no config.paths entry).
    for idx in sorted(k for k in bundle_cfg.versions_import.keys() if isinstance(k, int)):
        if idx in seen_indices:
            continue
        if _append_spriteframe(idx, sf_path_by_index.get(idx)):
            seen_indices.add(idx)

    return out


def _build_textures_for_bundle(bundle_cfg: BundleConfig) -> Dict[str, Dict[str, Any]]:
    cfg = bundle_cfg.cfg
    types = cfg.get("types", [])
    paths = cfg.get("paths", {})
    uuids = cfg.get("uuids", [])
    native_index = build_native_image_index(bundle_cfg.bundle_dir, bundle_cfg.native_base)

    out: Dict[str, Dict[str, Any]] = {}
    for idx_str, raw_path_entry in paths.items():
        idx = int(idx_str)
        if not isinstance(raw_path_entry, list) or len(raw_path_entry) < 2:
            continue
        type_idx = raw_path_entry[1]
        if type_idx < 0 or type_idx >= len(types) or types[type_idx] != "cc.Texture2D":
            continue

        texture_uuid = strip_uuid_suffix(decode_uuid(uuids[idx]))
        logical_path = str(raw_path_entry[0])
        native_hash = _version_get(bundle_cfg.versions_native, idx)
        native_path = _resolve_native(native_index, texture_uuid, native_hash)
        if not native_path:
            continue
        out[texture_uuid] = {
            "bundle": bundle_cfg.bundle,
            "textureIndex": idx,
            "textureUuid": texture_uuid,
            "logicalPath": logical_path,
            "nativePath": str(native_path),
            "nativeHash": native_hash,
            "ext": native_path.suffix.lower(),
            "spriteFrames": [],
        }
    return out


def _add_orphan_native_images(bundle_cfg: BundleConfig, textures: Dict[str, Dict[str, Any]]) -> int:
    native_dir = bundle_cfg.bundle_dir / bundle_cfg.native_base
    if not native_dir.exists():
        return 0

    known_ids = set()
    for uuid in textures.keys():
        known_ids.add(uuid)
        known_ids.add(uuid.replace("-", ""))

    added = 0
    for p in native_dir.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        stem = p.stem
        if "." in stem:
            asset_id, asset_hash = stem.rsplit(".", 1)
        else:
            asset_id, asset_hash = stem, ""
        if asset_id in known_ids:
            continue
        textures[asset_id] = {
            "bundle": bundle_cfg.bundle,
            "textureIndex": -1,
            "textureUuid": asset_id,
            "logicalPath": f"__native__/{asset_id}",
            "nativePath": str(p),
            "nativeHash": asset_hash if asset_hash else None,
            "ext": p.suffix.lower(),
            "spriteFrames": [],
        }
        known_ids.add(asset_id)
        added += 1
    return added


def _is_atlas_like(texture_size: Tuple[int, int], frames: List[Dict[str, Any]]) -> bool:
    if not frames:
        return False
    if len(frames) > 1:
        return True
    w, h = texture_size
    f = frames[0]
    x, y, rw, rh = f["rect"]
    if (x, y, rw, rh) != (0, 0, w, h):
        return True
    if f["rotated"]:
        return True
    if f["originalSize"] != [w, h]:
        return True
    if f["offset"] != [0, 0]:
        return True
    return False


def _export_texture(
    source_root: Path,
    project_root: Path,
    texture: Dict[str, Any],
) -> Optional[Tuple[bytes, Image.Image]]:
    native_path = Path(texture["nativePath"])
    if not native_path.exists():
        return None
    raw = native_path.read_bytes()
    decoded = decode_netease_bytes(raw)
    encoded = is_netease_encrypted(raw)
    texture["encoded"] = encoded

    rel_target = Path("textures") / sanitize_rel_component(texture["bundle"]) / (
        sanitize_rel_component(texture["logicalPath"]) + texture["ext"]
    )
    target = source_root / rel_target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(decoded)

    texture["nativePath"] = str(native_path.relative_to(project_root))
    texture["decodedPath"] = str(rel_target).replace("\\", "/")
    texture["decodedHash"] = sha256_bytes(decoded)

    try:
        img = Image.open(io.BytesIO(decoded)).convert("RGBA")
    except Exception:
        return None
    texture["width"], texture["height"] = img.size
    return decoded, img


def main() -> int:
    args = _arg()
    project_root = Path(args.project).resolve()
    source_root = Path(args.out).resolve()

    if args.clean and source_root.exists():
        shutil.rmtree(source_root)
    source_root.mkdir(parents=True, exist_ok=True)

    bundles = discover_bundle_configs(project_root)
    manifest: Dict[str, Any] = {
        "version": 1,
        "projectRoot": str(project_root),
        "sourceRoot": str(source_root),
        "generatedBy": "tools/cocos_export_source_images.py",
        "textures": [],
        "stats": {},
    }

    exported_textures = 0
    atlas_textures = 0
    missing_textures = 0
    missing_frame_bindings = 0
    orphan_images_added = 0

    for bundle_cfg in bundles:
        textures = _build_textures_for_bundle(bundle_cfg)
        orphan_images_added += _add_orphan_native_images(bundle_cfg, textures)
        texture_by_path = {
            t["logicalPath"]: t for t in textures.values() if isinstance(t.get("logicalPath"), str)
        }
        spriteframes = _load_spriteframes_for_bundle(bundle_cfg)
        for sf in spriteframes:
            tex_uuid = sf["textureUuid"]
            if tex_uuid in textures:
                textures[tex_uuid]["spriteFrames"].append(sf)
            elif sf["sfPath"] in texture_by_path:
                texture_by_path[sf["sfPath"]]["spriteFrames"].append(sf)
            else:
                missing_frame_bindings += 1

        for texture in textures.values():
            exported = _export_texture(source_root, project_root, texture)
            if not exported:
                missing_textures += 1
                continue
            _, image = exported
            texture["spriteFrames"].sort(key=lambda v: v["sfIndex"])
            texture["atlasLike"] = _is_atlas_like(image.size, texture["spriteFrames"])
            texture["frames"] = []
            if texture["atlasLike"]:
                atlas_textures += 1
            manifest["textures"].append(texture)
            exported_textures += 1

    manifest["textures"].sort(key=lambda t: (t["bundle"], t["logicalPath"]))
    manifest["stats"] = {
        "bundleCount": len(bundles),
        "exportedTextures": exported_textures,
        "atlasTextures": atlas_textures,
        "atlasFrames": 0,
        "missingTextureFiles": missing_textures,
        "missingFrameBindings": missing_frame_bindings,
        "orphanImagesAdded": orphan_images_added,
        "totalManifestTextures": len(manifest["textures"]),
    }

    save_json(source_root / "manifest.json", manifest)
    print(f"[export] source root: {source_root}")
    print(f"[export] textures: {exported_textures}, atlas textures: {atlas_textures}")
    print(
        f"[export] missing texture files: {missing_textures}, "
        f"missing frame bindings: {missing_frame_bindings}, orphan images: {orphan_images_added}"
    )
    print("[export] manifest: sourceImages/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
