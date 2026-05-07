# Repository Guidelines

## Project Structure & Module Organization
- `constructionist_math.py` is the in-memory MoO graph runtime with demo/export helpers.
- `strict_stage_moo.py` and `moo_graph_corpus.py` are the graph-first SQLite corpus path for strict-stage runs that preserve nodes and edge occurrences.
- The graph is the primary method of inspection. Values, target probes, and node summaries are secondary unless read through construction edges, graph neighborhoods, and confirmation status.
- Tests live in `tests/` when formal coverage is needed; ad-hoc checks can still run via the demo. Keep new modules flat in root unless a package layout becomes necessary.
- Exports: `to_json` and `to_dot` are the primary inspection interfaces; preserve their signatures and JSON shape when extending.
- Core docs live in root. Active research lenses live under `research/`; historical exploratory notes and transitional ledgers live under `archive/`.

## Build, Test, and Development Commands
- `python3 strict_stage_moo.py --db out/experiments/strict_stage_graph_smoke.sqlite --max-stage 80 --max-abs-p 200 --max-abs-q 200 --max-abs-value 4 --quiet --pretty` — builds a graph-first strict-stage MoO SQLite corpus.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --node 34/21 --pretty` — inspects incoming/outgoing construction edges for a node.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --node 34/21 --neighborhood --pretty` — inspects a node plus nearby results sharing its input nodes.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --confirmations --pretty` — lists values first seen speculatively and later confirmed by the core loop.
- `python3 moo_core_alignment_check.py --max-stage 6 --pretty` — compares small strict-stage output between the in-memory graph runtime and SQLite corpus path.
- `python3 constructionist_math.py` — runs the in-memory graph demo to build a small graph and prints JSON and DOT outputs.
- `python3 constructionist_math.py --limit 10` — runs a larger demo universe.
- `python3 constructionist_math.py '1/(1+1)'` — evaluates a minimal “MoO language” expression (only literal `1`, operators `+ - * /`, and parentheses).
- `python3 constructionist_math.py --stats ...` — prints `Graph.stats()` and `Graph.resolve_events()` before JSON/DOT.
- `python3 constructionist_math.py --maps ...` — convenience flag for `--stats --resolve-dot --field --field-ascii`.
- `python3 constructionist_math.py --write-maps out/demo --limit 6` — writes `out/demo.*` map files (DOT + resolve-DOT + field CSV/JSON/ASCII + stats).
- `python3 constructionist_math.py --allow-speculative-operands ...` — historical exploratory mode only. Aligned MoO records speculative nodes but does not operate on them until promotion.
- If Graphviz is available, render maps with: `dot -Tsvg out/demo.resolve.dot -o out/demo.resolve.svg`.
- For interactive work, import `Graph` from `constructionist_math` in a REPL or notebook.

## Coding Style & Naming Conventions
- Python 3 with type hints; prefer `dataclass` for simple data holders.
- Indentation: 4 spaces; keep lines ASCII unless data demands otherwise.
- Function and variable names are snake_case; classes are CapWords.
- Avoid silent mutation of shared structures; prefer helper methods (e.g., `_record_edge`, `_resolve_speculative_to_ref`, `_maybe_resolve_new_spec_to_existing_ref`) to keep graph integrity rules centralized.
- Do not add code paths that operate on speculative nodes by default. Speculative nodes are real graph nodes, but they are inspected rather than used as operands until core-loop promotion.

## Testing Guidelines
- Run focused `pytest` tests when they exist, plus the demo run for quick validation.
- When adding features, create lightweight checks that exercise grounded vs speculative paths (e.g., division by zero, zero-annihilation multiplication, speculative promotion to grounded, and S→G resolution telemetry).
- If you add tests, colocate them with the code or start a `tests/` directory using `pytest`; name tests `test_*.py`.

## Commit & Pull Request Guidelines
- IMPORTANT: the assistant must not run `git` commands or modify anything under `.git/` (no status/log/diff, no commits, no pushes, no branch operations). Handle all version-control actions manually.
- Commit messages: use concise, imperative summaries (e.g., “Add speculative resolution to grounded refs”). Include context if touching graph invariants.
- Pull requests should describe behavior changes, new invariants, and any format changes to JSON/DOT exports. Note manual test commands run (e.g., `python3 constructionist_math.py`) and include sample outputs or screenshots when relevant.

## Security & Configuration Tips
- No external dependencies or network access required; keep additions stdlib-only unless justified.
- The model assumes controlled inputs; if you add file or user input parsing, validate operations and guard against unsafe evaluation.
