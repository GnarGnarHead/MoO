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
- `NEXT_STEPS.md`: obvious pause-point note with current state, saved artifacts, and recommended next experiments.
- `VISION.md`: implementation-aligned specification + roadmap (what exists vs what’s aspirational).
- `TRANSCENDENTAL_ATTRACTORS_NOTE.md`: research note on rational closure, attractor behavior, and convergence toward constants.
- `RELATED_WORKS_NOTE.md`: exploratory literature map for rational trees, continued fractions, integer complexity, and experimental-math baselines.
- `RESEARCH_TOOLS_NOTE.md`: separates MoO-native observables from external confirmation tools.
- `RESIDUAL_EMERGENCE_NOTE.md`: first target-blind residual study after filtering the arithmetic skeleton.
- `MOTIF_GRAPH_NOTE.md`: first parent-motif study over the target-blind ledger.
- `MOTIF_PERSISTENCE_NOTE.md`: round-prefix persistence study for parent hubs, parent pairs, operation motifs, and inspected-vs-control concentration.
- `SATURATION_LAYER_NOTE.md`: compares the `n=5` emergence layer with the saturated `n=6` bounded universe.
- `CONSTRUCTION_CENTERS_NOTE.md`: names the emergent rational/motif centers and separates evidence from speculation.
- `CAMBRIDGE_ARC_MOTIFS_NOTE.md`: exploratory bridge from Hardy-Littlewood/Ramanujan-style rational arc methods to MoO motif hinges, with a clearly speculative reading.
- `PRIME_HARMONICS_NOTE.md`: speculative research note (analysis-layer, not runtime semantics).
- `moo_observatory.py`: persistent “observatory” runner (incremental closure-round corpus + probe logs).
- `moo_corpus.py`: stdlib `sqlite3` corpus schema + helpers used by `moo_observatory.py`.
- `moo_set_closure.py`: shared set-closure round-stepper used by `constant_probe.py` and `moo_observatory.py`.
- `moo_targets.py`: shared target definitions + parser used by probe scripts.
- `constant_probe.py`: stateless closure probe (JSON report; useful for quick ad-hoc checks).
- `native_emergence_scan.py`: target-blind MoO-native scan for first-seen order, witnesses, derivation events, operation signatures, and local density.
- `residual_emergence_study.py`: reranks a saved native ledger after filtering skeleton hubs and normalizing by round/denominator bucket.
- `motif_graph_study.py`: studies first-witness parent hubs, parent-pair motifs, operation motifs, and inspected approximant ancestry.
- `motif_persistence_study.py`: slices a saved first-witness ledger by round prefix to test motif persistence without recomputing closure.
- `motif_grid_summary.py`: summarizes the saved bounded replay grid for motif robustness and path sensitivity.
- `saturation_layer_study.py`: compares the penultimate emergence layer with the final saturated layer in a saved ledger.
- `emergence_baselines.py`: lightweight local report comparing closure approximants to continued-fraction, rational-tree, Farey, and integer-complexity baselines.
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
- Study when constants become visible as rational attractors under finite closure from `1`.

## Smoke Checks

- `python3 -m py_compile *.py` — basic syntax/type-hint sanity across scripts.
- `python3 constructionist_math.py --limit 10 --stats` — demo build + stats + acceptance checks.
- `python3 constant_probe.py --rounds 3 --targets pi,e,sqrt2 --top-k 1 --pretty` — quick closure probe (stateless).
- `python3 native_emergence_scan.py --rounds 5 --top-k 8 --pretty` — target-blind local emergence scan.
- `python3 residual_emergence_study.py --report out/experiments/native_r5_full.json --top-k 12 --pretty` — residual study over a saved native ledger.
- `python3 motif_graph_study.py --report out/experiments/native_r5_full.json --top-k 12 --pretty` — parent-motif study over a saved native ledger.
- `python3 motif_persistence_study.py --report out/experiments/native_r5_full.json --top-k 12 --pretty` — round-prefix motif persistence study over a saved native ledger.
- `python3 motif_grid_summary.py --pretty` — summarize the saved `3 x 3` bounded replay grid.
- `python3 saturation_layer_study.py --report out/experiments/native_r6_full.json --top-k 12 --pretty` — compare the `n=5` emergence layer against the saturated `n=6` layer.
- `python3 emergence_baselines.py --rounds 5 --targets pi,e,sqrt2,phi,ln2 --compact --pretty` — local baseline report for best approximants.
- `python3 moo_observatory.py --db out/moo_smoke.sqlite --to-round 3 --targets all` — persistent corpus extension + probes.

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
