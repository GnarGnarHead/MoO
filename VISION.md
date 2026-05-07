# Modulus of One (MoO)
## Vision and Prototype Specification
Version: 0.2-docs-aligned
Status: Implementation-aligned design note

---

## 1. Purpose

This document defines the current MoO implementation layers, separates them from
philosophical intent, and states a conservative roadmap. `constructionist_math.py`
is the in-memory MoO graph runtime and demo/export surface. `strict_stage_moo.py`
and `moo_graph_corpus.py` provide the graph-first SQLite corpus path for larger
strict-stage runs.

The graph is the primary method of inspection. A rational value, constant probe,
or concept label is only meaningful after its construction edges and graph
neighborhood have been inspected.

It is a documentation alignment pass, not a claim of a new mathematical foundation.

## 1.1 Repo Map (What To Read)

- `constructionist_math.py`: in-memory MoO graph (`Graph`, `Node`, `Edge`), demo generators, JSON/DOT exports.
- `moo_set_closure.py`: historical exploratory set-closure round stepper; it reuses generated speculative values and is not aligned MoO computation.
- `moo_targets.py`: shared target definitions + parser (pi/e/sqrt2/… and `all` expansion).
- `constant_probe.py`: historical stateless exploratory set-closure probe (JSON report for external constant matches).
- `moo_corpus.py`: stdlib `sqlite3` schema/helpers for historical exploratory set-closure corpora.
- `moo_observatory.py`: historical incremental set-closure runner that appends to a corpus and logs probe outcomes.
- `moo_graph_corpus.py`: graph-first SQLite schema/helpers for aligned strict-stage MoO nodes and edge occurrences.
- `strict_stage_moo.py`: canonical graph-first strict-stage MoO runner.
- `moo_graph_query.py`: graph inspection CLI for strict-stage MoO SQLite corpora.
- `moo_core_alignment_check.py`: small-run agreement check between the in-memory graph runtime and SQLite corpus path.
- `fermat_prime_probe.py`: graph-first analysis probe for odd-prime Fermat branch non-collapse.
- `fermat_little_probe.py`: graph-first analysis probe for Fermat Little return corridors; base `1` remains the certainty anchor.
- `order_transition_study.py`: stage-indexed inspection of core-loop confirmation versus speculative constructions.
- `stage_indexed_analysis.py`: compact summary pass over saved stage-indexed reports.
- `stage_indexed_moo_ledger.py`: bounded strict-stage MoO ledger generator preserving speculative rational outputs and first construction records.
- `stage_indexed_convergence_study.py`: structure-first convergence-chain study over a saved strict-stage MoO ledger.
- `waterfall_view.py` / `attractor_view.py`: visualization scripts over `constructionist_math.demo(...)` graphs.
- `README.md`: project overview + command map.
- `DOCS_INDEX.md`: consolidated reading map for canonical, active, speculative, and historical notes.
- `CORE_CLAIMS.md`: current claim boundary for what MoO can say, cannot say, and must keep corpus-conditioned.
- `ORDER4_PROJECTION_PROTOCOL.md`: protocol for non-operational projected objects inferred from stable graph families.
- `PROJECT_ALIGNMENT_NOTE.md`: canonical layer map separating strict-stage MoO, exploratory closure, purged miscommunication artifacts, and external probes.
- `PROJECT_MISALIGNMENT_AUDIT.md`: diagnostic note explaining where the repository still conflicts with the resolved MoO framing and why.
- `ANALYSIS_TOOL_PROTOCOL.md`: shared protocol for probes, scouts, lenses, and speculative studies so external analysis returns to graph context.
- `GRAPH_CORPUS_NOTE.md`: canonical graph-first storage note for aligned MoO.
- `EPISTEMIC_ORDER_NOTE.md`: canonical order framing: `1` as the only certainty, confirmed core-loop iterations as second order, and unconfirmed or relational constructions as third order.
- `STAGE_INDEXED_UNIVERSE_NOTE.md`: core-loop rule for when positive whole numbers enter the MoO universe and when speculative constructions remain unconfirmed.
- `STAGE_INDEXED_R100_NOTE.md`: first compact study of the strict `n=100` stage-indexed core run.
- `STAGE_INDEXED_MOO_LEDGER_NOTE.md`: transitional node-summary strict-stage run; useful evidence, but graph-first storage is now canonical.
- `CONVERGENCE_STRUCTURE_NOTE.md`: first convergence-chain study showing why approximating points matter only through shared structure.
- `TRANSCENDENTAL_ATTRACTORS_NOTE.md`: research note separating rational closure from external constant probes.
- `WITNESS_THRESHOLD_NOTE.md`: audit showing how value aperture changes witness availability and construction timing.
- `CONSTRUCTION_APERTURE_NOTE.md`: first corpus-wide metric for first-witness construction aperture.
- `CONCEPT_BRANCHES_NOTE.md`: first concept-family probe, separating shape anchors such as `3` and `4` from generated families.
- `PRIME_HARMONICS_NOTE.md`: speculative analysis note (not runtime semantics).
- `PRIME_FACTOR_AND_CONJECTURE_PROBES_NOTE.md`: speculative analysis note for prime factors, Sophie Germain/twin-prime/Goldbach corridors, Euler-product pi shadows, and Godel-style coding.
- `FERMAT_PRIME_PROBE_NOTE.md`: speculative Fermat-prime non-collapse probe over graph branch structure.
- `FERMAT_LITTLE_PROBE_NOTE.md`: speculative Fermat Little return-corridor probe preserving self-reference through `1`.
- `GEOMETRIC_PROBES_NOTE.md`: speculative analysis note for geometric constraint probes over emergent arithmetic patterns.
- `FOURIER_ANALYSIS_LENS_NOTE.md`: speculative analysis note treating Fourier's body of work as projection discipline over MoO edge structure.
- `SPECTRAL_SCOUT_NOTE.md`: speculative analysis-tool concept for using edge-derived spectral signatures to scout graph neighborhoods for inspection.
- `NULL_GEODESIC_LENS_NOTE.md`: speculative analysis-lens note for nontrivial construction paths that collapse under a chosen projection.
- `SPECTRAL_NULL_RELATED_WORKS_NOTE.md`: related-works pass for spectral scouting and null-like paths, emphasizing edge-flow and Hodge-style analysis.

---

## 2. Scope and Positioning

MoO is a constructionist epistemic experiment built around one primitive certainty event represented as `1`.

### 2.1 Lenses / Identification (Explicit “Filters”)

MoO takes the “only if you specify in what sense you are identifying them” move literally: the runtime keeps multiple coexisting identifications over the same constructed state.

- **Structure identity**: derivation nodes remain distinct (provenance is preserved).
- **Value identity**: one node exists per reduced rational value class `(p, q)`.
- **Construction identity**: distinct constructions are preserved as distinct edges/events landing on that value node.
- **Anchor identity**: grounded `Ref(N)` anchors are unique; grounding is represented by promoting the value-node `(N,1)` to status `G`.

These are not competing truths; they are different projections of the same graph.

It is not:

- a replacement for ZFC/Peano-style foundations,
- a geometric or dimensional embedding framework,
- a proof that classical arithmetic is invalid.

The current code is a computational model of relational arithmetic construction with explicit edge-history (construction identity) over canonical value nodes.

### 2.2 Philosophical Seed: The Failed Attempt To Prove 2

The motivating question behind MoO is the failed attempt to prove `2` from `1`.
The seed is:

```text
I think, therefore 1.
```

`1` is the only immediate certainty. To reach `2`, the system must preserve a
previous instance of `1` and use it again. That previous instance is once
removed from the immediate certainty. A Cartesian-demon doubt can attack that
memory, so certainty ends at `1`.

In this philosophical reading, `2` is infinite distance from `1`: not because
the runtime cannot construct the value `2`, but because the certainty of `1`
does not transfer across iteration.

The runtime claim is narrower: `Ref(1)` is the only primitive, and every other
value is generated from operations over already-generated expressions of `1`.
Later shape language should be read as analysis-layer interpretation over the
constructed arithmetic field:

```text
1        -> point / certainty / center
2        -> first failed proof attempt / line-like relation / infinite distance
3        -> triangle / threefold constraint
4        -> square / fourfold constraint
infinity -> unbounded extension / rotation-limit reading
```

The "infinity as 2" idea should be treated as philosophical, not runtime
identity: `2` is the first move beyond immediate certainty, and that move is
already infinitely distant from `1`.

MoO is also stage-indexed. At core-loop stage `n`, the confirmed core-loop
iterations are `1..n`. A construction can produce a future whole
number before it is confirmed. For example, once `2` and `3` exist, `2 * 3` can
produce `6` as a speculative construction; `6` becomes Order 2 only when the
core loop reaches `6`.

---

## 3. Current Mathematical Object

MoO currently implements:

- A single primitive grounded node (`Ref(1)`),
- Arithmetic construction edges (`+`, `-`, `*`, `/`) between permitted operands,
- Canonical value nodes: one node per reduced rational value (`p/q`),
- A shared edge-history representing derivations (many constructed expressions of `1` can land on the same value node),
- Grounding/promotion of integer value nodes into `Ref(N)` anchors when the integer backbone explicitly constructs them.

This produces a structure-preserving relational term graph with explicit value projection, rather than a free algebra.

The graph is not an optional visualization of the result. It is the result that
MoO inspects. Value projection is a convenience view over that graph.

When the implementation or analysis scripts use generic operands such as `a`
and `b`, they should be read as shorthand for already-generated constructions
from `1`, not as independent primitive numbers.

### 3.1 Infinity Stance (Potential, Not Completed)

MoO does not assume a completed infinite totality at runtime. Every graph is
finite and parameterized by budgets (`limit`, `max_nodes`, `max_depth`,
`operation_budget`). In the philosophical framing, the move from `1` to `2` is
already infinite distance from `1` because it depends on memory. In the runtime
framing, "infinity" also appears as an extendable frontier: once the system
accepts iteration, it can continue applying `+1` / `-1` outward from `Ref(1)` to
generate more integers.

MoO also does not treat divergent sums as having ordinary numeric values. If you want regularization-style assignments (e.g. analytic continuation / Ramanujan summation, like the `-1/12` association), that belongs as an additional analysis lens with explicit rules, not as a replacement for ordinary meanings.

### 3.2 External Constant Probes And Projected Anchors

MoO does not construct completed non-rational constants directly. Current
graph-first probes ask which already-recorded speculative rational nodes are
selected by external constant tests after finite construction from `1`. Older
set-closure reports remain historical comparison artifacts.

This is a research lens, not a runtime axiom: constants such as `pi`, `e`,
`sqrt2`, `phi`, and `ln2` are external targets used to test the ordering of
emergent rationals. The MoO-native structure is the first-seen round,
construction witness, derivation multiplicity, and speculative-node ancestry.
Approximation error belongs to the external probe layer.

Order-4 projected objects are allowed only as non-operational analysis anchors
inferred from exact graph families by explicit projection rules. They are not
runtime nodes, operands, confirmed facts, theorems, or completed objects inside
strict MoO.

Use the category `non-rational projected constants` for anchors such as:

```text
pi and e:
  transcendental

sqrt2 and phi:
  algebraic irrational
```

See `TRANSCENDENTAL_ATTRACTORS_NOTE.md` for the current observation and research
program, and `ORDER4_PROJECTION_PROTOCOL.md` for projected-object rules.

### 3.3 Geometric Probes as Analysis Layer

Circle, square, area, diagonal, and polygon-limit language is not part of the
current runtime semantics. These ideas belong to an analysis layer that filters
already-emergent arithmetic structure by explicit constraint signatures.

The intended direction is:

```text
runtime rational emergence
-> constraint signature
-> speculative geometric probe subset
-> possible concept branch
-> possible Order-4 projected invariant if held-out graph evidence supports it
```

See `GEOMETRIC_PROBES_NOTE.md` for guardrails and first probe families.

---

## 4. Core Runtime Model (Current Implementation)

### 4.1 Node classes

- Grounded nodes (`status == "G"`): integer anchor references `Ref(N)`.
- Speculative nodes (`status == "S"`): non-grounded value points (including non-integer rationals and integer-valued points not yet grounded), plus special undefined nodes like division-by-zero.

### 4.1.1 Taxonomy mapping (one screen)

MoO uses a few overlapping tags; this block is the intended alignment in the current implementation:

- `status`:
  - `G`: grounded integer anchor `Ref(N)`.
  - `S`: speculative derivation/claim node.
- `metadata["tier"]` (conceptual tier label):
  - `1`: the primitive `Ref(1)` anchor.
  - `2`: grounded positive integer anchors `Ref(N)` for `N > 1`.
  - `3`: speculative/analysis-layer nodes, relational/removal integer anchors such as `0` and negatives, rationals, integer-valued points not yet grounded, and undefined nodes like division-by-zero.
- `epistemic_order` (reported, derived):
  - `1`: `Ref(1)` (primitive certainty event).
  - `2`: grounded positive `Ref(N)` for `N > 1` (confirmed core-loop iteration; not immediate certainty).
  - `3`: speculative nodes and relational/removal values, including `0` and negative runtime refs.
- `constructible_from_one` (reported, evidence tag):
  - `True` for grounded anchors.
  - `True` for speculative nodes that have at least one witnessed derivation edge whose inputs are all constructible.
  - `False` for isolated/injected speculative claims with no witness edge yet (e.g. `speculate_ref(n)` before it participates in any construction).

### 4.2 Graph-level identity and value projection

The graph enforces identity operationally via:

- `nodes_by_int`: one grounded `Ref(N)` per grounded integer,
- `nodes_by_value`: one node per reduced rational value `(p, q)`,
- `value_classes`: explicit value projection (in the current semantics this is 1:1 with value-nodes).

### 4.3 Edge history

Edges preserve operation provenance (`op`, `inputs`, `output`, metadata). In value-centric semantics, the “spiderweb” is primarily the edge history.

Structural preservation is primary; numeric identity is represented by canonical value nodes, and emergence is represented by edge history (not duplicated nodes).

Therefore, the basic evidence unit is:

```text
node + incoming construction edges + local graph neighborhood
```

not a bare value.

---

## 5. Primitive, Grounding, and Injection

### 5.1 Primitive

`Ref(1)` is seeded at graph initialization and is the only first-class primitive.

### 5.2 Grounding rule

Positive integers greater than `1` become grounded only when the core loop
explicitly promotes that iteration of `1`. Arithmetic construction can produce
an integer-valued node first, but that node remains speculative until the core
loop reaches it. Zero and negative values are relational/removal constructions,
not core-loop confirmations.

### 5.3 Speculative injection path (`speculate_ref`)

The in-memory runtime includes `speculate_ref(n)` which can inject speculative integer points directly. This is used in demo flows to exercise grounding/promotion behavior.

Therefore, the current implementation is not a fully pure derivational model strictly from operations on `1`.

---

## 6. Operational Semantics (Current)

### 6.1 Addition and subtraction

- Default aligned mode permits only confirmed core-loop operands.
- Exact integer output is recorded as the canonical value node.
- If that whole number has already been promoted by the core loop, the output is grounded.
- Otherwise the output remains speculative until later core-loop promotion.

### 6.2 Multiplication

- Default aligned mode permits only confirmed core-loop operands.
- Exact output is recorded as a canonical value node.
- Integer outputs become grounded only if the corresponding core-loop `Ref(N)` already exists; otherwise they remain speculative integer claims.

### 6.3 Division

- Default aligned mode permits only confirmed core-loop operands.
- Division by zero returns a reusable dedicated speculative node.
- Non-integer outcomes are represented as speculative rational nodes with reduced `p/q` value metadata.
- Integer outcomes follow the same grounded-if-existing, otherwise speculative-claim rule.

Historical exploratory mode can be enabled in the in-memory runtime with
`allow_speculative_operands=True` / `--allow-speculative-operands`. That mode is
kept for comparison with older reports; it is not aligned MoO computation.

---

## 7. Identity and Collapse Status

Identity and grounding behavior is implemented operationally, but not yet axiomatized or formally proven as a mathematical system.

Current operational rules:

- one node per reduced rational value (`p/q`),
- unique grounded identity for each grounded integer (`Ref(N)`),
- grounding as promotion of the integer value-node `(N,1)` to status `G`.

Derivationally distinct equal-valued structures are preserved as distinct edges/events.

---

## 8. Interface and Outputs

Primary inspection interfaces (stable in spirit, preserve signatures/shape):

- `to_json()` / `to_jsonable()` for machine-readable graph state,
- `to_dot()` for graph visualization,
- `to_resolve_dot()` and `resolve_events()` for resolution/grounding diagnostics (under value-centric semantics, most emergence is observed through edges).
- node/report epistemic annotations: `epistemic_order` and `constructible_from_one`,
- `stats()` / field-map helpers for aggregate diagnostics.

For strict-stage corpus work, `moo_graph_query.py` is the primary inspection
tool because it reads nodes together with construction edges and neighborhoods.

`epistemic_order` is intended as a ranked stance on certainty:

- Order 1: `1`, the only certainty.
- Order 2: core-loop iterations confirmed from `1`.
- Order 3: unconfirmed or relational constructions from iterations of `1`, including fractions, zero/negative removals, and positive whole-number constructions not yet confirmed by `n`.

Order 3 nodes are still MoO nodes. Their speculative status is about certainty
and confirmation, not about whether they belong to the graph. They are
speculated on and inspected, but not operated on unless the core loop later
confirms them. Once promoted by confirmation, they may participate in further
speculation. MoO does not speculate on speculations.

Example:

```text
3 * 2 produces 6.
If n < 6, 6 is an unconfirmed construction: Order 3.
Once n confirms 6 as a whole-number iteration of 1, 6 becomes Order 2.
```

See `EPISTEMIC_ORDER_NOTE.md` for the canonical framing.

For a low-compute inspection of stage confirmation versus speculative
construction, run:

```sh
python3 order_transition_study.py --max-stage 6 --pretty
```

This should be kept distinct from the older bounded closure scans. The strict
stage-indexed core records speculative nodes but does not operate on them.
Older exploratory closure scripts reused all retained generated values as
operands, including speculative rationals and speculative future whole numbers.
Those scripts remain historical hypothesis artifacts, but they are not aligned
MoO computation.

---

## 9. Conceptual Roadmap vs Current Implementation

### 9.1 Current

- Structure-preserving arithmetic graph with shared nodes,
- Canonical value nodes with explicit edge-history,
- Speculative injection supported (`speculate_ref`),
- No formal symmetry or invariant framework.

### 9.2 Conceptual direction

- Explicit formalization of the current structure-preserving identity model,
- Explicit invariant detection and reporting,
- Formal axiomatization/proof-oriented encoding of operational rules.

Roadmap items are targets, not implemented guarantees.

---

## 10. Open Formalization Questions

The following remain open at the formal level:

1. Exact axiomatization of identity across grounded and speculative strata.
2. Conditions for collapse versus persistent structural distinction.
3. Invariants that should be preserved under rewiring/resolve operations.
4. Notion of independence within the current relational graph.
5. Criteria for proving consistency and completeness of the operational calculus.

---

## 11. Development Status

MoO is currently:

- A conceptual and computational exploration,
- An implementation-backed runtime with explicit operational behavior,
- Not yet a formally proved alternative algebraic foundation.

Recommended public positioning:

> An epistemic and structural exploration of arithmetic construction from a single certainty primitive, implemented as a structure-preserving relational term graph.

Avoid claims implying geometric, dimensional, or foundational replacement narratives.
