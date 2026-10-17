#!/usr/bin/env python3
"""Scan/prefetch Cocos Creator 2.x assets from config.*.json."""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
import urllib.request

BASE64_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
BASE64_VALUES = [64] * 123
for i in range(64):
    BASE64_VALUES[ord(BASE64_KEYS[i])] = i

HEX = list("0123456789abcdef")
UUID_TEMPLATE = [""] * 8 + ["-"] + [""] * 4 + ["-"] + [""] * 4 + ["-"] + [""] * 4 + ["-"] + [""] * 12
UUID_CHAR_INDEX = [i for i, v in enumerate(UUID_TEMPLATE) if v != "-"]

IMPORT_EXT_CANDIDATES = [".json", ".cconb"]
NATIVE_EXT_CANDIDATES = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp3",
    ".m4a",
    ".ogg",
    ".wav",
    ".mp4",
    ".bin",
    ".json",
    ".txt",
    ".ttf",
    ".pem",
    ".atlas",
    ".plist",
]


@dataclass
class ImportEntry:
    bundle: str
    rel_no_ext: str
    existing_rel: Optional[str]


@dataclass
class NativeEntry:
    bundle: str
    rel_no_ext: str
    existing_rel: Optional[str]


def _arg() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scan/prefetch Cocos assets from config.*.json",
        epilog="Exit codes: 0 = complete, 1 = missing assets/download failures, 2 = invalid inputs/config scan.",
    )
    p.add_argument(
        "bundles",
        nargs="*",
        help="Optional bundle names. Empty means all bundles under assets/.",
    )
    p.add_argument(
        "--project",
        required=True,
        help="Web project root path that contains assets/.",
    )
    p.add_argument(
        "--base-url",
        default="",
        help="Default remote base URL; otherwise every selected bundle needs --bundle-url.",
    )
    p.add_argument(
        "--bundle-url",
        action="append",
        default=[],
        metavar="BUNDLE=URL",
        help=(
            "Override the remote root for one bundle. Repeatable. The URL must "
            "point at the bundle directory that contains import/ and native/."
        ),
    )
    p.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan local missing files; do not download.",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Download worker count for prefetch mode.",
    )
    p.add_argument(
        "--report",
        default="",
        help="Optional JSON report path. Relative path is resolved from current working directory.",
    )
    return p.parse_args()


def decode_uuid(compact: str) -> str:
    if len(compact) != 22:
        return compact
    out = UUID_TEMPLATE[:]
    out[0], out[1] = compact[0], compact[1]
    r = 2
    for i in range(2, 22, 2):
        a = BASE64_VALUES[ord(compact[i])]
        c = BASE64_VALUES[ord(compact[i + 1])]
        out[UUID_CHAR_INDEX[r]] = HEX[a >> 2]
        r += 1
        out[UUID_CHAR_INDEX[r]] = HEX[((a & 3) << 2) | (c >> 4)]
        r += 1
        out[UUID_CHAR_INDEX[r]] = HEX[c & 15]
        r += 1
    return "".join(out)


def normalize_base_url(base_url: str) -> str:
    if not base_url:
        return ""
    return base_url if base_url.endswith("/") else base_url + "/"


def parse_bundle_urls(values: List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for value in values:
        bundle, separator, url = value.partition("=")
        bundle = bundle.strip()
        url = url.strip()
        if not separator or not bundle or not url:
            raise SystemExit(f"invalid --bundle-url value: {value!r}; expected BUNDLE=URL")
        result[bundle] = normalize_base_url(url)
    return result


def remote_asset_url(rel: str, bundle: str, base_url: str, bundle_urls: Dict[str, str]) -> str:
    bundle_url = bundle_urls.get(bundle)
    if not bundle_url:
        if not base_url:
            raise ValueError(f"no remote URL configured for bundle: {bundle}")
        return base_url + rel
    prefix = f"assets/{bundle}/"
    if not rel.startswith(prefix):
        raise ValueError(f"asset path does not belong to bundle {bundle}: {rel}")
    return bundle_url + rel[len(prefix):]


def safe_download(url: str, out_path: str, timeout: int = 20) -> Tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                return False, f"http-{status}"
            data = resp.read()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(data)
        return True, "ok"
    except HTTPError as e:
        return False, f"http-{e.code}"
    except URLError as e:
        return False, f"url-{e.reason}"
    except TimeoutError:
        return False, "timeout"
    except Exception as e:  # pylint: disable=broad-except
        return False, f"error-{type(e).__name__}"


def resolve_uuid(raw_key, uuids: List[str]) -> str:
    try:
        idx = int(raw_key)
        compact = uuids[idx]
    except Exception:  # pylint: disable=broad-except
        compact = str(raw_key)
    return decode_uuid(compact)


def iter_config_files(assets_dir: str, selected_bundles: Optional[set]) -> Iterable[Tuple[str, str]]:
    if not os.path.isdir(assets_dir):
        return []
    pairs: List[Tuple[str, str]] = []
    for bundle in sorted(os.listdir(assets_dir)):
        if selected_bundles and bundle not in selected_bundles:
            continue
        bundle_dir = os.path.join(assets_dir, bundle)
        if not os.path.isdir(bundle_dir):
            continue
        for name in sorted(os.listdir(bundle_dir)):
            if name.startswith("config.") and name.endswith(".json"):
                pairs.append((bundle, os.path.join(bundle_dir, name)))
                break
    return pairs


def resolve_existing(rel_no_ext: str, candidates: List[str], project_root: str) -> Optional[str]:
    for ext in candidates:
        rel = rel_no_ext + ext
        if os.path.isfile(os.path.join(project_root, rel)):
            return rel
    return None


def enumerate_entries(project_root: str, selected_bundles: Optional[set]) -> Tuple[List[ImportEntry], List[NativeEntry]]:
    assets_dir = os.path.join(project_root, "assets")
    import_entries: List[ImportEntry] = []
    native_entries: List[NativeEntry] = []

    for bundle, cfg_path in iter_config_files(assets_dir, selected_bundles):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        uuids = cfg.get("uuids", [])
        packs = cfg.get("packs", {})
        packed_uuid_indices = {
            int(uuid_index)
            for uuid_indices in packs.values()
            for uuid_index in uuid_indices
            if isinstance(uuid_index, int) or str(uuid_index).isdigit()
        }
        versions = cfg.get("versions", {})
        import_versions = versions.get("import", [])
        native_versions = versions.get("native", [])

        for i in range(0, len(import_versions), 2):
            if i + 1 >= len(import_versions):
                continue
            key = import_versions[i]
            ver = import_versions[i + 1]
            if (isinstance(key, int) or str(key).isdigit()) and int(key) in packed_uuid_indices:
                # Cocos loads this UUID from its pack file. Some builds leave a
                # stale per-UUID version entry even though no standalone file
                # is published, so scanning both produces false 404s.
                continue
            if key in packs:
                file_id = str(key)
            else:
                file_id = resolve_uuid(key, uuids)
            rel_no_ext = f"assets/{bundle}/import/{file_id[:2]}/{file_id}.{ver}"
            existing_rel = resolve_existing(rel_no_ext, IMPORT_EXT_CANDIDATES, project_root)
            import_entries.append(ImportEntry(bundle=bundle, rel_no_ext=rel_no_ext, existing_rel=existing_rel))

        for i in range(0, len(native_versions), 2):
            if i + 1 >= len(native_versions):
                continue
            key = native_versions[i]
            ver = native_versions[i + 1]
            uuid = resolve_uuid(key, uuids)
            rel_no_ext = f"assets/{bundle}/native/{uuid[:2]}/{uuid}.{ver}"
            existing_rel = resolve_existing(rel_no_ext, NATIVE_EXT_CANDIDATES, project_root)
            native_entries.append(NativeEntry(bundle=bundle, rel_no_ext=rel_no_ext, existing_rel=existing_rel))

    return import_entries, native_entries


def fetch_import(
    entry: ImportEntry,
    base_url: str,
    bundle_urls: Dict[str, str],
    project_root: str,
) -> Tuple[str, str, str]:
    for ext in IMPORT_EXT_CANDIDATES:
        rel = entry.rel_no_ext + ext
        url = remote_asset_url(rel, entry.bundle, base_url, bundle_urls)
        ok, reason = safe_download(url, os.path.join(project_root, rel))
        if ok:
            return "downloaded", rel, "ok"
    return "remote_missing", entry.rel_no_ext + "<import-ext>", "all-candidates-failed"


def fetch_native(
    entry: NativeEntry,
    base_url: str,
    bundle_urls: Dict[str, str],
    project_root: str,
) -> Tuple[str, str, str]:
    for ext in NATIVE_EXT_CANDIDATES:
        rel = entry.rel_no_ext + ext
        url = remote_asset_url(rel, entry.bundle, base_url, bundle_urls)
        ok, reason = safe_download(url, os.path.join(project_root, rel))
        if ok:
            return "downloaded", rel, "ok"
    return "remote_missing", entry.rel_no_ext + "<native-ext>", "all-candidates-failed"


def collect_missing_entries(
    import_entries: List[ImportEntry],
    native_entries: List[NativeEntry],
    project_root: str,
) -> List[str]:
    """Recheck the filesystem, including files downloaded during this run."""
    missing: List[str] = []
    for entries, extensions, label in (
        (import_entries, IMPORT_EXT_CANDIDATES, "<import-ext>"),
        (native_entries, NATIVE_EXT_CANDIDATES, "<native-ext>"),
    ):
        for item in entries:
            if not resolve_existing(item.rel_no_ext, extensions, project_root):
                missing.append(item.rel_no_ext + label)
    return missing


def main() -> int:
    args = _arg()
    project_root = os.path.abspath(args.project)
    assets_dir = os.path.join(project_root, "assets")
    base_url = normalize_base_url(args.base_url)
    bundle_urls: Dict[str, str] = {}
    selected_bundles = set(args.bundles) if args.bundles else None
    errors: List[Dict[str, str]] = []
    try:
        bundle_urls = parse_bundle_urls(args.bundle_url)
    except SystemExit as exc:
        errors.append({"rel": "<arguments>", "reason": str(exc)})

    config_files = list(iter_config_files(assets_dir, selected_bundles))
    configured_bundles = {bundle for bundle, _ in config_files}
    if not os.path.isdir(assets_dir):
        errors.append({"rel": assets_dir, "reason": "assets directory not found"})
    elif not config_files:
        errors.append({"rel": assets_dir, "reason": "no matching config.*.json files; scan is not valid"})
    if selected_bundles:
        for bundle in sorted(selected_bundles - configured_bundles):
            errors.append({"rel": f"assets/{bundle}", "reason": "selected bundle has no config.*.json file"})

    import_entries: List[ImportEntry] = []
    native_entries: List[NativeEntry] = []
    if config_files:
        try:
            import_entries, native_entries = enumerate_entries(project_root, selected_bundles)
        except Exception as exc:  # pylint: disable=broad-except
            errors.append({"rel": "<configs>", "reason": f"failed to scan configs: {type(exc).__name__}: {exc}"})
        else:
            if not import_entries and not native_entries:
                errors.append({"rel": "<configs>", "reason": "configs produced zero resource entries; scan is not valid"})

    if not args.scan_only and not base_url:
        for bundle in sorted(configured_bundles - set(bundle_urls)):
            errors.append({"rel": f"assets/{bundle}", "reason": "no remote URL; set --base-url or --bundle-url for this bundle"})

    initial_missing_local = collect_missing_entries(import_entries, native_entries, project_root)
    configuration_failed = bool(errors)

    downloaded: List[str] = []
    remote_missing: List[str] = []

    if not args.scan_only and not configuration_failed:
        futures = []
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for item in import_entries:
                if not item.existing_rel:
                    futures.append(pool.submit(fetch_import, item, base_url, bundle_urls, project_root))
            for item in native_entries:
                if not item.existing_rel:
                    futures.append(pool.submit(fetch_native, item, base_url, bundle_urls, project_root))

            for future in futures:
                try:
                    status, rel, reason = future.result()
                except Exception as e:  # pylint: disable=broad-except
                    errors.append({"rel": "<unknown>", "reason": str(e)})
                    continue

                if status == "downloaded":
                    downloaded.append(rel)
                    print(f"downloaded: {rel}")
                elif status == "remote_missing":
                    remote_missing.append(rel)
                    print(f"missing-remote: {rel}")
                else:
                    errors.append({"rel": rel, "reason": reason})

    missing_local = collect_missing_entries(import_entries, native_entries, project_root)
    scanned_count = len(import_entries) + len(native_entries)
    exit_code = 2 if configuration_failed else (1 if missing_local or remote_missing or errors else 0)
    status = "error" if configuration_failed else ("incomplete" if exit_code else "ok")
    report = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "project_root": project_root,
        "base_url": base_url,
        "bundle_urls": bundle_urls,
        "selected_bundles": sorted(list(selected_bundles)) if selected_bundles else [],
        "scan_only": bool(args.scan_only),
        "status": status,
        "exit_code": exit_code,
        "config_count": len(config_files),
        "config_files": [os.path.relpath(path, project_root).replace(os.sep, "/") for _, path in config_files],
        "scanned": scanned_count,
        "initial_existing_local": scanned_count - len(initial_missing_local),
        "initial_missing_local": len(initial_missing_local),
        "initial_missing_local_entries": initial_missing_local,
        "existing_local": scanned_count - len(missing_local),
        "missing_local": len(missing_local),
        "downloaded": len(downloaded),
        "remote_missing": len(remote_missing),
        "errors": len(errors),
        "missing_local_entries": missing_local,
        "downloaded_entries": downloaded,
        "remote_missing_entries": remote_missing,
        "error_entries": errors,
    }

    print("\n=== summary ===")
    print(f"scanned        : {report['scanned']}")
    print(f"existing_local : {report['existing_local']}")
    print(f"missing_local  : {report['missing_local']}")
    print(f"downloaded     : {report['downloaded']}")
    print(f"remote_missing : {report['remote_missing']}")
    print(f"errors         : {report['errors']}")
    print(f"status         : {status}")
    print(f"exit_code      : {exit_code}")
    for error in errors:
        print(f"error: {error['rel']}: {error['reason']}")

    if args.report:
        report_path = args.report
        if not os.path.isabs(report_path):
            report_path = os.path.abspath(report_path)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"report written : {report_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
