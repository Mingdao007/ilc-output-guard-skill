---
name: ilc-output-guard
description: Build and run an iterative-learning output guard for recurring writing, formatting, explanation, or delivery failures. Use when the user wants feedback to tighten future outputs, asks for an ILC-based guard, needs feedforward before drafting, wants fail-closed checks before sending, or needs historical feedback replay without double-counting duplicates.
---

# ILC Output Guard

## Overview

Use this skill to turn repeated output failures into a small closed loop:

1. bucketize explicit feedback
2. feed active bucket pressure into the next draft
3. check the draft before send
4. update bucket state only for real failures
5. dedupe repeated feedback during replay

This skill is mechanism-first. It does not prescribe one user's formatting
rules. Installers should map their own output rules into the bucket catalog and
state file.

## Public Boundary

Do not store private memory, live user state, session logs, or machine-specific
paths inside this public skill package.

State must be caller-provided or created in the current working directory.
The helper script defaults to `./ilc-output-state.json` only when no state path
is supplied.

## Core Workflow

### 1. Define buckets

Start with a compact, reusable bucket catalog. Read
`references/buckets.md` before adding new buckets.

Good buckets describe failure classes, not one-off complaints:

- `bloated_answer_shape`
- `wrong_symbol_role_binding`
- `inline_raw_latex`
- `inline_code_math`
- `display_overflow`
- `mode_selection_drift`
- `missing_required_repair`

Keep buckets finite. If a new failure is just a sharper example of an existing
bucket, update that bucket's repair rule instead of creating a new one.

### 2. Run preflight before drafting

Use active bucket pressure as feedforward:

```bash
python3 ilc-output-guard/scripts/ilc_output_guard.py preflight \
  --state ./ilc-output-state.json \
  --request "explain this derivation"
```

The output is JSON with:

- active buckets
- repair notes
- recommended draft constraints

The agent should draft under those constraints before any post-draft guard is
needed.

### 3. Check draft before send

Run:

```bash
python3 ilc-output-guard/scripts/ilc_output_guard.py check \
  --state ./ilc-output-state.json \
  --draft ./draft.md
```

Treat a nonzero exit code as unsendable. Regenerate the affected block instead
of line-patching semantic failures.

### 4. Write explicit feedback into ILC state

When the user gives concrete output feedback, write it before regenerating:

```bash
python3 ilc-output-guard/scripts/ilc_output_guard.py feedback \
  --state ./ilc-output-state.json \
  --feedback "The answer used raw LaTeX in prose again."
```

The script infers a bucket when possible. Pass `--bucket` when the owner skill
already knows the right bucket.

### 5. Replay safely

For historical replay, always pass a stable `--source-id`.

The dedupe key is:

- normalized feedback text
- bucket
- source id when supplied

If the event already exists, treat `duplicate_skipped` as a successful no-op.

## Failure Policy

Default failure classes:

- fixable mechanical failures may be rewritten once and checked again
- semantic failures should block send and trigger regeneration
- unknown failures should not silently update state; report them as unmapped

Do not use ILC as an excuse to keep adding long global rules. The loop should
compress repeated failures into stable buckets and short executable repairs.

## Script Commands

```bash
python3 ilc-output-guard/scripts/ilc_output_guard.py preflight --help
python3 ilc-output-guard/scripts/ilc_output_guard.py check --help
python3 ilc-output-guard/scripts/ilc_output_guard.py feedback --help
```

## Output Expectations

When reporting a guard run:

- state the active buckets or say none are active
- state whether the draft is sendable
- state whether feedback was applied or deduped
- keep private state paths out of public examples unless the user explicitly asks


## Validation And Checkpoints

- Before final handoff, validate the requested artifact or decision against this skill's output contract and report the verification result explicitly.
- Before any local mutation, pass the recoverability gate: create a rollback point when the change is reversible, and request confirmation when backup cannot cover the risk.
- Use an explicit checkpoint when required input is missing, tool evidence conflicts, or repeated attempts fail; wait for approval or route to the named owner instead of guessing.
- For multi-session work, update a progress or HANDOFF artifact with current state, verified result, and next executable step.
