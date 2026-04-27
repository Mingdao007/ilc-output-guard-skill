# ILC Output Buckets

Keep this catalog small. A bucket is useful when it changes the next draft or
the send gate.

## Default Buckets

| Bucket | Failure class | Feedforward repair |
| --- | --- | --- |
| `bloated_answer_shape` | The answer is longer or broader than the task needs. | Cut optional recap, keep only required sections, and bind the current target before expanding. |
| `wrong_symbol_role_binding` | Symbols, terms, variables, or labels appear before their role is clear. | Bind each new object before using it in claims or formulas. |
| `inline_raw_latex` | Raw LaTeX or math delimiters leak into prose. | Move relation-bearing math into display blocks or rewrite in plain prose. |
| `inline_code_math` | Mathematical objects are placed in code spans. | Reserve code spans for operational identifiers; use plain prose or display math for math objects. |
| `display_overflow` | A displayed relation is too long for the output surface. | Split long relation chains before send. |
| `mode_selection_drift` | The answer shape does not match the user's requested task. | Restate the selected mode and regenerate inside that mode. |
| `missing_required_repair` | The user corrected a mistake but the next answer only acknowledged it. | Repair the latest concrete affected object before reporting the rule update. |

## Bucket Design Rules

- Prefer failure classes over one-off examples.
- Merge near-duplicates unless they require different feedforward repairs.
- Keep user-specific style details outside the public package.
- Store private state in the installing workspace, not in this repository.
