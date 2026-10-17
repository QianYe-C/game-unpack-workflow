"""Offline package/self-check regressions, using only temporary synthetic files.

Run from the workflow root:
    python -B -m unittest discover -s tools/tests -p "test_*.py" -v
No game code, network requests or real imported source documents are required.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "workflow_selfcheck.py"
SPEC = importlib.util.spec_from_file_location("reviewed_workflow_selfcheck", SCRIPT)
selfcheck = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = selfcheck
SPEC.loader.exec_module(selfcheck)


class WorkflowSelfcheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-selfcheck-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in selfcheck.REQUIRED_ENTRIES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic entry\n", encoding="utf-8")
        for dependency in selfcheck.TT_DEPENDENCIES:
            path = self.root / selfcheck.TT_TEMPLATE / dependency
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic dependency\n", encoding="utf-8")
        self.body = self.root / "experience/归档正文.md"
        self.body.write_text("# synthetic imported body\n", encoding="utf-8")
        self.manifest = {
            "source_docs": 3,
            "imported_docs": 1,
            "missing_bodies": 1,
            "indexes_rebuilt": 1,
            "records": [
                {
                    "status": "imported",
                    "source_path": "body.md",
                    "destination": "experience/归档正文.md",
                    "imported_sha256": hashlib.sha256(self.body.read_bytes()).hexdigest(),
                },
                {"status": "missing_body", "source_path": "missing.md"},
                {"status": "index_rebuilt", "source_path": "README.md"},
            ],
            "unbundled_link_references": [
                {"document": "新游戏迁移还原入口.md", "target": "../not-shipped-project.js"},
            ],
        }
        self.write_manifest()

    def write_manifest(self):
        path = self.root / selfcheck.SOURCE_MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.manifest, ensure_ascii=False), encoding="utf-8")

    def run_check(self):
        return selfcheck.run_selfcheck(self.root)

    def test_valid_package_known_missing_body_is_warning(self):
        report = self.run_check()
        self.assertEqual(0, report["exit_code"], report["errors"])
        self.assertEqual(2, len(report["warnings"]))
        self.assertEqual(1, report["counts"]["imported_hashes_checked"])
        self.assertTrue(any(item["check"] == "known_missing_body" for item in report["warnings"]))

    def test_chinese_spaces_fragments_angles_references_images_and_titles(self):
        document = self.root / "有 空格目录/正文(甲).md"
        document.parent.mkdir()
        document.write_text("# local target", encoding="utf-8")
        (self.root / "图.png").write_bytes(b"synthetic image")
        (self.root / "路径(甲).md").write_text("# escaped target", encoding="utf-8")
        text = """[inline](<有 空格目录/正文(甲).md#部分>)
![图](图.png)
[encoded](有%20空格目录/正文%28甲%29.md?raw=1#frag)
[reference][key]
[key]: <有 空格目录/正文(甲).md> "title"
[escaped](路径\\(甲\\).md)
[title](图.png 'title')
[external](https://example.invalid/missing)
[anchor](#absent)
`[inline code](ghost.md)`
```md
[fenced](ghost.md)
```
~~~markdown
[fenced2](ghost2.md)
~~~
<!-- [comment](ghost.md) -->
"""
        (self.root / "新游戏迁移还原入口.md").write_text(text, encoding="utf-8")
        report = self.run_check()
        self.assertEqual(0, report["exit_code"], report["errors"])
        self.assertEqual(6, report["counts"]["local_links_checked"])
        self.assertEqual(2, report["counts"]["nonlocal_or_anchor_links_skipped"])

    def test_unknown_broken_link_fails_with_document_and_line(self):
        (self.root / "新游戏迁移还原入口.md").write_text(
            "# Test\n[bad](absent.md#fragment)\n", encoding="utf-8",
        )
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        errors = [item for item in report["errors"] if item["check"] == "markdown_link"]
        self.assertEqual("新游戏迁移还原入口.md", errors[0]["path"])
        self.assertEqual(2, errors[0]["line"])

    def test_missing_template_dependency_fails(self):
        (self.root / selfcheck.TT_TEMPLATE / "adapter-min.js").unlink()
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        self.assertTrue(any(item["check"] == "tt_template" for item in report["errors"]))

    def test_modified_imported_body_fails_hash_check(self):
        self.body.write_text("changed body", encoding="utf-8")
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        self.assertTrue(any(item["check"] == "source_hash" for item in report["errors"]))

    def test_manifest_count_mismatch_fails(self):
        self.manifest["source_docs"] = 100
        self.write_manifest()
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        self.assertTrue(any(item["check"] == "source_counts" for item in report["errors"]))

    def test_manifest_import_path_cannot_escape_package(self):
        self.manifest["records"][0]["destination"] = "../outside.md"
        self.write_manifest()
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        self.assertTrue(any("escapes" in item["message"] for item in report["errors"]))

    def test_reference_links_and_nested_image_links(self):
        text = """[![img](图.png)](https://example.invalid/)
[ref][] [short]
[ref]: 图.png
[short]: <图.png>
"""
        self.assertEqual(
            [("https://example.invalid/", 1), ("图.png", 1), ("图.png", 2), ("图.png", 2)],
            list(selfcheck.markdown_links(text)),
        )

    def test_registered_historical_reference_cannot_exempt_active_broken_link(self):
        (self.root / "新游戏迁移还原入口.md").write_text(
            "[history](../not-shipped-project.js)\n", encoding="utf-8",
        )
        report = self.run_check()
        self.assertEqual(1, report["exit_code"])
        self.assertTrue(any(item["check"] == "markdown_link" for item in report["errors"]))

    def test_missing_root_has_clear_error_report(self):
        report = selfcheck.run_selfcheck(self.root / "absent")
        self.assertEqual(1, report["exit_code"])
        self.assertEqual("root", report["errors"][0]["check"])

    def test_reference_destination_on_next_line(self):
        text = "[test][ref]\n[ref]:\n  <中文 路径.md#fragment>\n"
        self.assertEqual([("中文 路径.md#fragment", 1)], list(selfcheck.markdown_links(text)))

    def test_escaped_backtick_does_not_hide_actual_link(self):
        text = "\\` [actual](target.md)\n"
        self.assertEqual([("target.md", 1)], list(selfcheck.markdown_links(text)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
