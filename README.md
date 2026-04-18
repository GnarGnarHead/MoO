# Modulus of One (MoO)

MoO is a constructionist arithmetic prototype that starts from one primitive grounded node, `Ref(1)`, and builds a relational arithmetic graph using `+`, `-`, `*`, and `/`.

## Conceptual Framing

MoO treats “what counts as the same object?” as a first-class choice. The same arithmetic world can be read through multiple explicit lenses (filters):

- **Structure lens**: preserve *construction identity* as distinct edges/events (many edges may land on the same value-point).
- **Value lens**: deduplicate to unique `(src_value, dst_value, op)` links, i.e. a quotient of the full edge-occurrence graph.
- **Grounding lens**: integer points can be “grounded” as `Ref(N)` anchors; integer-valued points produced by `*`/`/` may remain speculative until explicitly grounded via the `+`/`-` backbone.

MoO is also deliberately “potential-infinity flavored”: every run builds a finite graph, but the integer backbone is extendable by continued iteration from `Ref(1)` (e.g. `--limit N`).

Irrationals are not constructed directly; they appear (if at all) only as limit behavior of rational contexts (e.g. Fibonacci ratio nodes).

Regularization-style readings of divergent objects (e.g. analytic continuation / Ramanujan summation, like the `-1/12` association) are not implemented as runtime semantics; they would be additional analysis lenses, not replacements for the ordinary meanings.

## Doc Map

- `constructionist_math.py`: core runtime (`Graph`, `Node`), demo, exports (JSON/DOT/stats).
- `VISION.md`: implementation-aligned specification + roadmap (what exists vs what’s aspirational).
- `PRIME_HARMONICS_NOTE.md`: speculative research note (analysis-layer, not runtime semantics).
- `moo_observatory.py`: persistent “observatory” runner (incremental closure-round corpus + probe logs).
- `moo_corpus.py`: stdlib `sqlite3` corpus schema + helpers used by `moo_observatory.py`.
- `constant_probe.py`: stateless closure probe (JSON report; useful for quick ad-hoc checks).
- `waterfall_view.py` / `attractor_view.py`: analysis/visualization scripts over demo-generated graphs.

## Current Implementation

- Runtime object: structure-preserving arithmetic term-DAG/graph (shared nodes, edge history).
- Identity model: one node per reduced rational value (`p/q`); derivation identity is preserved as edge/occurrence identity.
- Grounded layer: unique grounded `Ref(N)` nodes for grounded integers.
- Speculative layer: rationals and integer-valued points that are not yet grounded.
- Grounding behavior: a point can be promoted to a grounded `Ref(N)` anchor when the integer backbone explicitly constructs it.
- Epistemic annotations: every node/report includes `epistemic_order` (`1|2|3`) and `constructible_from_one`.
- Prototype injection: `speculate_ref()` can inject speculative integer claims for demo/testing flows.

## What It Is Not

- Not a replacement for established mathematical foundations.
- Not a geometric/dimensional embedding (any “space” language here is interpretive).
- Not a proof that classical arithmetic is invalid.

## Project Focus

- Preserve operational provenance while computing value-equivalence classes.
- Observe grounded vs speculative dynamics.
- Instrument grounding and construction behavior through JSON/DOT/stats outputs.

## Command Examples

- `python3 constructionist_math.py` — runs the default demo and prints JSON and DOT outputs.
- `python3 constructionist_math.py '1/(1+1)'` — evaluates a minimal “MoO language” expression.
- `python3 constructionist_math.py --fibonacci 8 --maps` — builds a Fibonacci-focused graph with recurrence terms, ratio nodes, subtraction back-links, and Cassini identities.
- `python3 constructionist_math.py --write-maps out/fib --fibonacci 8 --view value` — writes the standard map artifacts plus a `*.fibonacci.json` report.
- `python3 moo_observatory.py --db out/moo_corpus.sqlite --to-round 8 --targets all` — incrementally extends a persistent closure-round corpus and logs probe results.

## Analysis Views

- `python3 waterfall_view.py --n-min 1 --n-max 20` — normalized waterfall (`x=k/N`, `y=N`, `z=mass/m(0)`) with in-browser slice controls.
- `python3 attractor_view.py --n-min 1 --n-max 20` — attractor heatmap over `N x v` for `inflow_resolve`, `mass`, `pull_ratio`, and `rank_inflow`.

See [VISION.md](VISION.md) for the implementation-aligned specification and roadmap split.
