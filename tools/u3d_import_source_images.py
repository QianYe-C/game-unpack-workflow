#!/usr/bin/env python3
"""Import edited Texture2D PNGs back into Unity .unity3d bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import UnityPy
from PIL import Image
from u3d_manifest_crc import (
    auto_detect_package_manifest,
    extract_bundle_hashes,
    sync_manifest_bundle_crc,
)
from unity_webdata_extract import extract as extract_webdata
from unity_webdata_pack import pack as pack_webdata


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import edited textures according to sourceImages mapping."
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root path, e.g. /path/to/webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="sourceImages project directory, contains image_mapping.json and images/.",
    )
    parser.add_argument(
        "--mapping",
        default="image_mapping.json",
        help="Mapping file path relative to --source-root or absolute path.",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Optional report output path. Default: import_report(.json) under source-root.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Compatibility flag, currently no-op.",
    )
    parser.add_argument(
        "--manifest",
        default="",
        help="Optional fallback manifest path (legacy compatibility).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only check modified images, do not write bundles.",
    )
    parser.add_argument(
        "--allow-size-mismatch",
        action="store_true",
        help="Allow import even if image size differs from original metadata.",
    )
    parser.add_argument(
        "--backup-dir",
        default="",
        help=(
            "Backup dir for original bundles. Default: "
            "<source-root>/_bundle_backups/<timestamp>/"
        ),
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help=(
            "Optional PackageManifest_*.bytes path for CRC sync. "
            "If omitted, auto-detect under --project-root."
        ),
    )
    parser.add_argument(
        "--skip-manifest-crc-sync",
        action="store_true",
        help="Skip syncing CRC fields in PackageManifest after bundle write.",
    )
    parser.add_argument(
        "--prefer-suffix",
        default="",
        help=(
            "Prefer sibling variant image with this suffix before extension, e.g. "
            "'_nano' to use foo_nano.png over foo.png when present."
        ),
    )
    return parser.parse_args()


def _resolve_path(source_root: Path, path_arg: str) -> Path:
    m = Path(path_arg)
    if m.is_absolute():
        return m
    return source_root / m


def _prefer_variant(path: Path, suffix: str) -> Path:
    if not suffix:
        return path
    alt = path.with_name(f"{path.stem}{suffix}{path.suffix}")
    return alt if alt.is_file() else path


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_entries_from_doc(doc: Dict) -> List[Dict]:
    schema = doc.get("schema")
    if schema in ("u3d-image-mapping-v1", "u3d-source-images-v1"):
        entries = doc.get("entries", [])
        return [
            e
            for e in entries
            if e.get("kind") == "Texture2D"
            and "exportPath" in e
            and "bundleRelPath" in e
        ]
    raise SystemExit(f"Unsupported mapping schema: {schema}")


def _resolve_report_path(source_root: Path, report_arg: str, dry_run: bool) -> Path:
    if report_arg:
        p = Path(report_arg)
        path = p if p.is_absolute() else (source_root / p)
        return path.resolve()
    return source_root / ("import_report_dry_run.json" if dry_run else "import_report.json")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root).resolve()
    mapping_path = _resolve_path(source_root, args.mapping).resolve()
    manifest_path = _resolve_path(source_root, args.manifest).resolve() if args.manifest else None

    if not source_root.is_dir():
        raise SystemExit(f"source-root not found: {source_root}")

    entries: List[Dict] = []
    loaded_from = ""
    if mapping_path.is_file():
        mapping_doc = _load_json(mapping_path)
        entries = _load_entries_from_doc(mapping_doc)
        loaded_from = str(mapping_path)
    elif manifest_path and manifest_path.is_file():
        manifest_doc = _load_json(manifest_path)
        schema = manifest_doc.get("schema")
        if schema == "u3d-source-images-v2":
            mapped = manifest_doc.get("mappingFile", "image_mapping.json")
            mapped_path = _resolve_path(source_root, mapped).resolve()
            if not mapped_path.is_file():
                raise SystemExit(f"mapping not found: {mapped_path}")
            mapping_doc = _load_json(mapped_path)
            entries = _load_entries_from_doc(mapping_doc)
            loaded_from = str(mapped_path)
            mapping_path = mapped_path
        else:
            entries = _load_entries_from_doc(manifest_doc)
            loaded_from = str(manifest_path)
    else:
        raise SystemExit(
            "No mapping file found. Expected image_mapping.json in source-root "
            "or provide --manifest for legacy format."
        )

    if not entries:
        raise SystemExit("No valid Texture2D entries found in mapping.")

    print(f"[import] project_root : {project_root}")
    print(f"[import] source_root  : {source_root}")
    print(f"[import] mapping      : {loaded_from}")
    print(f"[import] prefer_suffix: {args.prefer_suffix or '<none>'}")
    print(f"[import] entry_count  : {len(entries)}")

    grouped: Dict[str, List[Dict]] = defaultdict(list)
    unchanged = 0
    missing = 0
    invalid_size = 0
    changed_slice_images = 0
    entries_with_slice_changes = 0

    for entry in entries:
        entry = dict(entry)
        export_path = source_root / entry["exportPath"]
        resolved_export_path = _prefer_variant(export_path, args.prefer_suffix)
        entry["resolvedExportPath"] = str(resolved_export_path.relative_to(source_root))
        slice_defs = entry.get("spriteAtlasSlices")
        has_slices = isinstance(slice_defs, list) and bool(slice_defs)
        base_exists = resolved_export_path.is_file()
        if not base_exists and not has_slices:
            missing += 1

        base_changed = False
        if base_exists:
            current_sha = _sha256_file(resolved_export_path)
            if current_sha != entry.get("sha256"):
                with Image.open(resolved_export_path) as im:
                    width, height = im.size
                expected = (int(entry.get("width", 0)), int(entry.get("height", 0)))
                actual = (int(width), int(height))
                if actual != expected and not args.allow_size_mismatch:
                    invalid_size += 1
                    continue
                entry["newSha256"] = current_sha
                entry["newWidth"] = actual[0]
                entry["newHeight"] = actual[1]
                base_changed = True

        slice_changes: List[Dict] = []
        slice_invalid = False
        atlas_base_image = None
        atlas_width = 0
        atlas_height = 0
        if base_exists and isinstance(slice_defs, list) and slice_defs:
            with Image.open(resolved_export_path) as atlas_im:
                atlas_base_image = atlas_im.convert("RGBA")
            atlas_width, atlas_height = atlas_base_image.size
        if isinstance(slice_defs, list):
            for slice_entry in slice_defs:
                if not isinstance(slice_entry, dict):
                    continue
                slice_rel = slice_entry.get("exportPath")
                if not isinstance(slice_rel, str) or not slice_rel:
                    continue
                slice_path = source_root / slice_rel
                resolved_slice_path = _prefer_variant(slice_path, args.prefer_suffix)
                if not resolved_slice_path.is_file():
                    missing += 1
                    continue

                slice_sha = _sha256_file(resolved_slice_path)

                with Image.open(resolved_slice_path) as sim:
                    sw, sh = sim.size
                expected = (
                    int(slice_entry.get("width", 0)),
                    int(slice_entry.get("height", 0)),
                )
                actual = (int(sw), int(sh))
                if actual != expected and not args.allow_size_mismatch:
                    invalid_size += 1
                    slice_invalid = True
                    continue

                updated_slice = dict(slice_entry)
                updated_slice["newSha256"] = slice_sha
                updated_slice["newWidth"] = actual[0]
                updated_slice["newHeight"] = actual[1]
                changed_by_sha = slice_sha != slice_entry.get("sha256")
                changed_by_region = False
                if atlas_base_image is not None:
                    try:
                        x = int(round(float(slice_entry.get("x", 0))))
                        y = int(round(float(slice_entry.get("y", 0))))
                    except Exception:  # noqa: BLE001
                        invalid_size += 1
                        slice_invalid = True
                        continue
                    top = atlas_height - y - actual[1]
                    if x < 0 or top < 0 or x + actual[0] > atlas_width or top + actual[1] > atlas_height:
                        invalid_size += 1
                        slice_invalid = True
                        continue
                    region = atlas_base_image.crop((x, top, x + actual[0], top + actual[1]))
                    with Image.open(resolved_slice_path) as sim:
                        patch = sim.convert("RGBA")
                    changed_by_region = region.tobytes() != patch.tobytes()

                if changed_by_sha or changed_by_region:
                    slice_changes.append(updated_slice)

        if slice_invalid:
            continue
        if not base_changed and not slice_changes:
            unchanged += 1
            continue

        if slice_changes:
            changed_slice_images += len(slice_changes)
            entries_with_slice_changes += 1

        entry["baseChanged"] = base_changed
        entry["sliceChanges"] = slice_changes
        grouped[entry["bundleRelPath"]].append(entry)

    changed = sum(len(v) for v in grouped.values())
    print(
        "[import] changed_textures="
        f"{changed}, changed_slices={changed_slice_images}, "
        f"unchanged={unchanged}, missing_files={missing}, invalid_size={invalid_size}"
    )

    if changed == 0:
        print("[import] no modified textures detected, nothing to write.")
        return 0 if invalid_size == 0 else 2

    backup_dir = (
        Path(args.backup_dir).resolve()
        if args.backup_dir
        else source_root / "_bundle_backups" / datetime.now().strftime("%Y%m%d-%H%M%S")
    )

    report = {
        "schema": "u3d-import-report-v1",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "sourceRoot": str(source_root),
        "mapping": str(mapping_path),
        "preferSuffix": args.prefer_suffix,
        "dryRun": bool(args.dry_run),
        "allowSizeMismatch": bool(args.allow_size_mismatch),
        "summary": {
            "entryCount": len(entries),
            "changedTextures": changed,
            "changedSliceImages": changed_slice_images,
            "entriesWithSliceChanges": entries_with_slice_changes,
            "unchangedTextures": unchanged,
            "missingFiles": missing,
            "invalidSize": invalid_size,
            "modifiedBundles": len(grouped),
            "modifiedWebDataFiles": 0,
        },
        "bundles": [],
        "errors": [],
        "webDataPacks": [],
        "manifestCrcSync": None,
    }

    if args.dry_run:
        for rel, mods in sorted(grouped.items()):
            report["bundles"].append(
                {
                    "bundleRelPath": rel,
                    "modifiedTextures": len(mods),
                    "written": False,
                }
            )
        report_path = _resolve_report_path(source_root, args.report, dry_run=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[import] dry-run report: {report_path}")
        return 0 if invalid_size == 0 else 2

    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"[import] backup_dir   : {backup_dir}")
    modified_bundle_hashes = set()
    modified_webdata_targets: Dict[str, str] = {}

    for bundle_rel, mods in sorted(grouped.items()):
        source_type = str(mods[0].get("sourceType") or "bundle")
        webdata_rel = str(mods[0].get("webDataRelPath") or "")
        extract_rel = str(mods[0].get("webDataExtractRelPath") or "")
        if not extract_rel:
            extract_rel = str(Path(bundle_rel).parent.as_posix())

        bundle_path = project_root / bundle_rel
        bundle_item = {
            "sourceType": source_type,
            "bundleRelPath": bundle_rel,
            "bundlePath": str(bundle_path),
            "modifiedTextures": len(mods),
            "written": False,
            "updatedPathIds": [],
            "updatedSpriteSlices": 0,
        }
        if source_type == "webdata":
            bundle_item["webDataRelPath"] = webdata_rel
            bundle_item["webDataExtractRelPath"] = extract_rel

        if not bundle_path.is_file():
            if source_type == "webdata" and webdata_rel:
                webdata_path = project_root / webdata_rel
                extract_dir = project_root / extract_rel
                if webdata_path.is_file():
                    try:
                        extract_dir.mkdir(parents=True, exist_ok=True)
                        extract_webdata(webdata_path, extract_dir)
                    except Exception as exc:  # noqa: BLE001
                        report["errors"].append(
                            f"Failed to extract webdata for import: {webdata_path} ({exc})"
                        )
            report["errors"].append(f"Bundle not found: {bundle_path}")
            report["bundles"].append(bundle_item)
            continue

        backup_path = backup_dir / bundle_rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundle_path, backup_path)

        env = UnityPy.load(str(bundle_path))
        tex_map = defaultdict(list)
        tex_map_by_assets = {}
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            pid = int(obj.path_id)
            assets_name = str(getattr(obj.assets_file, "name", "") or "")
            tex_map[pid].append(obj)
            tex_map_by_assets[(pid, assets_name)] = obj

        for entry in mods:
            path_id = int(entry["pathId"])
            assets_name = str(entry.get("assetsFile") or "")
            obj = None
            if assets_name:
                obj = tex_map_by_assets.get((path_id, assets_name))
            if obj is None:
                candidates = tex_map.get(path_id, [])
                if len(candidates) == 1:
                    obj = candidates[0]
                elif len(candidates) > 1:
                    candidate_names = sorted(
                        str(getattr(c.assets_file, "name", "") or "")
                        for c in candidates
                    )
                    report["errors"].append(
                        "Texture pathId is ambiguous, set assetsFile in mapping: "
                        f"{bundle_rel}#{path_id} candidates={candidate_names}"
                    )
                    continue
            if obj is None:
                report["errors"].append(
                    "Texture pathId not found: "
                    f"{bundle_rel}#{path_id} assetsFile={assets_name or '<any>'}"
                )
                continue

            texture = obj.read()
            image_path = source_root / entry["exportPath"]
            resolved_image_path = _prefer_variant(image_path, args.prefer_suffix)
            replacement = None

            slice_changes = entry.get("sliceChanges")
            if isinstance(slice_changes, list) and slice_changes:
                all_slices = entry.get("spriteAtlasSlices")
                if not isinstance(all_slices, list):
                    all_slices = slice_changes

                # Always rebuild atlas from current source files to avoid using
                # stale merged images.
                if resolved_image_path.is_file():
                    with Image.open(resolved_image_path) as im:
                        replacement = im.convert("RGBA")
                else:
                    base_image = texture.image
                    if base_image is None:
                        report["errors"].append(
                            f"Texture image is None for sprite merge: {bundle_rel}#{path_id}"
                        )
                        continue
                    replacement = base_image.convert("RGBA")

                atlas_w, atlas_h = replacement.size
                applied = 0
                for slice_entry in all_slices:
                    if not isinstance(slice_entry, dict):
                        continue
                    slice_rel = slice_entry.get("exportPath")
                    if not isinstance(slice_rel, str) or not slice_rel:
                        report["errors"].append(
                            f"Invalid slice exportPath for {bundle_rel}#{path_id}"
                        )
                        continue
                    slice_path = source_root / slice_rel
                    resolved_slice_path = _prefer_variant(slice_path, args.prefer_suffix)
                    if not resolved_slice_path.is_file():
                        report["errors"].append(f"Slice image missing: {resolved_slice_path}")
                        continue

                    with Image.open(resolved_slice_path) as sim:
                        patch = sim.convert("RGBA")
                    sw, sh = patch.size

                    try:
                        x = int(round(float(slice_entry.get("x", 0))))
                        y = int(round(float(slice_entry.get("y", 0))))
                    except Exception:  # noqa: BLE001
                        report["errors"].append(
                            f"Invalid slice coordinates for {slice_path}"
                        )
                        continue

                    top = atlas_h - y - sh
                    if x < 0 or top < 0 or x + sw > atlas_w or top + sh > atlas_h:
                        report["errors"].append(
                            "Slice out of atlas bounds: "
                            f"{resolved_slice_path} -> x={x}, y={y}, w={sw}, h={sh}, "
                            f"atlas={atlas_w}x{atlas_h}"
                        )
                        continue

                    replacement.paste(patch, (x, top))
                    applied += 1

                bundle_item["updatedSpriteSlices"] += applied

            if replacement is None and entry.get("baseChanged"):
                if not resolved_image_path.is_file():
                    report["errors"].append(f"Texture image missing: {resolved_image_path}")
                    continue
                with Image.open(resolved_image_path) as im:
                    replacement = im.copy()

            if replacement is None:
                # Should not happen because changed entries always carry at least
                # one modified source (base texture or sprite slices).
                continue

            texture.image = replacement
            texture.save()
            bundle_item["updatedPathIds"].append(path_id)

        bundle_bytes = env.file.save(packer="original")
        bundle_path.write_bytes(bundle_bytes)
        bundle_item["written"] = True
        report["bundles"].append(bundle_item)
        if source_type == "bundle":
            modified_bundle_hashes.update(extract_bundle_hashes([bundle_rel]))
        elif source_type == "webdata" and webdata_rel:
            modified_webdata_targets[webdata_rel] = extract_rel

        print(
            f"[import] wrote bundle: {bundle_rel} "
            f"(textures={len(bundle_item['updatedPathIds'])})"
        )

    if modified_webdata_targets:
        report["summary"]["modifiedWebDataFiles"] = len(modified_webdata_targets)
        for webdata_rel, extract_rel in sorted(modified_webdata_targets.items()):
            webdata_path = project_root / webdata_rel
            extract_dir = project_root / extract_rel
            pack_item = {
                "webDataRelPath": webdata_rel,
                "webDataPath": str(webdata_path),
                "extractDir": str(extract_dir),
                "written": False,
            }

            if not extract_dir.is_dir():
                report["errors"].append(
                    f"Webdata extract directory missing: {extract_dir}"
                )
                report["webDataPacks"].append(pack_item)
                continue

            if webdata_path.is_file():
                webdata_backup = backup_dir / webdata_rel
                webdata_backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(webdata_path, webdata_backup)
                pack_item["backupPath"] = str(webdata_backup)
            else:
                report["errors"].append(f"Webdata file not found: {webdata_path}")
                report["webDataPacks"].append(pack_item)
                continue

            try:
                packed_count = pack_webdata(extract_dir, webdata_path)
                pack_item["packedFileCount"] = int(packed_count)
                pack_item["written"] = True
                print(
                    f"[import] wrote webdata: {webdata_rel} "
                    f"(packed_files={packed_count})"
                )
            except Exception as exc:  # noqa: BLE001
                report["errors"].append(
                    f"Failed to repack webdata {webdata_rel}: {exc}"
                )
            report["webDataPacks"].append(pack_item)

    if args.skip_manifest_crc_sync:
        report["manifestCrcSync"] = {"skipped": True, "reason": "skip flag enabled"}
        print("[import] manifest crc sync: skipped (--skip-manifest-crc-sync)")
    elif modified_bundle_hashes:
        if args.package_manifest:
            manifest_sync_path = _resolve_path(source_root, args.package_manifest).resolve()
        else:
            manifest_sync_path = auto_detect_package_manifest(project_root)

        if manifest_sync_path and manifest_sync_path.is_file():
            try:
                sync_result = sync_manifest_bundle_crc(
                    manifest_sync_path,
                    asset_dir=manifest_sync_path.parent,
                    bundle_hashes=modified_bundle_hashes,
                    dry_run=False,
                    backup=True,
                )
                report["manifestCrcSync"] = sync_result
                print(
                    "[import] manifest crc sync: "
                    f"checked={sync_result['checkedBundleCount']}, "
                    f"updated={sync_result['updatedBundleCount']}, "
                    f"errors={sync_result['errorCount']}"
                )
                if sync_result.get("backupPath"):
                    print(f"[import] manifest backup: {sync_result['backupPath']}")
                if sync_result["errorCount"]:
                    report["errors"].append(
                        "Manifest CRC sync errors: "
                        f"{sync_result['errorCount']} (see manifestCrcSync.errors)"
                    )
            except Exception as exc:  # noqa: BLE001
                report["errors"].append(f"Manifest CRC sync failed: {exc}")
                report["manifestCrcSync"] = {"skipped": True, "reason": str(exc)}
        else:
            msg = (
                "PackageManifest not found for CRC sync. "
                "Use --package-manifest to specify explicitly."
            )
            report["errors"].append(msg)
            report["manifestCrcSync"] = {"skipped": True, "reason": msg}
            print(f"[import] manifest crc sync: {msg}")

    report_path = _resolve_report_path(source_root, args.report, dry_run=False)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[import] report      : {report_path}")
    if report["errors"]:
        print(f"[import] errors      : {len(report['errors'])}")
        return 2

    print("[import] done")
    return 0 if invalid_size == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
