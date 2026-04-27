from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ilc_output_guard.py"
SPEC = importlib.util.spec_from_file_location("ilc_output_guard", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class IlcOutputGuardTests(unittest.TestCase):
    def test_feedback_dedupes_same_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state = Path(tmpdir) / "state.json"
            argv = [
                "ilc_output_guard.py",
                "feedback",
                "--state",
                str(state),
                "--feedback",
                "The answer used raw LaTeX in prose again.",
                "--source-id",
                "session-1",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", new_callable=io.StringIO) as first:
                self.assertEqual(MODULE.main(), 0)
            with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", new_callable=io.StringIO) as second:
                self.assertEqual(MODULE.main(), 0)
            self.assertEqual(json.loads(first.getvalue())["status"], "applied")
            self.assertEqual(json.loads(second.getvalue())["status"], "duplicate_skipped")

    def test_preflight_reports_active_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state = Path(tmpdir) / "state.json"
            state.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "buckets": {
                            "inline_raw_latex": {
                                "count": 2,
                                "feedback_hits": 1,
                                "last_seen": "2026-04-27T00:00:00+00:00",
                            }
                        },
                        "feedback_events": {},
                    }
                ),
                encoding="utf-8",
            )
            argv = ["ilc_output_guard.py", "preflight", "--state", str(state), "--request", "explain"]
            with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(MODULE.main(), 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["active_bucket_count"], 1)
            self.assertEqual(result["active_buckets"][0]["bucket"], "inline_raw_latex")

    def test_check_blocks_raw_latex_and_code_math(self) -> None:
        draft = "This has $x=y$ and `F=ma` in prose."
        argv = ["ilc_output_guard.py", "check"]
        with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdin", io.StringIO(draft)), mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out:
            self.assertEqual(MODULE.main(), 1)
        result = json.loads(out.getvalue())
        buckets = {item["bucket"] for item in result["failures"]}
        self.assertIn("inline_raw_latex", buckets)
        self.assertIn("inline_code_math", buckets)


if __name__ == "__main__":
    unittest.main()
