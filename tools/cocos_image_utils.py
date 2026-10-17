#!/usr/bin/env python3
"""Shared helpers for cocos image export/import workflows."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ENC_MAGIC = b"netease"
ENC_HEADER = bytes([0x01, 0x01, 0x01, 0x6F])
ENC_KEY_A = "ee02fb77bf0bbb5e833173efd043e55b"
ENC_KEY_B = "husgyeasabzsd"

_BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_BASE64_MAP = {c: i for i, c in enumerate(_BASE64_CHARS)}
_HEX = "0123456789abcdef"


@dataclass
class BundleConfig:
    bundle: str
    bundle_dir: Path
    cfg_path: Path
    cfg: Dict[str, Any]
    import_base: str
    native_base: str
    versions_import: Dict[Any, str]
    versions_native: Dict[Any, str]


class IndexMap:
    def __init__(self) -> None:
        self.by_id_hash: Dict[Tuple[str, str], Path] = {}
        self.by_id: Dict[str, List[Path]] = {}

    def add(self, asset_id: str, asset_hash: str, path: Path) -> None:
        key = (asset_id, asset_hash)
        if key not in self.by_id_hash:
            self.by_id_hash[key] = path
        self.by_id.setdefault(asset_id, []).append(path)

    def resolve(self, asset_id: str, asset_hash: Optional[str]) -> Optional[Path]:
        if asset_hash:
            hit = self.by_id_hash.get((asset_id, asset_hash))
            if hit:
                return hit
        hits = self.by_id.get(asset_id)
        if hits:
            return hits[0]
        return None


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: Any) -> None:
    ensure_dir(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _xor_key() -> bytes:
    a = bytearray(ENC_KEY_A.encode("utf-8"))
    b = ENC_KEY_B.encode("utf-8")
    m = min(len(a), len(b))
    for i in range(m):
        a[i] ^= b[i]
    return bytes(a)


_XOR_KEY = _xor_key()


def is_netease_encrypted(data: bytes) -> bool:
    return (
        len(data) > 11
        and data.startswith(ENC_MAGIC)
        and data[7:11] == ENC_HEADER
    )


def decode_netease_bytes(data: bytes) -> bytes:
    if not is_netease_encrypted(data):
        return data
    body = bytearray(data[11:])
    key_len = len(_XOR_KEY)
    for i in range(len(body)):
        body[i] ^= _XOR_KEY[i % key_len]
    return bytes(body)


def encode_netease_bytes(decoded: bytes) -> bytes:
    body = bytearray(decoded)
    key_len = len(_XOR_KEY)
    for i in range(len(body)):
        body[i] ^= _XOR_KEY[i % key_len]
    return ENC_MAGIC + ENC_HEADER + bytes(body)


def strip_uuid_suffix(uuid_text: str) -> str:
    return uuid_text.split("@", 1)[0]


def decode_uuid(raw_uuid: str) -> str:
    if not raw_uuid:
        return raw_uuid
    if "@" in raw_uuid:
        main, suffix = raw_uuid.split("@", 1)
    else:
        main, suffix = raw_uuid, None

    decoded = main
    if len(main) == 22:
        out = [main[0], main[1]]
        for i in range(2, 22, 2):
            lhs = _BASE64_MAP[main[i]]
            rhs = _BASE64_MAP[main[i + 1]]
            out.append(_HEX[lhs >> 2])
            out.append(_HEX[((lhs & 0x3) << 2) | (rhs >> 4)])
            out.append(_HEX[rhs & 0xF])
        s = "".join(out)
        decoded = f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"

    if suffix:
        return f"{decoded}@{suffix}"
    return decoded


def parse_versions_map(raw_list: Iterable[Any]) -> Dict[Any, str]:
    arr = list(raw_list or [])
    out: Dict[Any, str] = {}
    for i in range(0, len(arr), 2):
        if i + 1 < len(arr):
            out[arr[i]] = str(arr[i + 1])
    return out


def discover_bundle_configs(project_root: Path) -> List[BundleConfig]:
    assets_dir = project_root / "assets"
    bundles: List[BundleConfig] = []
    if not assets_dir.exists():
        return bundles

    for entry in sorted(assets_dir.iterdir()):
        if not entry.is_dir():
            continue
        cfg_files = [p for p in entry.iterdir() if p.is_file() and re.match(r"^config\..+\.json$", p.name)]
        if not cfg_files:
            continue
        cfg_path = sorted(cfg_files)[0]
        cfg = load_json(cfg_path)
        versions = cfg.get("versions", {})
        bundles.append(
            BundleConfig(
                bundle=entry.name,
                bundle_dir=entry,
                cfg_path=cfg_path,
                cfg=cfg,
                import_base=cfg.get("importBase", "import"),
                native_base=cfg.get("nativeBase", "native"),
                versions_import=parse_versions_map(versions.get("import", [])),
                versions_native=parse_versions_map(versions.get("native", [])),
            )
        )
    return bundles


def build_import_index(bundle_dir: Path, import_base: str) -> IndexMap:
    out = IndexMap()
    import_dir = bundle_dir / import_base
    if not import_dir.exists():
        return out
    for root, _, files in os.walk(import_dir):
        for name in files:
            if not name.endswith(".json"):
                continue
            stem = name[:-5]
            if "." in stem:
                asset_id, asset_hash = stem.rsplit(".", 1)
            else:
                asset_id, asset_hash = stem, ""
            out.add(asset_id, asset_hash, Path(root) / name)
    return out


def build_native_image_index(bundle_dir: Path, native_base: str) -> IndexMap:
    out = IndexMap()
    native_dir = bundle_dir / native_base
    if not native_dir.exists():
        return out
    for root, _, files in os.walk(native_dir):
        for name in files:
            p = Path(root) / name
            ext = p.suffix.lower()
            if ext not in IMAGE_EXTS:
                continue
            stem = p.stem
            if "." in stem:
                asset_id, asset_hash = stem.rsplit(".", 1)
            else:
                asset_id, asset_hash = stem, ""
            out.add(asset_id, asset_hash, p)
    return out


def sanitize_rel_component(text: str) -> str:
    text = text.replace("\\", "/").strip("/")
    parts = []
    for raw in text.split("/"):
        safe = re.sub(r'[<>:"|?*]', "_", raw).strip()
        parts.append(safe if safe else "_")
    return "/".join(parts)


def is_frame_object(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("name"), str)
        and isinstance(obj.get("rect"), list)
        and len(obj["rect"]) == 4
    )


def resolve_uuid_ref(ref: Any, root_uuids: List[Any]) -> Optional[str]:
    if isinstance(ref, int) and 0 <= ref < len(root_uuids):
        raw = root_uuids[ref]
        if isinstance(raw, str):
            return strip_uuid_suffix(decode_uuid(raw))
    elif isinstance(ref, str):
        return strip_uuid_suffix(decode_uuid(ref))
    return None


def extract_spriteframe_from_entry(entry: Any, root_uuids: List[Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(entry, list):
        return None, None

    # Pack entry style:
    # [[{frame}],[...],0,[...],[...],[texRef]]
    if (
        len(entry) >= 6
        and isinstance(entry[0], list)
        and entry[0]
        and is_frame_object(entry[0][0])
    ):
        frame = dict(entry[0][0])
        tex_ref = None
        if isinstance(entry[5], list) and entry[5]:
            tex_ref = entry[5][0]
        tex_uuid = resolve_uuid_ref(tex_ref, root_uuids)
        return frame, tex_uuid

    # Direct file style:
    # [1,[texUuid],["_textureSetter"],["cc.SpriteFrame"],0,[{frame}],...]
    if len(entry) >= 6 and isinstance(entry[5], list):
        frame = next((v for v in entry[5] if is_frame_object(v)), None)
        if frame:
            tex_ref = None
            if isinstance(entry[1], list) and entry[1]:
                tex_ref = entry[1][0]
            tex_uuid = resolve_uuid_ref(tex_ref, root_uuids)
            if not tex_uuid:
                for raw in root_uuids:
                    if isinstance(raw, str):
                        tex_uuid = strip_uuid_suffix(decode_uuid(raw))
                        break
            return dict(frame), tex_uuid

    return None, None

