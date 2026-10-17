"""Offline regression fixtures for the reviewed prefetch gate.

Run: python -B -m unittest discover -s tools/tests -p "test_*.py" -v
Only temporary synthetic assets are written; HTTP download calls are mocked.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "cocos_prefetch_assets.py"
SPEC = importlib.util.spec_from_file_location("reviewed_prefetch", SCRIPT)
prefetch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prefetch
SPEC.loader.exec_module(prefetch)

UUID_A = "aa000000-0000-4000-8000-000000000001"
UUID_B = "bb000000-0000-4000-8000-000000000002"


class PrefetchGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="prefetch-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        self.report = self.root / "report.json"

    def bundle(self, name="main", *, imports=None, natives=None, packs=None):
        directory = self.root / "assets" / name
        directory.mkdir(parents=True, exist_ok=True)
        data = {
            "uuids": [UUID_A, UUID_B],
            "packs": packs or {},
            "versions": {"import": imports or [], "native": natives or []},
        }
        (directory / "config.fixture.json").write_text(json.dumps(data), encoding="utf-8")
        return directory

    def put(self, relative, payload=b"synthetic asset"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def run_gate(self, *arguments, download=None):
        argv = [str(SCRIPT), "--project", str(self.root), "--report", str(self.report), *arguments]
        # A default blocker makes accidental networking an immediate test failure.
        downloader = download or mock.Mock(side_effect=AssertionError("unexpected download"))
        with mock.patch.object(sys, "argv", argv), mock.patch.object(prefetch, "safe_download", downloader):
            with contextlib.redirect_stdout(io.StringIO()):
                code = prefetch.main()
        if download is None:
            downloader.assert_not_called()
        self.assertTrue(self.report.is_file())
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(code, report["exit_code"])
        return code, report

    def test_no_config_cannot_pass(self):
        code, report = self.run_gate("--scan-only")
        self.assertEqual(2, code)
        self.assertEqual("error", report["status"])
        self.assertEqual(0, report["config_count"])
        self.assertIn("no matching config", report["error_entries"][0]["reason"])

    def test_missing_assets_still_writes_error_report(self):
        (self.root / "assets").rmdir()
        code, report = self.run_gate("--scan-only")
        self.assertEqual(2, code)
        self.assertIn("directory not found", report["error_entries"][0]["reason"])

    def test_zero_resources_cannot_pass(self):
        self.bundle()
        code, report = self.run_gate("--scan-only")
        self.assertEqual(2, code)
        self.assertEqual(1, report["config_count"])
        self.assertEqual(0, report["scanned"])
        self.assertIn("zero resource", report["error_entries"][0]["reason"])

    def test_selected_bundle_requires_config(self):
        self.bundle(natives=[0, "v1"])
        code, report = self.run_gate("main", "typo_bundle", "--base-url", "https://example.invalid/")
        self.assertEqual(2, code)
        self.assertEqual(0, report["downloaded"])
        self.assertTrue(any(e["rel"] == "assets/typo_bundle" for e in report["error_entries"]))

    def test_scan_missing_assets_is_incomplete(self):
        self.bundle(imports=[0, "v1"], natives=[0, "v2"])
        code, report = self.run_gate("--scan-only")
        self.assertEqual(1, code)
        self.assertEqual("incomplete", report["status"])
        self.assertEqual(2, report["missing_local"])

    def test_complete_assets_and_extra_native_formats_pass(self):
        self.bundle(imports=[0, "i1"], natives=[0, "n1", 1, "n2"])
        self.put(f"assets/main/import/aa/{UUID_A}.i1.cconb")
        self.put(f"assets/main/native/aa/{UUID_A}.n1.m4a")
        self.put(f"assets/main/native/bb/{UUID_B}.n2.mp4")
        code, report = self.run_gate("--scan-only")
        self.assertEqual(0, code)
        self.assertEqual("ok", report["status"])
        self.assertEqual(3, report["existing_local"])
        self.assertIn(".pem", prefetch.NATIVE_EXT_CANDIDATES)

    def test_backup_file_is_not_a_runtime_asset(self):
        self.bundle(natives=[0, "v1"])
        self.put(f"assets/main/native/aa/{UUID_A}.v1.bak_before_cap32")
        code, report = self.run_gate("--scan-only")
        self.assertEqual(1, code)
        self.assertEqual(1, report["missing_local"])

    def test_directory_with_asset_extension_is_not_a_file(self):
        self.bundle(natives=[0, "v1"])
        (self.root / f"assets/main/native/aa/{UUID_A}.v1.png").mkdir(parents=True)
        code, report = self.run_gate("--scan-only")
        self.assertEqual(1, code)
        self.assertEqual(1, report["missing_local"])

    def test_packed_uuid_stale_version_does_not_create_false_missing(self):
        self.bundle(imports=["pack01", "p1", 0, "stale"], packs={"pack01": [0]})
        self.put("assets/main/import/pa/pack01.p1.json")
        code, report = self.run_gate("--scan-only")
        self.assertEqual(0, code)
        self.assertEqual(1, report["scanned"])

    def test_bundle_only_urls_require_all_selected_bundle_roots(self):
        self.bundle("main", natives=[0, "v1"])
        self.bundle("extra", natives=[1, "v2"])
        code, report = self.run_gate("--bundle-url", "main=https://example.invalid/custom/")
        self.assertEqual(2, code)
        self.assertEqual(0, report["downloaded"])
        self.assertTrue(any(e["rel"] == "assets/extra" and "no remote URL" in e["reason"] for e in report["error_entries"]))
        with self.assertRaisesRegex(ValueError, "no remote URL"):
            prefetch.remote_asset_url("assets/extra/native/x.png", "extra", "", {})

    def test_successful_download_rechecks_files_and_preserves_url_overrides(self):
        self.bundle("main", imports=[0, "i1"])
        self.bundle("extra", natives=[1, "n1"])
        urls = []

        def download(url, path):
            urls.append(url)
            if not url.endswith((".cconb", ".png")):
                return False, "http-404"
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"synthetic downloaded asset")
            return True, "ok"

        code, report = self.run_gate(
            "--base-url", "https://fallback.invalid/root",
            "--bundle-url", "main=https://bundle.invalid/remote-main",
            "--workers", "1", download=download,
        )
        self.assertEqual(0, code)
        self.assertEqual(2, report["initial_missing_local"])
        self.assertEqual(0, report["missing_local"])
        self.assertEqual(2, report["existing_local"])
        self.assertEqual(2, report["downloaded"])
        self.assertIn(f"https://bundle.invalid/remote-main/import/aa/{UUID_A}.i1.cconb", urls)
        self.assertIn(f"https://fallback.invalid/root/assets/extra/native/bb/{UUID_B}.n1.png", urls)

    def test_remote_failures_return_incomplete(self):
        self.bundle(natives=[0, "v1"])
        code, report = self.run_gate(
            "--base-url", "https://example.invalid/",
            download=mock.Mock(return_value=(False, "http-404")),
        )
        self.assertEqual(1, code)
        self.assertEqual(1, report["remote_missing"])
        self.assertEqual(1, report["missing_local"])

    def test_worker_exceptions_return_incomplete(self):
        self.bundle(natives=[0, "v1"])
        code, report = self.run_gate(
            "--base-url", "https://example.invalid/",
            download=mock.Mock(side_effect=RuntimeError("fixture worker failure")),
        )
        self.assertEqual(1, code)
        self.assertEqual(1, report["errors"])
        self.assertIn("fixture worker failure", report["error_entries"][0]["reason"])

    def test_reported_download_without_file_does_not_pass(self):
        self.bundle(natives=[0, "v1"])
        code, report = self.run_gate(
            "--base-url", "https://example.invalid/",
            download=mock.Mock(return_value=(True, "ok")),
        )
        self.assertEqual(1, code)
        self.assertEqual(1, report["downloaded"])
        self.assertEqual(1, report["missing_local"])

    def test_invalid_config_still_writes_error_report(self):
        directory = self.bundle(natives=[0, "v1"])
        (directory / "config.fixture.json").write_text("{invalid", encoding="utf-8")
        code, report = self.run_gate("--scan-only")
        self.assertEqual(2, code)
        self.assertIn("JSONDecodeError", report["error_entries"][0]["reason"])

    def test_invalid_bundle_url_still_writes_error_report(self):
        self.bundle(natives=[0, "v1"])
        code, report = self.run_gate("--bundle-url", "missing-equals")
        self.assertEqual(2, code)
        self.assertTrue(any("invalid --bundle-url" in e["reason"] for e in report["error_entries"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
