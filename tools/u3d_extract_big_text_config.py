#!/usr/bin/env python3
"""Extract large multilingual text blocks from Unity WebGL .data."""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_ANCHORS = [
    "Categories/",
    "StoryCategories/",
    "Boosters/",
    "Elderly",
    "老人",
    "戴眼镜",
]

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_ /'\-]{2,}|[\u4e00-\u9fff]{2,}")
KEY_PREFIXES = ("Categories/", "StoryCategories/", "Boosters/")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolve(base: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def _auto_detect_data_file(project_root: Path) -> Path:
    build_dir = project_root / "Build"
    if not build_dir.is_dir():
        raise FileNotFoundError(f"Build directory not found: {build_dir}")
    candidates = sorted(build_dir.glob("*.data"))
    if not candidates:
        raise FileNotFoundError(f"No *.data found under: {build_dir}")
    candidates.sort(key=lambda p: (p.stat().st_size, p.stat().st_mtime), reverse=True)
    return candidates[0]


def _default_output_root(project_root: Path) -> Path:
    # New layout: myprojects/<project>/webprojects
    if project_root.name == "webprojects":
        return (project_root.parent / "sourceConfigs" / "bigTextConfig").resolve()
    # Legacy layout: webprojects/<project>
    return (project_root.parent.parent / "sourceConfigs" / project_root.name / "bigTextConfig").resolve()


def _iter_offsets(data: bytes, needle: bytes) -> Iterable[int]:
    pos = 0
    while True:
        pos = data.find(needle, pos)
        if pos < 0:
            return
        yield pos
        pos += 1


def _find_anchor_hits(data: bytes, anchors: List[str]) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {}
    for anchor in anchors:
        offsets = list(_iter_offsets(data, anchor.encode("utf-8")))
        result[anchor] = offsets
    return result


def _normalize_token(token: str) -> str:
    token = token.strip(" _-:/\\|\t\r\n")
    token = " ".join(token.split())
    return token


def _looks_hex_noise(token: str) -> bool:
    if len(token) < 16:
        return False
    return bool(re.fullmatch(r"[0-9a-f]+", token.lower()))


def _extract_tokens(text: str) -> List[str]:
    ordered = OrderedDict()
    for match in TOKEN_PATTERN.finditer(text):
        token = _normalize_token(match.group(0))
        if len(token) < 2 or len(token) > 120:
            continue
        if token.startswith("0-") or token.startswith("20-"):
            continue
        if _looks_hex_noise(token):
            continue
        # Keep only tokens with latin letters or CJK.
        has_latin = any("a" <= ch.lower() <= "z" for ch in token)
        has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in token)
        if not (has_latin or has_cjk):
            continue
        ordered[token] = None
    return list(ordered.keys())


def _build_key_pairs(tokens: List[str]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for i, token in enumerate(tokens):
        if not token.startswith(KEY_PREFIXES):
            continue
        english = ""
        chinese = ""
        for j in range(i + 1, min(i + 12, len(tokens))):
            cand = tokens[j]
            if not english and any("a" <= ch.lower() <= "z" for ch in cand):
                english = cand
            if not chinese and any("\u4e00" <= ch <= "\u9fff" for ch in cand):
                chinese = cand
            if english and chinese:
                break
        rows.append(
            {
                "key": token,
                "englishCandidate": english,
                "chineseCandidate": chinese,
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract multilingual big-text area from Build/*.data using keyword anchors."
        )
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root, e.g. webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--data-file",
        default="",
        help="Optional .data file path. Auto-detect from <project-root>/Build/*.data if omitted.",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help=(
            "Output root directory. Default: "
            "new layout => <project-root-parent>/sourceConfigs/bigTextConfig, "
            "legacy => <workspace>/sourceConfigs/<project-name>/bigTextConfig"
        ),
    )
    parser.add_argument(
        "--anchors",
        nargs="*",
        default=DEFAULT_ANCHORS,
        help="Anchor terms used to locate text block.",
    )
    parser.add_argument(
        "--padding-before",
        type=int,
        default=16384,
        help="Bytes to include before first anchor.",
    )
    parser.add_argument(
        "--padding-after",
        type=int,
        default=16384,
        help="Bytes to include after last anchor.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    project_root = _resolve(cwd, args.project_root).resolve()
    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")

    if args.data_file:
        data_file = _resolve(cwd, args.data_file).resolve()
    else:
        data_file = _auto_detect_data_file(project_root)

    if not data_file.is_file():
        raise SystemExit(f"data-file not found: {data_file}")

    if args.output_root:
        output_root = _resolve(cwd, args.output_root).resolve()
    else:
        output_root = _default_output_root(project_root)

    data = data_file.read_bytes()
    anchor_hits = _find_anchor_hits(data, args.anchors)

    all_offsets: List[int] = [offset for offsets in anchor_hits.values() for offset in offsets]
    if not all_offsets:
        raise SystemExit("No anchor matched in data file.")

    extract_start = max(0, min(all_offsets) - max(0, int(args.padding_before)))
    extract_end = min(len(data), max(all_offsets) + max(0, int(args.padding_after)))
    extract_bytes = data[extract_start:extract_end]
    extract_text = extract_bytes.decode("utf-8", errors="ignore")

    tokens = _extract_tokens(extract_text)
    key_pairs = _build_key_pairs(tokens)

    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "big_text_config_report.json"
    tokens_path = output_root / "big_text_config_tokens.txt"
    pairs_path = output_root / "big_text_config_key_pairs.json"

    report = {
        "schema": "u3d-big-text-config-extract-v1",
        "generatedAt": _utc_now(),
        "projectRoot": str(project_root),
        "dataFile": str(data_file),
        "dataFileSize": len(data),
        "anchors": args.anchors,
        "anchorHitCount": {k: len(v) for k, v in anchor_hits.items()},
        "anchorOffsets": anchor_hits,
        "extractRange": {
            "start": extract_start,
            "end": extract_end,
            "size": extract_end - extract_start,
        },
        "tokenCount": len(tokens),
        "keyPairCount": len(key_pairs),
        "outputFiles": {
            "tokens": str(tokens_path),
            "keyPairs": str(pairs_path),
        },
    }

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    tokens_path.write_text("\n".join(tokens) + "\n", encoding="utf-8")
    pairs_path.write_text(json.dumps(key_pairs, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[big-text] project_root : {project_root}")
    print(f"[big-text] data_file    : {data_file}")
    print(f"[big-text] extract      : {extract_start}-{extract_end} ({extract_end - extract_start} bytes)")
    print(f"[big-text] tokens       : {len(tokens)}")
    print(f"[big-text] key_pairs    : {len(key_pairs)}")
    print(f"[big-text] output_dir   : {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
