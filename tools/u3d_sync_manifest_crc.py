#!/usr/bin/env python3
"""CLI to sync CRC fields in PackageManifest_*.bytes against local bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from u3d_manifest_crc import auto_detect_package_manifest, sync_manifest_bundle_crc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sync PackageManifest bundle CRC values. "
            "Calculated CRC is based on bundle uncompressed file payload."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root path, e.g. webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--package-manifest",
        default="",
        help="Optional explicit PackageManifest_*.bytes path.",
    )
    parser.add_argument(
        "--bundle-hash",
        action="append",
        default=[],
        help="Optional bundle hash to sync. Can be specified multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only check and report differences, do not write manifest.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a manifest backup before writing.",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Optional JSON report output path.",
    )
    return parser.parse_args()


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path)


def main() -> int:
    args = parse_args()
    cwd = Path.cwd()
    project_root = _resolve(cwd, args.project_root).resolve()
    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")

    if args.package_manifest:
        manifest_path = _resolve(cwd, args.package_manifest).resolve()
    else:
        manifest_path = auto_detect_package_manifest(project_root)
    if not manifest_path or not manifest_path.is_file():
        raise SystemExit("PackageManifest not found. Use --package-manifest.")

    bundle_hashes = {h.lower() for h in args.bundle_hash if h}
    result = sync_manifest_bundle_crc(
        manifest_path,
        asset_dir=manifest_path.parent,
        bundle_hashes=bundle_hashes or None,
        dry_run=bool(args.dry_run),
        backup=not args.no_backup,
    )

    if args.report:
        report_path = _resolve(cwd, args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[crc-sync] report         : {report_path}")

    print(f"[crc-sync] manifest       : {manifest_path}")
    print(f"[crc-sync] bundle rows    : {result['bundleRowCount']}")
    print(f"[crc-sync] checked        : {result['checkedBundleCount']}")
    print(f"[crc-sync] updated        : {result['updatedBundleCount']}")
    print(f"[crc-sync] missing        : {result['missingBundleCount']}")
    print(f"[crc-sync] errors         : {result['errorCount']}")
    if result["backupPath"]:
        print(f"[crc-sync] backup         : {result['backupPath']}")
    if result["updates"]:
        first = result["updates"][0]
        print(
            "[crc-sync] sample         : "
            f"{first['bundleHash']} {first['oldCrcHex']} -> {first['newCrcHex']}"
        )

    return 2 if result["errorCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
