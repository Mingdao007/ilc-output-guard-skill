# ILC Output Guard Skill

Portable skill for building an iterative-learning output guard around recurring writing, formatting, and explanation failures.

## What Ships

- installable skill: [`ilc-output-guard`](./ilc-output-guard)
- default bucket catalog: [`ilc-output-guard/references/buckets.md`](./ilc-output-guard/references/buckets.md)
- helper script: [`ilc-output-guard/scripts/ilc_output_guard.py`](./ilc-output-guard/scripts/ilc_output_guard.py)

## Install / Use

- `Codex App`: install the skill from this repo path `ilc-output-guard`
- GitHub install target:
  - repo: `<owner>/ilc-output-guard-skill`
  - path: `ilc-output-guard`
- Restart `Codex App` after installation so the new skill is discovered.

## Coverage

- bucketized output-feedback memory
- feedforward guidance before drafting
- deterministic draft checks before sending
- feedback dedupe for historical replay or repeated user corrections
- portable state files chosen by the caller

## Trigger Examples

- `Build an ILC-based guard for this output style.`
- `Remember this formatting failure and tighten future drafts.`
- `Run output guard preflight before sending this explanation.`
- `Replay old feedback without double-counting the same event.`

## Non-Trigger Examples

- `Rewrite this paragraph once.`
- `Check grammar only.`
- `Store private memory in a public repo.`

## Privacy Boundary

This public repository keeps the mechanism generic and reusable.

- No private session logs, personal memory, or live ILC state are included.
- State paths are caller-provided or default to the current working directory.
- Bucket names are generic and should be adapted by the installing agent.

## Repository Layout

- `ilc-output-guard/`: installable `Codex App` skill
- `ilc-output-guard/references/`: bundled public references
- `ilc-output-guard/scripts/`: bundled helper scripts
- `CHANGELOG.md`: release history
- `LICENSE`: `MIT`

Chinese:

- [README.zh-CN.md](./README.zh-CN.md)
