# Repository Guidelines

## Project Structure & Module Organization
- Core code lives in `constructionist_math.py` at the repo root; it contains the `Graph`, `Node`, and operation helpers plus a small `demo`.
- No test directory yet; ad-hoc checks run via the demo. Keep new modules flat in root unless a package layout becomes necessary.
- Exports: `to_json` and `to_dot` are the primary inspection interfaces; preserve their signatures and JSON shape when extending.
- Docs live in root (`VISION.md`, plus any speculative notes like `PRIME_HARMONICS_NOTE.md`).

## Build, Test, and Development Commands
- `python3 constructionist_math.py` — runs the demo to build a small graph and prints JSON and DOT outputs. Use this as a quick regression check.
- `python3 constructionist_math.py --limit 10` — runs a larger demo universe.
- `python3 constructionist_math.py '1/(1+1)'` — evaluates a minimal “MoO language” expression (only literal `1`, operators `+ - * /`, and parentheses).
- `python3 constructionist_math.py --stats ...` — prints `Graph.stats()` and `Graph.resolve_events()` before JSON/DOT.
- `python3 constructionist_math.py --maps ...` — convenience flag for `--stats --resolve-dot --field --field-ascii`.
- `python3 constructionist_math.py --write-maps out/demo --limit 6` — writes `out/demo.*` map files (DOT + resolve-DOT + field CSV/JSON/ASCII + stats).
- If Graphviz is available, render maps with: `dot -Tsvg out/demo.resolve.dot -o out/demo.resolve.svg`.
- For interactive work, import `Graph` from `constructionist_math` in a REPL or notebook.

## Coding Style & Naming Conventions
- Python 3 with type hints; prefer `dataclass` for simple data holders.
- Indentation: 4 spaces; keep lines ASCII unless data demands otherwise.
- Function and variable names are snake_case; classes are CapWords.
- Avoid silent mutation of shared structures; prefer helper methods (e.g., `_record_edge`, `_resolve_speculative_to_ref`, `_maybe_resolve_new_spec_to_existing_ref`) to keep graph integrity rules centralized.

## Testing Guidelines
- There is no formal test suite yet; rely on the demo run for quick validation.
- When adding features, create lightweight checks that exercise grounded vs speculative paths (e.g., division by zero, zero-annihilation multiplication, speculative promotion to grounded, and S→G resolution telemetry).
- If you add tests, colocate them with the code or start a `tests/` directory using `pytest`; name tests `test_*.py`.

## Commit & Pull Request Guidelines
- IMPORTANT: the assistant must not run `git` commands or modify anything under `.git/` (no status/log/diff, no commits, no pushes, no branch operations). Handle all version-control actions manually.
- Commit messages: use concise, imperative summaries (e.g., “Add speculative resolution to grounded refs”). Include context if touching graph invariants.
- Pull requests should describe behavior changes, new invariants, and any format changes to JSON/DOT exports. Note manual test commands run (e.g., `python3 constructionist_math.py`) and include sample outputs or screenshots when relevant.

## Security & Configuration Tips
- No external dependencies or network access required; keep additions stdlib-only unless justified.
- The model assumes controlled inputs; if you add file or user input parsing, validate operations and guard against unsafe evaluation.
