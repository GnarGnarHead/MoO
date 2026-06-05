# Modulus of One (MoO)

> Heads up: this repo is slop right now.
>
> I was not intending to release it as-is, so expect rough notes, half-aligned
> probes, and terminology drift. The point worth engaging is the core concept:
> MoO studies how structure emerges from `1` through witnessed operations,
> recurrence, branches, and projection.

MoO is a construction-first arithmetic framework that asks what structure
appears when number is built outward from a single certainty: `1`.

It records how rational values become constructible through `+`, `-`, `*`, and
`/`, preserving the paths, motifs, and speculative nodes that appear along the
way.

The aim is to study arithmetic as a construction process, then use external
probes only after the native structure has been recorded.

Primary inspection rule:

```text
The value is not the object.
The witnessed emergence is the object.
```

Graph context is the primary MoO evidence. Value summaries and scouting reports
are useful when read through construction edges, witnesses, and confirmation
status.

Language alignment rule:

```text
MoO studies values through witnessed emergence.
The same value can appear by different witnesses.
The witness matters.
```

Tooling fields such as `aperture`, `retention`, `provenance`, `controls`, and
`baselines` support the theory vocabulary: order, witness, emergence, relation,
branch interaction, and projected form. See `MOO_REALIGNMENT_NOTE.md` and
`BRANCH_GLOSSARY.md` for branch/projection reports.

Philosophically, MoO begins from:

```text
I think, therefore 1.
```

`1` is the only immediate certainty. MoO began as an attempt to prove `2` from
`1`: `2` already requires a previous instance of `1` to be preserved and used
again. That previous instance is once removed from the immediate certainty. In
this framing, `2` is the first structure beyond certainty: infinite distance
from `1`.

MoO begins before positive counting, with the fundamental operator fan of `1`
against itself:

```text
1 + 1 -> 2
1 - 1 -> 0
1 * 1 -> 1
1 / 1 -> 1
```

This is the first asymmetry:

```text
+ expands
- cancels
* preserves
/ preserves
```

The positive counting spine is one branch/projection of this
operator-generated field. Zero and negative values are native to cancellation,
removal, opposition, and crossing. See `FUNDAMENTAL_OPERATOR_FAN_NOTE.md`.

The implementation keeps `Ref(1)` as the only primitive. Everything else is
generated from iterations and relations of `1`. Point, line, triangle, square,
and circle language in these notes is analysis-layer framing over that
construction.

The current saved strict corpora are stage-indexed along the positive spine:
before that selected field rule has iterated twice, there is no confirmed `2`
in the positive-spine corpus. Once `2` and `3` exist, a construction such as
`2 * 3` may produce `6`, but `6` remains speculative until the positive spine
reaches `6`.

Speculative nodes are real MoO nodes with weaker epistemic status than `1` or a
confirmed selected-field iteration. They are inspected as generated structure.
In the current positive-spine corpus, confirmed positive-spine iterations act as
operands; a speculative node becomes available for operation when the selected
confirmation rule later promotes it. MoO speculates from promoted certainty.

Current epistemic order:

```text
Order 1: immediate certainty, 1
Order 2: recurrence of 1 through memory and iteration
Order 3: relational emergence from confirmed recurrence
Order 4: projected form, a stable MoO subset or repeated structure whose
         shadow can be read as a higher form
```

A branch is a repeated witnessed relation that emerges along the recurrence of
`1`. Values are shadows of branches; witnesses show where a value enters a
branch. For example, the even branch is `n -> n+n`, the square branch is
`n -> n*n`, composites are product-branch landings, and the prime branch is
the repeated irreducibility relation where the counting spine is witnessed but
no nontrivial product-branch landing exists.

Recurrence frames, such as Fibonacci/two-memory recurrence or doubling as an
iteration system, are parked as future study. Current branch-lineage tooling
focuses on repeated relations inside the selected field.

## Alignment Layers

MoO results must be read by layer:

```text
positive-spine strict corpus:
  confirmed positive-spine iterations are operands; speculative nodes are
  recorded as real nodes, but not operated on unless later confirmed by the
  selected field rule

exploratory closure:
  older bounded scans that reused speculative nodes as operands; historical
  hypothesis artifacts, not aligned MoO computation

external probes:
  constants, geometry labels, and baselines used only after native structure
  is recorded
```

See `CORE_CLAIMS.md` for the current claim boundary and
`PROJECT_ALIGNMENT_NOTE.md` before interpreting old reports.

## Conceptual Framing

MoO treats “what counts as the same object?” as a first-class choice. The same arithmetic world can be read through multiple explicit lenses (filters):

- **Structure lens**: preserve *construction identity* as distinct edges/events (many edges may land on the same value-point).
- **Value lens**: deduplicate to unique `(src_value, dst_value, op)` links, i.e. a quotient of the full edge-occurrence graph.
- **Grounding lens**: integer points can be “grounded” as `Ref(N)` anchors; integer-valued points produced by `*`/`/` may remain speculative until explicitly grounded via the `+`/`-` backbone.

The structure lens is primary. Value lists, decimal approximations, target probes,
and concept labels are secondary readings over the graph.

MoO is also deliberately “potential-infinity flavored”: every run builds a finite graph, but the integer backbone is extendable by continued iteration from `Ref(1)` (e.g. `--limit N`).

Irrationals are not constructed directly; they appear (if at all) only as limit behavior of rational contexts (e.g. Fibonacci ratio nodes).

Regularization-style readings of divergent objects (e.g. analytic continuation / Ramanujan summation, like the `-1/12` association) are not implemented as runtime semantics; they would be additional analysis lenses, not replacements for the ordinary meanings.

Terminology note: the code and some reports use ordinary graph words such as
`parent`, `child`, and `hub`. These are mechanical report terms for generated
ledger relations: an earlier construction, a resulting construction, or a place
where many recorded events meet. They are not independent objects outside the
iteration of `1`.

## Doc Map

- `DOCS_INDEX.md`: consolidated reading map for the current core,
  research lenses, and quarantined historical notes.
- `MOO_REALIGNMENT_NOTE.md`: canonical language correction: a value is not the
  result by itself; the witnessed emergence of the value is the result.
- `BRANCH_GLOSSARY.md`: canonical branch vocabulary: counting-spine reference,
  even branch, square branch, product-branch landing, prime branch,
  shell-relation branch, interaction branch, witness, field of observation,
  and projected form.
- `BRANCH_FORMALIZATION_NOTE.md`: branch-card standard for naming the repeated
  relation, active field, witness criterion, classical shadow, and weakening
  rule before interpreting a branch probe.
- `FUNDAMENTAL_OPERATOR_FAN_NOTE.md`: canonical correction that MoO begins with
  the four-operator fan of `1` against itself; the positive spine is a branch,
  not the whole strict field.
- `SPAN_TRIAD_SQUARE_EMERGENCE_NOTE.md`: active conceptual note for the early
  ladder from certainty to successor span, additive triad closure, and first
  nontrivial square emergence.
- `RECURRENCE_FRAMES_NOTE.md`: parked future-study note separating recurrence
  frames such as Fibonacci/two-memory recurrence from active branch lineage.
- `CORE_CLAIMS.md`: current claim boundary: what MoO can claim now, what is
  corpus-conditioned, what is candidate-only, and what is not yet earned.
- `VISION.md`: implementation-aligned specification and roadmap.
- `PROJECT_ALIGNMENT_NOTE.md`: canonical layer map separating the
  positive-spine strict corpus, exploratory closure, discarded
  miscommunication artifacts, and external probes.
- `EPISTEMIC_ORDER_NOTE.md`: canonical framing for certainty,
  operator-fan asymmetry, positive-spine confirmation, unconfirmed
  constructions, and promotion by `n`.
- `ORDER4_PROJECTION_PROTOCOL.md`: active protocol for projected forms:
  non-rational constants, shape-like shadows, asymptotic anchors, and
  predictive organization tests.
- `GRAPH_INVARIANTS_PROTOCOL.md`: shared vocabulary for graph-native invariant
  fields such as arrival, witness diversity, operation signature, neighborhood
  overlap, and baseline-adjusted rank.
- `RESEARCH_LENSES.md`: operational scrutiny matrix for strict, exploratory,
  and external-probe claims.
- `GRAPH_CORPUS_NOTE.md`: canonical graph-first storage note for the current
  positive-spine strict corpus, including SQLite schema and smoke-run results.
- `ANALYSIS_TOOL_PROTOCOL.md`: shared rulebook for probes, scouts, lenses, and
  speculative studies; analysis tools must return to graph context.
- `research/`: active scrutiny lenses and strict-corpus research branches,
  grouped by family (`dynamics`, `euler`, `geometry`, `number_theory`,
  `spectral`, and `strict_stage`).
- `archive/`: historical exploratory closure notes, transitional ledgers,
  working logs, and misalignment audits. These preserve leads without letting
  them read as current positive-spine strict corpus claims.
- `out/experiments/dynamics/`: narrowly tracked saved reports,
  preregistration notes, and paired interpretation notes for stage-dynamics and
  Order-4 protocol experiments.
- `out/experiments/geometry/`: narrowly tracked saved reports,
  preregistration notes, and paired interpretation notes for rational shell and
  circle-without-pi experiments, including shell/square component reports,
  prime/Euclid shell scrutiny, shell/prime-branch interaction, and primitive
  Euclid formula-family sweeps.
- `constructionist_math.py`: in-memory MoO graph runtime and demo/export surface (JSON/DOT/stats).
- `strict_stage_moo.py`: positive-spine graph-first strict corpus runner;
  useful but not the full signed operator-fan MoO field.
- `moo_graph_corpus.py`: graph-first SQLite schema/helpers for positive-spine
  strict corpus nodes and edge occurrences.
- `moo_graph_query.py`: inspect graph neighborhoods and high-derivation nodes
  in a positive-spine strict SQLite corpus.
- `moo_research_report.py`, `moo_circle_probe.py`,
  `moo_circle_square_probe.py`, `primitive_euclid_branch_sweep.py`,
  `branch_lineage.py`, `prime_shell_features.py`, and
  `rational_baselines.py`: read-only
  research-layer reporting, circle/shell probing, shell/square component
  co-presence reporting, primitive Euclid formula-family sweeps, branch-lineage auditing,
  rational shell normalization / prime-Euclid features, and rational baseline
  helpers over strict graph corpora.
- `moo_graph_invariants.py`: shared invariant helpers used by research reports
  so probes describe graph evidence with the same vocabulary.
- `moo_observatory.py`: historical exploratory closure-round corpus runner.
- `moo_corpus.py`: stdlib `sqlite3` corpus schema + helpers used by the historical observatory runner.
- `moo_graph_corpus.py`: graph-first SQLite schema/helpers for positive-spine strict corpus nodes and edge occurrences.
- `moo_set_closure.py`: historical set-closure round-stepper that operates on generated speculative values; not aligned MoO computation.
- `moo_targets.py`: shared target definitions + parser used by probe scripts.
- `rational_baselines.py`: stdlib rational-baseline helpers for continued fractions, Farey neighbors, and Stern-Brocot paths.
- `strict_stage_moo.py`: positive-spine graph-first strict corpus runner.
- `moo_graph_query.py`: inspect graph neighborhoods and high-derivation nodes in a positive-spine strict SQLite corpus.
- `moo_research_report.py`: read-only research-layer node dossiers and corpus-wide baseline rankings over positive-spine strict graph corpora.
- `moo_circle_probe.py`: read-only unit-quadratic-shell rational probes over positive-spine strict graph corpora.
- `moo_circle_square_probe.py`: read-only rational shell / square-component
  co-presence report with primitive-triple and Euclid-parameter scrutiny fields.
- `primitive_euclid_branch_sweep.py`: read-only primitive Euclid formula-family
  sweep that records complete, partial, and absent generator/shell/square row
  visibility over positive-spine strict graph corpora.
- `prime_shell_features.py`: stdlib helpers for rational shell integerization,
  primitive triples, prime factor features, and Euclid parameter recovery.
- `out/experiments/dynamics/`: narrowly tracked saved reports, preregistration notes, and paired interpretation notes for stage-dynamics experiments.
- `moo_core_alignment_check.py`: compares a small positive-spine strict run through the in-memory graph runtime and SQLite corpus path.
- `fermat_prime_probe.py`: graph-first analysis probe for odd-prime Fermat branch non-collapse.
- `fermat_little_probe.py`: graph-first analysis probe for Fermat Little return corridors through the certainty anchor.
- `constant_probe.py`: historical stateless closure probe (JSON report; useful only as a comparison artifact).
- `native_emergence_scan.py`: historical exploratory-closure scan for first-seen order, construction records, derivation events, operation signatures, and local density.
- `order_transition_study.py`: stage-indexed inspection of positive-spine confirmation, speculative whole-number constructions, and promotion by the positive-spine rule.
- `stage_indexed_analysis.py`: compact summary pass over saved stage-indexed reports.
- `stage_indexed_moo_ledger.py`: transitional node-summary positive-spine ledger generator; graph-first work should use `strict_stage_moo.py`.
- `residual_emergence_study.py`: historical saved-ledger reranker for exploratory closure.
- `motif_graph_study.py`: historical exploratory-closure first-witness motif study.
- `motif_persistence_study.py`: historical round-prefix motif persistence study.
- `motif_grid_summary.py`: historical bounded replay grid summary.
- `saturation_layer_study.py`: historical saturation-layer comparison over exploratory closure.
- `witness_threshold_study.py`: historical saved-ledger aperture comparison.
- `construction_aperture_study.py`: historical first-witness construction aperture study.
- `concept_branch_study.py`: historical square/triangle cohort probe over saved exploratory ledgers.
- `binding_structure_study.py`: historical binding-profile merger over exploratory ledgers.
- `motif_mass_study.py`: historical motif-mass view over saved exploratory reports.
- `corridor_atlas_study.py`: historical exploratory-closure corridor atlas.
- `stage_indexed_convergence_study.py`: extracts record-improving convergence chains from a saved positive-spine ledger and tests determinant/recurrence structure.
- `emergence_baselines.py`: historical external-probe baseline over exploratory closure values.
- `waterfall_view.py` / `attractor_view.py`: historical analysis/visualization scripts over demo-generated graphs; the attractor name is visualization terminology, not a current dynamics claim.

## Current Implementation

- Runtime object: structure-preserving arithmetic term-DAG/graph (shared nodes, edge history).
- Identity model: one node per reduced rational value (`p/q`); derivation identity is preserved as edge/occurrence identity.
- Grounded layer: unique grounded `Ref(N)` nodes for runtime integer anchors.
- Speculative layer: rationals and integer-valued points that are not yet grounded.
- Operation rule in the current positive-spine corpus: only promoted/grounded
  positive-spine iterations are operands. Speculative nodes are recorded and
  inspected, not operated on.
- Grounding behavior in the current positive-spine corpus: a positive-spine
  whole-number value becomes Order 2 when the positive spine reaches it;
  arithmetic construction alone does not promote it. This corpus does not yet
  implement the full signed operator-fan field.
- Epistemic annotations: every node/report includes `epistemic_order` (`1|2|3`) and `constructible_from_one`; see `EPISTEMIC_ORDER_NOTE.md` for the intended reading.
- Prototype injection: `speculate_ref()` can inject speculative integer claims for demo/testing flows, but those claims are not operands until promoted.

## Project Focus

- Preserve operational provenance while computing value-equivalence classes.
- Inspect graph structure before interpreting values.
- Observe grounded vs speculative dynamics.
- Instrument grounding and construction behavior through JSON/DOT/stats outputs.
- Study external constant probes only after MoO-native construction structure has been recorded.

## Smoke Checks

- `python3 -m py_compile *.py` — basic syntax/type-hint sanity across scripts.
- `python3 constructionist_math.py --limit 10 --stats` — in-memory graph demo build + stats.
- `python3 order_transition_study.py --max-stage 6 --pretty` — stage-indexed check of confirmed iterations versus speculative constructions.
- `python3 moo_core_alignment_check.py --max-stage 6 --pretty` — compare small positive-spine strict output between the in-memory graph and SQLite corpus paths.
- `python3 stage_indexed_analysis.py --report out/experiments/stage_indexed_core_r100.json --pretty` — summarize a saved stage-indexed core run.
- `python3 strict_stage_moo.py --db out/experiments/strict_stage_graph_smoke.sqlite --max-stage 80 --max-abs-p 200 --max-abs-q 200 --max-abs-value 4 --quiet --pretty` — graph-first positive-spine strict corpus.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --summary --pretty` — summarize a saved graph corpus.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --node 34/21 --neighborhood --pretty` — inspect a speculative node, its inputs, and nearby graph structure.
- `python3 moo_graph_query.py --db out/experiments/strict_stage_graph_smoke.sqlite --confirmations --pretty` — list values first seen speculatively and later confirmed by the positive spine.
- `python3 moo_research_report.py --db out/experiments/strict_stage_graph_smoke.sqlite --node 34/21 --pretty` — build a strict graph node dossier beside classical rational baselines.
- `python3 moo_research_report.py --db out/experiments/strict_stage_graph_smoke.sqlite --corpus-baselines --rank-by derivation_events --control denominator --pretty` — rank rational nodes within denominator peer groups without claiming single-node unusualness.
- `python3 moo_circle_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --node 3/4 --pretty` — inspect an exact unit quadratic-shell candidate from a rational parameter.
- `python3 moo_circle_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --only-complete --pretty` — summarize unit-shell candidates whose component nodes are present in the strict corpus.
- `python3 moo_circle_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --pythagorean --max-denominator 40 --pretty` — scan existing rational node pairs for exact quadratic-shell relations.
- `python3 moo_circle_square_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --max-denominator 20 --max-abs-value 5 --require-complete-family --pretty` — scan rational shell/square co-presence candidates with primitive-triple, prime-factor, and Euclid-parameter fields.
- `python3 primitive_euclid_branch_sweep.py --db out/experiments/strict_stage_graph_smoke.sqlite --max-m 8 --pretty` — sweep target primitive Euclid formula-family rows and record complete, partial, or absent row visibility.
- `python3 branch_lineage.py --db out/experiments/strict_stage_graph_smoke.sqlite --branch square --limit 20 --pretty` — audit a repeated MoO branch relation such as `n -> n*n`, separating branch participation from retained edge rows.
- `python3 fermat_prime_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --primes 3,5 --min-base 2 --max-base 5 --top-k 3 --pretty` — inspect Fermat odd-prime non-collapse against a graph corpus.
- `python3 fermat_little_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --max-modulus 12 --max-base 8 --top-k 5 --pretty` — inspect Fermat Little return corridors; base `1` is included by default as the certainty anchor.
- `python3 stage_indexed_moo_ledger.py --max-stage 1000 --max-abs-p 1000 --max-abs-q 1000 --max-abs-value 4 --pretty` — bounded positive-spine ledger with speculative rational nodes.

## Command Examples

- `python3 constructionist_math.py` — runs the default demo and prints JSON and DOT outputs.
- `python3 constructionist_math.py '1/(1+1)'` — evaluates a minimal “MoO language” expression.
- `python3 constructionist_math.py --fibonacci 8 --maps` — builds an aligned Fibonacci-focused graph with recurrence terms, ratio nodes, and subtraction back-links. Cassini-style second-step identities require `--allow-speculative-operands` and are historical exploratory behavior.
- `python3 constructionist_math.py --write-maps out/fib --fibonacci 8 --view value` — writes the standard map artifacts plus a `*.fibonacci.json` report.
- `python3 moo_observatory.py --db out/moo_corpus.sqlite --to-round 8 --targets all` — historical exploratory closure runner; useful only as a comparison artifact.

## Analysis Views

- `python3 waterfall_view.py --n-min 1 --n-max 20` — normalized waterfall (`x=k/N`, `y=N`, `z=mass/m(0)`) with in-browser slice controls.
- `python3 attractor_view.py --n-min 1 --n-max 20` — historical heatmap over `N x v` for `inflow_resolve`, `mass`, `pull_ratio`, and `rank_inflow`; the script name predates the current attractor guardrails.

See [VISION.md](VISION.md) for the implementation-aligned specification and roadmap split.

## Compute Modes

- **Positive-spine strict corpus**: compute only with confirmed positive-spine
  iterations as operands. Speculative results are recorded as graph nodes and
  edge occurrences, but they are inspected rather than operated on until the
  selected confirmation rule confirms them. This is useful graph-first storage,
  but it is not the full signed operator-fan MoO field.
- **Exploratory closure**: older bounded scans reused all retained generated values as operands, including speculative nodes. These runs are historical hypothesis artifacts; they are not aligned MoO computation.
- **External probes**: constants, geometry labels, and baselines used to inspect already-generated structure. Probe-selected points matter only through shared structure, not approximation alone.

Across all modes, the primary method of inspection is graph inspection: nodes,
construction edges, repeated paths, neighborhoods, and confirmation transitions.
