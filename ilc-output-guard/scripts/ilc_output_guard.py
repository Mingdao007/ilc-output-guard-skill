#!/usr/bin/env python3
"""Small public helper for ILC-style output guarding."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


STATE_VERSION = 1
DEFAULT_STATE_PATH = Path("ilc-output-state.json")
DEFAULT_BUCKET_REPAIRS = {
    "bloated_answer_shape": "Cut optional recap and keep only the current target, required context, and one concise repair.",
    "wrong_symbol_role_binding": "Bind each new symbol, term, or label before using it in a claim.",
    "inline_raw_latex": "Move raw LaTeX, math delimiters, and relation-bearing math out of prose.",
    "inline_code_math": "Use code spans only for operational identifiers, not mathematical objects.",
    "display_overflow": "Split long displayed relations before send.",
    "mode_selection_drift": "Restate the selected task mode and regenerate inside that mode.",
    "missing_required_repair": "Repair the latest concrete affected object before reporting the rule update.",
}
BUCKET_KEYWORDS = {
    "bloated_answer_shape": ("too long", "bloated", "verbose", "too much", "啰嗦", "太长", "废话"),
    "wrong_symbol_role_binding": ("symbol", "variable", "undefined", "not defined", "符号", "变量", "没解释"),
    "inline_raw_latex": ("latex", "$", "\\", "raw latex", "行内latex"),
    "inline_code_math": ("backtick", "code span", "`", "反引号", "代码"),
    "display_overflow": ("overflow", "too wide", "line too long", "超行", "太宽"),
    "mode_selection_drift": ("wrong mode", "not what i asked", "跑题", "模式", "不是我要的"),
    "missing_required_repair": ("you only acknowledged", "did not fix", "没改", "只是承认", "没有修"),
}
RAW_LATEX_RE = re.compile(r"(?<!`)(\$[^$\n]+\$|\\[A-Za-z]+(?:\{[^}\n]*\})?)")
CODE_MATH_RE = re.compile(r"`[^`\n]*(?:=|≈|∝|->|→|<-|←|\\[A-Za-z]|\b[A-Z]\s*[A-Za-z]*\s*=)[^`\n]*`")
LONG_LINE_RE = re.compile(r"^.{180,}$", re.MULTILINE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def fingerprint(bucket: str, feedback: str, source_id: str | None) -> str:
    payload = json.dumps(
        {
            "bucket": bucket,
            "feedback": normalize_text(feedback),
            "source_id": source_id or "",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": STATE_VERSION, "buckets": {}, "feedback_events": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"State is not a JSON object: {path}")
    data.setdefault("version", STATE_VERSION)
    data.setdefault("buckets", {})
    data.setdefault("feedback_events", {})
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def infer_bucket(text: str) -> str:
    normalized = normalize_text(text)
    for bucket, keywords in BUCKET_KEYWORDS.items():
        if any(keyword.casefold() in normalized for keyword in keywords):
            return bucket
    return "missing_required_repair"


def active_buckets(state: dict, threshold: int) -> list[dict]:
    buckets = []
    for name, entry in sorted((state.get("buckets") or {}).items()):
        if not isinstance(entry, dict):
            continue
        count = int(entry.get("count", 0) or 0)
        if count >= threshold:
            buckets.append(
                {
                    "bucket": name,
                    "count": count,
                    "last_seen": entry.get("last_seen"),
                    "repair": DEFAULT_BUCKET_REPAIRS.get(name, "Apply the owner-defined repair before drafting."),
                }
            )
    return buckets


def command_preflight(args: argparse.Namespace) -> int:
    state = load_state(args.state)
    active = active_buckets(state, args.threshold)
    result = {
        "status": "ok",
        "request": args.request,
        "active_bucket_count": len(active),
        "active_buckets": active,
        "draft_constraints": [item["repair"] for item in active],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def detect_draft_failures(text: str) -> list[dict]:
    failures = []
    if RAW_LATEX_RE.search(text):
        failures.append({"bucket": "inline_raw_latex", "code": "raw_latex_in_prose"})
    if CODE_MATH_RE.search(text):
        failures.append({"bucket": "inline_code_math", "code": "math_in_code_span"})
    if LONG_LINE_RE.search(text):
        failures.append({"bucket": "display_overflow", "code": "long_line_overflow_risk"})
    return failures


def command_check(args: argparse.Namespace) -> int:
    text = args.draft.read_text(encoding="utf-8") if args.draft else sys.stdin.read()
    failures = detect_draft_failures(text)
    result = {
        "status": "blocked" if failures else "sendable",
        "failure_count": len(failures),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


def command_feedback(args: argparse.Namespace) -> int:
    state = load_state(args.state)
    bucket = args.bucket or infer_bucket(args.feedback)
    event_id = fingerprint(bucket, args.feedback, args.source_id)
    events = state.setdefault("feedback_events", {})
    if event_id in events:
        print(json.dumps({"status": "duplicate_skipped", "bucket": bucket, "fingerprint": event_id}, ensure_ascii=False, indent=2))
        return 0

    now = utc_now()
    buckets = state.setdefault("buckets", {})
    entry = buckets.setdefault(bucket, {"count": 0, "feedback_hits": 0, "last_seen": None})
    entry["count"] = int(entry.get("count", 0) or 0) + args.weight
    entry["feedback_hits"] = int(entry.get("feedback_hits", 0) or 0) + 1
    entry["last_seen"] = now
    events[event_id] = {
        "bucket": bucket,
        "normalized_feedback": normalize_text(args.feedback),
        "source_id": args.source_id,
        "first_seen": now,
        "weight": args.weight,
    }
    save_state(args.state, state)
    print(
        json.dumps(
            {
                "status": "applied",
                "bucket": bucket,
                "fingerprint": event_id,
                "count": entry["count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ILC-style output guard helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight", help="emit feedforward constraints from active bucket state")
    preflight.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    preflight.add_argument("--request", default="")
    preflight.add_argument("--threshold", type=int, default=1)
    preflight.set_defaults(func=command_preflight)

    check = sub.add_parser("check", help="check a draft before send")
    check.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    check.add_argument("--draft", type=Path)
    check.set_defaults(func=command_check)

    feedback = sub.add_parser("feedback", help="write explicit feedback into bucket state")
    feedback.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    feedback.add_argument("--feedback", required=True)
    feedback.add_argument("--bucket", choices=sorted(DEFAULT_BUCKET_REPAIRS))
    feedback.add_argument("--source-id")
    feedback.add_argument("--weight", type=int, default=2)
    feedback.set_defaults(func=command_feedback)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
