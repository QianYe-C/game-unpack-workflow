#!/usr/bin/env python3
"""Export editable Texture2D images from Unity bundles and WebGL webdata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

import UnityPy

WEBDATA_HEADER = b"UnityWebData1.0\0"


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
    return value[:80] or "unnamed"


def _build_output_rel(bundle_stem: str, path_id: int, name: str) -> Path:
    filename = f"{bundle_stem}_{path_id}_{_safe_name(name)}.png"
    return Path("images") / filename


def _iter_bundles(asset_dir: Path) -> List[Path]:
    return sorted(asset_dir.glob("*.unity3d"))


def _iter_webdata_files(webdata_dir: Path, pattern: str) -> List[Path]:
    if not webdata_dir.is_dir():
        return []
    return sorted(webdata_dir.glob(pattern))


def _default_output_root(project_root: Path) -> Path:
    # New layout: myprojects/<project>/webprojects
    if project_root.name == "webprojects":
        return (project_root.parent / "sourceImages").resolve()
    # Legacy layout: webprojects/<project>
    return (project_root.parent.parent / "sourceImages" / project_root.name).resolve()


def _extract_unity_webdata(data_path: Path, out_dir: Path) -> int:
    data = data_path.read_bytes()
    if not data.startswith(WEBDATA_HEADER):
        raise RuntimeError(f"Unknown webdata header: {data_path}")

    def u32_le(offset: int) -> int:
        return int.from_bytes(data[offset : offset + 4], "little", signed=False)

    n = len(WEBDATA_HEADER)
    table_end = u32_le(n)
    n += 4

    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    while n < table_end:
        data_offset = u32_le(n)
        n += 4
        data_length = u32_le(n)
        n += 4
        path_length = u32_le(n)
        n += 4
        rel_bytes = data[n : n + path_length]
        if b"\x00" in rel_bytes:
            rel_bytes = rel_bytes.split(b"\x00", 1)[0]
        rel_path = rel_bytes.decode("utf-8", errors="ignore").lstrip("/")
        n += path_length
        if not rel_path:
            continue
        out_path = out_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data[data_offset : data_offset + data_length])
        count += 1
    return count


def _export_container(
    container_path: Path,
    container_rel: str,
    container_name: str,
    output_root: Path,
    used_export_paths: Set[str],
    entry_meta: Dict[str, object] | None = None,
    stats_meta: Dict[str, object] | None = None,
) -> Tuple[List[Dict], Dict]:
    env = UnityPy.load(str(container_path))

    entries: List[Dict] = []
    stats = {
        "containerName": container_name,
        "containerRelPath": container_rel,
        "containerFile": container_path.name,
        "objectCount": 0,
        "textureObjects": 0,
        "exportedTextures": 0,
        "failedTextures": 0,
    }
    if stats_meta:
        stats.update(stats_meta)

    for obj in env.objects:
        stats["objectCount"] += 1
        if obj.type.name != "Texture2D":
            continue
        stats["textureObjects"] += 1

        try:
            texture = obj.read()
            image = texture.image
            if image is None:
                raise RuntimeError("Texture2D.image is None")

            name = getattr(texture, "m_Name", "") or ""
            rel_path = _build_output_rel(
                container_path.stem, int(obj.path_id), name
            )
            if rel_path.as_posix() in used_export_paths:
                i = 1
                while True:
                    candidate = rel_path.with_name(
                        f"{rel_path.stem}_dup{i}{rel_path.suffix}"
                    )
                    if candidate.as_posix() not in used_export_paths:
                        rel_path = candidate
                        break
                    i += 1
            used_export_paths.add(rel_path.as_posix())

            abs_path = output_root / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(abs_path, format="PNG")
            width, height = image.size

            entries.append(
                {
                    "kind": "Texture2D",
                    "bundleFile": container_path.name,
                    "bundleRelPath": container_rel,
                    "pathId": int(obj.path_id),
                    "assetsFile": str(getattr(obj.assets_file, "name", "") or ""),
                    "name": name,
                    "width": int(width),
                    "height": int(height),
                    "exportPath": rel_path.as_posix(),
                    "sha256": _sha256_file(abs_path),
                }
            )
            if entry_meta:
                entries[-1].update(entry_meta)
            stats["exportedTextures"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failedTextures"] += 1
            entries.append(
                {
                    "kind": "Texture2D",
                    "bundleFile": container_path.name,
                    "bundleRelPath": container_rel,
                    "pathId": int(obj.path_id),
                    "assetsFile": str(getattr(obj.assets_file, "name", "") or ""),
                    "error": str(exc),
                }
            )
            if entry_meta:
                entries[-1].update(entry_meta)

    return entries, stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export Texture2D images from Unity bundles (*.unity3d) and "
            "optional WebGL webdata files (WebGL_*.data)."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root path, e.g. /path/to/webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--asset-dir",
        default="StreamingAssets/WebGL/ljpx2_lt",
        help="Bundle directory relative to --project-root.",
    )
    parser.add_argument(
        "--webdata-dir",
        default="Build",
        help="Directory containing WebGL *.data files relative to --project-root.",
    )
    parser.add_argument(
        "--webdata-glob",
        default="WebGL_*.data",
        help="Glob for webdata files in --webdata-dir.",
    )
    parser.add_argument(
        "--webdata-extract-root",
        default="_extracted_webdata",
        help=(
            "Extraction cache root relative to --project-root. "
            "Each webdata file extracts to <root>/<data_stem>/"
        ),
    )
    parser.add_argument(
        "--skip-webdata",
        action="store_true",
        help="Skip exporting textures from WebGL_*.data payloads.",
    )
    parser.add_argument(
        "--refresh-webdata-extract",
        action="store_true",
        help="Force re-extract WebGL_*.data payloads before export.",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help=(
            "Output directory. Default: "
            "new layout => <project-root-parent>/sourceImages, "
            "legacy => <workspace>/sourceImages/<project-root-name>/"
        ),
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete output-root before export.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only export first N bundles for smoke test (0 means all).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    asset_dir = (project_root / args.asset_dir).resolve()
    webdata_dir = (project_root / args.webdata_dir).resolve()
    webdata_extract_root = (project_root / args.webdata_extract_root).resolve()

    if not asset_dir.is_dir():
        raise SystemExit(f"Asset dir not found: {asset_dir}")

    if args.output_root:
        output_root = Path(args.output_root).resolve()
    else:
        output_root = _default_output_root(project_root)

    if args.clean and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    bundles = _iter_bundles(asset_dir)
    if args.limit > 0:
        bundles = bundles[: args.limit]
    if not bundles:
        raise SystemExit(f"No .unity3d files found in: {asset_dir}")

    webdata_files: List[Path] = []
    if not args.skip_webdata:
        webdata_files = _iter_webdata_files(webdata_dir, args.webdata_glob)

    print(f"[export] project_root: {project_root}")
    print(f"[export] asset_dir   : {asset_dir}")
    print(f"[export] webdata_dir : {webdata_dir}")
    print(f"[export] output_root : {output_root}")
    print(f"[export] bundle_count: {len(bundles)}")
    print(f"[export] webdata_cnt : {len(webdata_files)}")

    manifest = {
        "schema": "u3d-source-images-v2",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "assetDir": str(asset_dir),
        "webDataDir": str(webdata_dir),
        "webDataGlob": str(args.webdata_glob),
        "webDataExtractRoot": str(webdata_extract_root),
        "outputRoot": str(output_root),
        "imageDir": "images",
        "mappingFile": "image_mapping.json",
        "bundleStats": [],
        "webDataStats": [],
        "summary": {},
    }
    mapping = {
        "schema": "u3d-image-mapping-v1",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "assetDir": str(asset_dir),
        "outputRoot": str(output_root),
        "imageDir": "images",
        "entries": [],
    }

    total_exported = 0
    total_failed = 0
    total_texture_objects = 0
    total_webdata_exported = 0
    total_webdata_failed = 0
    total_webdata_texture_objects = 0
    used_export_paths: Set[str] = set()

    for idx, bundle in enumerate(bundles, start=1):
        bundle_rel = bundle.relative_to(project_root).as_posix()
        entries, stats = _export_container(
            bundle,
            bundle_rel,
            bundle.name,
            output_root,
            used_export_paths,
            entry_meta={"sourceType": "bundle"},
            stats_meta={"sourceType": "bundle"},
        )
        mapping["entries"].extend(entries)
        manifest["bundleStats"].append(stats)
        total_exported += stats["exportedTextures"]
        total_failed += stats["failedTextures"]
        total_texture_objects += stats["textureObjects"]

        if idx % 20 == 0 or idx == len(bundles):
            print(
                f"[export] bundles {idx}/{len(bundles)} | "
                f"textures exported={total_exported} failed={total_failed}"
            )

    for idx, webdata_path in enumerate(webdata_files, start=1):
        data_rel = webdata_path.relative_to(project_root).as_posix()
        extract_dir = webdata_extract_root / webdata_path.stem
        data_bundle_path = extract_dir / "data.unity3d"

        extracted_count = 0
        extract_error = ""
        try:
            if args.refresh_webdata_extract and extract_dir.exists():
                shutil.rmtree(extract_dir)
            if not data_bundle_path.is_file():
                extracted_count = _extract_unity_webdata(webdata_path, extract_dir)
        except Exception as exc:  # noqa: BLE001
            extract_error = str(exc)

        if extract_error:
            manifest["webDataStats"].append(
                {
                    "sourceType": "webdata",
                    "webDataRelPath": data_rel,
                    "webDataFile": webdata_path.name,
                    "extractDir": str(extract_dir),
                    "extractedFileCount": extracted_count,
                    "error": extract_error,
                }
            )
            print(
                f"[export] webdata {idx}/{len(webdata_files)} failed: "
                f"{webdata_path.name} ({extract_error})"
            )
            continue

        if not data_bundle_path.is_file():
            manifest["webDataStats"].append(
                {
                    "sourceType": "webdata",
                    "webDataRelPath": data_rel,
                    "webDataFile": webdata_path.name,
                    "extractDir": str(extract_dir),
                    "extractedFileCount": extracted_count,
                    "error": "data.unity3d not found after extraction",
                }
            )
            print(
                f"[export] webdata {idx}/{len(webdata_files)} skipped: "
                f"{webdata_path.name} (data.unity3d missing)"
            )
            continue

        extracted_rel = data_bundle_path.relative_to(project_root).as_posix()
        entries, stats = _export_container(
            data_bundle_path,
            extracted_rel,
            webdata_path.name,
            output_root,
            used_export_paths,
            entry_meta={
                "sourceType": "webdata",
                "webDataRelPath": data_rel,
                "webDataExtractRelPath": extract_dir.relative_to(project_root).as_posix(),
                "webDataEntryPath": "data.unity3d",
            },
            stats_meta={
                "sourceType": "webdata",
                "webDataRelPath": data_rel,
                "webDataFile": webdata_path.name,
                "extractDir": str(extract_dir),
                "extractedFileCount": extracted_count,
            },
        )
        mapping["entries"].extend(entries)
        manifest["webDataStats"].append(stats)
        total_webdata_exported += stats["exportedTextures"]
        total_webdata_failed += stats["failedTextures"]
        total_webdata_texture_objects += stats["textureObjects"]
        print(
            f"[export] webdata {idx}/{len(webdata_files)} | "
            f"{webdata_path.name} textures exported={stats['exportedTextures']} "
            f"failed={stats['failedTextures']}"
        )

    manifest["summary"] = {
        "bundleCount": len(bundles),
        "textureObjects": total_texture_objects,
        "exportedTextures": total_exported,
        "failedTextures": total_failed,
        "webDataFileCount": len(webdata_files),
        "webDataTextureObjects": total_webdata_texture_objects,
        "webDataExportedTextures": total_webdata_exported,
        "webDataFailedTextures": total_webdata_failed,
        "allTextureObjects": total_texture_objects + total_webdata_texture_objects,
        "allExportedTextures": total_exported + total_webdata_exported,
        "allFailedTextures": total_failed + total_webdata_failed,
        "totalEntries": len(mapping["entries"]),
    }

    mapping_path = output_root / "image_mapping.json"
    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    manifest_path = output_root / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[export] mapping    : {mapping_path}")
    print(f"[export] manifest   : {manifest_path}")
    print(
        f"[export] done       : exported={manifest['summary']['allExportedTextures']}, "
        f"failed={manifest['summary']['allFailedTextures']}, "
        f"texture_objects={manifest['summary']['allTextureObjects']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
