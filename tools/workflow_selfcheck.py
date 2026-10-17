#!/usr/bin/env python3
"""Read-only workflow/package checks; never imports or runs game/project code.

Exit 0 means the documented package is internally consistent, not that a game
has passed migration or runtime acceptance. Exit 1 means a package check failed.
Only --report writes a file. All other operations use the Python standard library
to read entry documents, Markdown links, template dependencies and source hashes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlsplit


REQUIRED_ENTRIES = (
    "新游戏迁移还原入口.md",
    "工作流说明.md",
    "experience/README.md",
    "experience/05-复杂还原方法/README.md",
    "experience/90-项目案例归档/README.md",
    "experience/90-项目案例归档/cocosgame2增补/README.md",
    "experience/90-项目案例归档/cocosgame2增补/未随包提供正文.md",
)
TT_TEMPLATE = "templates/bytedance-mini-game-cc2.4"
TT_DEPENDENCIES = (
    "game.js", "main.js", "adapter-min.js", "physics-min.js", "ccRequire.js",
    "cocos/cocos2d-js-min.js", "src/settings.js", "game.json", "project.config.json",
)
SOURCE_MANIFEST = "experience/90-项目案例归档/cocosgame2增补/来源清单.json"
COUNT_FIELDS = {
    "imported_docs": "imported",
    "missing_bodies": "missing_body",
    "indexes_rebuilt": "index_rebuilt",
}
FENCE = re.compile(r"^[ \t]{0,3}(?:> ?)*(`{3,}|~{3,})(.*)$")
REFERENCE = re.compile(r"^[ \t]{0,3}\[([^\]\n]+)\]:[ \t]*(.*)$")
MARKDOWN_ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~\\])")


def blank(text: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in text)


def mask_code(text: str) -> str:
    """Keep offsets/line numbers while masking fenced code, comments and code spans."""
    lines = []
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence_char:
            lines.append(blank(line))
            if match and match[1][0] == fence_char and len(match[1]) >= fence_length and not match[2].strip():
                fence_char = ""
        elif match:
            fence_char, fence_length = match[1][0], len(match[1])
            lines.append(blank(line))
        else:
            lines.append(line)
    masked = re.sub(r"<!--[\s\S]*?-->", lambda match: blank(match[0]), "".join(lines))
    characters = list(masked)
    cursor = 0
    while cursor < len(masked):
        if masked[cursor] != "`" or escaped(masked, cursor):
            cursor += 1
            continue
        end = cursor
        while end < len(masked) and masked[end] == "`":
            end += 1
        closing = re.search(r"(?<!`)`{" + str(end - cursor) + r"}(?!`)", masked[end:])
        if closing:
            stop = end + closing.end()
            characters[cursor:stop] = blank(masked[cursor:stop])
            cursor = stop
        else:
            cursor = end
    return "".join(characters)


def escaped(text: str, position: int) -> bool:
    slashes = 0
    position -= 1
    while position >= 0 and text[position] == "\\":
        slashes += 1
        position -= 1
    return slashes % 2 == 1


def closing_bracket(text: str, start: int) -> Optional[int]:
    depth = 1
    for cursor in range(start + 1, len(text)):
        if escaped(text, cursor):
            continue
        if text[cursor] == "[":
            depth += 1
        elif text[cursor] == "]":
            depth -= 1
            if not depth:
                return cursor
    return None


def read_destination(text: str, start: int) -> Optional[Tuple[str, int]]:
    cursor = start
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text):
        return None
    if text[cursor] == "<":
        begin = cursor + 1
        cursor = begin
        while cursor < len(text):
            if text[cursor] == ">" and not escaped(text, cursor):
                return text[begin:cursor], cursor + 1
            if text[cursor] == "\n":
                return None
            cursor += 1
        return None
    begin = cursor
    depth = 0
    while cursor < len(text):
        char = text[cursor]
        if escaped(text, cursor):
            cursor += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if not depth:
                break
            depth -= 1
        elif char.isspace():
            break
        cursor += 1
    if depth:
        return None
    return text[begin:cursor], cursor


def valid_inline_tail(text: str, cursor: int) -> bool:
    """Require a closing link delimiter, allowing the optional Markdown title."""
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor < len(text) and text[cursor] == ")":
        return True
    if cursor >= len(text) or text[cursor] not in "\"'(":
        return False
    title_end = ")" if text[cursor] == "(" else text[cursor]
    cursor += 1
    while cursor < len(text) and (text[cursor] != title_end or escaped(text, cursor)):
        cursor += 1
    cursor += 1
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    return cursor < len(text) and text[cursor] == ")"


def reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def markdown_links(text: str) -> Iterable[Tuple[str, int]]:
    """Read inline/image links and used reference links outside literal code."""
    masked = mask_code(text)
    references: Dict[str, str] = {}
    definition_lines = set()
    lines = masked.splitlines()
    for number, line in enumerate(lines, 1):
        match = REFERENCE.match(line)
        if match:
            destination = read_destination(match[2], 0)
            continued = False
            if not destination and not match[2].strip() and number < len(lines):
                destination = read_destination(lines[number], 0)
                continued = bool(destination)
            if destination:
                references.setdefault(reference_label(match[1]), destination[0])
                definition_lines.add(number)
                if continued:
                    definition_lines.add(number + 1)
    reference_suffixes = set()
    for cursor, char in enumerate(masked):
        if char != "[" or escaped(masked, cursor) or cursor in reference_suffixes:
            continue
        number = masked.count("\n", 0, cursor) + 1
        if number in definition_lines:
            continue
        end = closing_bracket(masked, cursor)
        if end is None:
            continue
        label = masked[cursor + 1:end]
        after = end + 1
        if after < len(masked) and masked[after] == "(":
            destination = read_destination(masked, after + 1)
            if destination and valid_inline_tail(masked, destination[1]):
                yield destination[0], number
        elif after < len(masked) and masked[after] == "[":
            reference_end = closing_bracket(masked, after)
            if reference_end is not None:
                reference_suffixes.add(after)
                key = reference_label(masked[after + 1:reference_end] or label)
                if key in references:
                    yield references[key], number
        else:
            key = reference_label(label)
            if key in references:
                yield references[key], number


def local_link_path(document: Path, target: str) -> Optional[Path]:
    target = MARKDOWN_ESCAPE.sub(r"\1", target.strip())
    if not target or target.startswith(("#", "//")):
        return None
    windows_absolute = bool(re.match(r"^[A-Za-z]:[\\/]", target))
    if windows_absolute:
        local = target.split("#", 1)[0].split("?", 1)[0]
    else:
        parsed = urlsplit(target)
        if parsed.scheme and parsed.scheme.lower() != "file":
            return None
        local = parsed.path
        if parsed.scheme.lower() == "file":
            if parsed.netloc and parsed.netloc.lower() != "localhost":
                local = "//" + parsed.netloc + local
            elif re.match(r"^/[A-Za-z]:/", local):
                local = local[1:]
    local = unquote(local).replace("\\", "/")
    if not local:
        return None
    path = Path(local)
    return path if path.is_absolute() else document.parent / path


def add_issue(report: Dict, level: str, check: str, message: str, path: str = "", **details) -> None:
    item = {"check": check, "message": message}
    if path:
        item["path"] = path
    item.update(details)
    report[level].append(item)


def package_path(root: Path, relative: str) -> Path:
    """Manifest destinations must stay inside the package, on every host."""
    if not relative or relative.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", relative):
        raise ValueError("destination must be relative to the workflow root")
    path = (root / relative.replace("\\", "/")).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("destination escapes the workflow root") from exc
    return path


def check_manifest(root: Path, report: Dict) -> None:
    manifest_path = root / SOURCE_MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
    except (OSError, UnicodeError, ValueError) as exc:
        add_issue(report, "errors", "source_manifest", f"cannot read source manifest: {exc}", SOURCE_MANIFEST)
        return
    records = manifest.get("records")
    if not isinstance(records, list):
        add_issue(report, "errors", "source_manifest", "records must be an array", SOURCE_MANIFEST)
        return
    counts = Counter()
    destinations = set()
    sources = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("status") not in COUNT_FIELDS.values():
            add_issue(report, "errors", "source_manifest", f"record {index} has an invalid status/object", SOURCE_MANIFEST)
            continue
        status = record["status"]
        counts[status] += 1
        source = record.get("source_path")
        if isinstance(source, str):
            if source in sources:
                add_issue(report, "errors", "source_manifest", f"duplicate source record: {source}", SOURCE_MANIFEST)
            sources.add(source)
        if status != "imported":
            continue
        destination = record.get("destination")
        digest = record.get("imported_sha256")
        if not isinstance(destination, str) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            add_issue(report, "errors", "source_hash", f"record {index} requires destination and SHA-256", SOURCE_MANIFEST)
            continue
        if destination in destinations:
            add_issue(report, "errors", "source_manifest", f"duplicate imported destination: {destination}", SOURCE_MANIFEST)
        destinations.add(destination)
        try:
            destination_path = package_path(root, destination)
            actual = hashlib.sha256(destination_path.read_bytes()).hexdigest()
            report["counts"]["imported_hashes_checked"] += 1
            if actual != digest.lower():
                add_issue(report, "errors", "source_hash", "imported body SHA-256 differs from manifest", destination, expected=digest.lower(), actual=actual)
        except (OSError, ValueError) as exc:
            add_issue(report, "errors", "source_hash", f"cannot verify imported body: {exc}", destination)
    expected_counts = {"source_docs": len(records)}
    expected_counts.update({field: counts[status] for field, status in COUNT_FIELDS.items()})
    for field, actual in expected_counts.items():
        expected = manifest.get(field)
        report["counts"]["manifest_" + field] = actual
        if not isinstance(expected, int) or isinstance(expected, bool) or expected != actual:
            add_issue(report, "errors", "source_counts", f"{field}: declared {expected!r}, actual {actual}", SOURCE_MANIFEST)
    if sum(counts.values()) != len(records):
        add_issue(report, "errors", "source_counts", "source_docs must equal imported + missing_body + index_rebuilt records", SOURCE_MANIFEST)
    if counts["missing_body"]:
        add_issue(report, "warnings", "known_missing_body", f"{counts['missing_body']} known source documents contain no bundled body; not accepted as implementation evidence", SOURCE_MANIFEST, count=counts["missing_body"])
    unbundled = manifest.get("unbundled_link_references")
    if not isinstance(unbundled, list):
        add_issue(report, "errors", "source_manifest", "unbundled_link_references must be an array", SOURCE_MANIFEST)
    else:
        report["counts"]["registered_historical_references"] = len(unbundled)
        for index, reference in enumerate(unbundled):
            if not isinstance(reference, dict) or not isinstance(reference.get("document"), str) or not isinstance(reference.get("target"), str):
                add_issue(report, "errors", "source_manifest", f"historical reference {index} requires document and target", SOURCE_MANIFEST)
                continue
            try:
                if not package_path(root, reference["document"]).is_file():
                    raise ValueError("historical reference document is missing")
            except (OSError, ValueError) as exc:
                add_issue(report, "errors", "source_manifest", str(exc), reference["document"])
        if unbundled:
            add_issue(report, "warnings", "historical_references", f"{len(unbundled)} historical project references are registered as unbundled; active Markdown links still require valid targets", SOURCE_MANIFEST, count=len(unbundled))


def run_selfcheck(root: Path) -> Dict:
    root = root.resolve()
    report = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "status": "ok",
        "exit_code": 0,
        "scope": "Workflow files, Markdown link targets, TT template dependencies and imported source hashes; no game code is executed.",
        "counts": {"entry_files_checked": 0, "template_files_checked": 0, "markdown_files_checked": 0, "local_links_checked": 0, "nonlocal_or_anchor_links_skipped": 0, "imported_hashes_checked": 0},
        "errors": [],
        "warnings": [],
    }
    if not root.is_dir():
        add_issue(report, "errors", "root", "workflow root directory does not exist", str(root))
    else:
        for relative in REQUIRED_ENTRIES:
            report["counts"]["entry_files_checked"] += 1
            if not (root / relative).is_file():
                add_issue(report, "errors", "entry_document", "required entry document is missing", relative)
        for dependency in TT_DEPENDENCIES:
            relative = TT_TEMPLATE + "/" + dependency
            report["counts"]["template_files_checked"] += 1
            if not (root / relative).is_file():
                add_issue(report, "errors", "tt_template", "TT template dependency is missing", relative)
        check_manifest(root, report)
        try:
            documents = sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".md")
        except OSError as exc:
            add_issue(report, "errors", "markdown_scan", f"cannot enumerate Markdown files: {exc}")
            documents = []
        for document in documents:
            relative = document.relative_to(root).as_posix()
            report["counts"]["markdown_files_checked"] += 1
            try:
                text = document.read_text(encoding="utf-8-sig")
                for target, line in markdown_links(text):
                    path = local_link_path(document, target)
                    if path is None:
                        report["counts"]["nonlocal_or_anchor_links_skipped"] += 1
                        continue
                    report["counts"]["local_links_checked"] += 1
                    if not path.exists():
                        add_issue(report, "errors", "markdown_link", "local Markdown link target does not exist", relative, line=line, target=target)
            except (OSError, UnicodeError, ValueError) as exc:
                add_issue(report, "errors", "markdown_scan", f"cannot check Markdown document: {exc}", relative)
    if report["errors"]:
        report["status"], report["exit_code"] = "failed", 1
    report["counts"]["errors"] = len(report["errors"])
    report["counts"]["warnings"] = len(report["warnings"])
    return report


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Workflow root; defaults to this script's parent directory's parent.")
    parser.add_argument("--report", type=Path, help="Optional JSON report; this is the only file written.")
    args = parser.parse_args()
    report = run_selfcheck(args.root)
    print(f"Workflow self-check: {report['status']} (exit {report['exit_code']})")
    print(f"Root: {report['root']}")
    for key, value in report["counts"].items():
        print(f"  {key}: {value}")
    for level, label in (("errors", "ERROR"), ("warnings", "WARNING")):
        for item in report[level]:
            location = item.get("path", "")
            if "line" in item:
                location += f":{item['line']}"
            print(f"[{label}][{item['check']}] {location}: {item['message']}")
            if "target" in item:
                print(f"  target: {item['target']}")
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Report: {args.report.resolve()}")
        except OSError as exc:
            print(f"[ERROR][report_write] {args.report}: {exc}", file=sys.stderr)
            return 1
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
