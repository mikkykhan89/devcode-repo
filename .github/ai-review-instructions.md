# AI pull-request review rules

Review only the proposed change. Report a finding only when it is specific,
actionable, and likely to matter.

Prioritize, in this order:

1. Correctness bugs, regressions, and missing error handling.
2. Security, data exposure, and unsafe input handling.
3. Tests that are needed to protect changed behavior.
4. Maintainability problems that make the change materially harder to operate.

Do not report formatting preferences, praise, speculative issues, or anything
that a standard formatter/linter would catch. Use `P0` only for a release
blocker, `P1` for an important issue, and `P2` for a normal actionable issue.
If no findings are justified, return an empty `findings` list.
