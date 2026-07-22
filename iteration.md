# Current Iteration

## Goal

Iteration 2: Add a read-only `gleaner sessions` CLI command that lists locally-captured sessions from the local vault.

## Acceptance Signal

- A `gleaner sessions` CLI command is added.
- It lists locally-captured sessions from the local vault, one row per unique `session_id`.
- Displayed fields: source (claude/cursor), project, last-updated time, and message count.
- Order is newest-first.
- Supports optional `--source` and `--limit` (default 20) flags.
- Command is strictly read-only, uses no network, and never touches production.
- A deterministic test captures a couple of mock sessions into a temp vault and asserts the command lists them with correct fields newest-first and that `--source` filters correctly.
- The command is documented in the README CLI section.
- PR against `ikamensh/gleaner`.
