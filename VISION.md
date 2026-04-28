# Modulus of One (MoO)
## Vision and Prototype Specification
Version: 0.2-docs-aligned
Status: Implementation-aligned design note

---

## 1. Purpose

This document defines what MoO currently implements in `constructionist_math.py`, separates that from philosophical intent, and states a conservative roadmap.

It is a documentation alignment pass, not a claim of a new mathematical foundation.

## 1.1 Repo Map (What To Read)

- `constructionist_math.py`: canonical runtime graph (`Graph`, `Node`, `Edge`), demo generators, JSON/DOT exports.
- `moo_set_closure.py`: shared set-closure “round stepper” used by probe scripts (set-of-rationals closure rounds).
- `moo_targets.py`: shared target definitions + parser (pi/e/sqrt2/… and `all` expansion).
- `constant_probe.py`: stateless set-closure probe (JSON report for emergence of rational approximants).
- `moo_corpus.py`: stdlib `sqlite3` schema/helpers for persistent set-closure corpora.
- `moo_observatory.py`: incremental set-closure runner that appends to a corpus and logs probe outcomes.
- `waterfall_view.py` / `attractor_view.py`: visualization scripts over `constructionist_math.demo(...)` graphs.
- `README.md`: project overview + command map.
- `TRANSCENDENTAL_ATTRACTORS_NOTE.md`: research note on rational closure and constant-directed attractor behavior.
- `PRIME_HARMONICS_NOTE.md`: speculative analysis note (not runtime semantics).

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

---

## 3. Current Mathematical Object

MoO currently implements:

- A single primitive grounded node (`Ref(1)`),
- Closure under arithmetic operations (`+`, `-`, `*`, `/`) at the graph level,
- Canonical value nodes: one node per reduced rational value (`p/q`),
- A shared edge-history representing derivations (many derivations can land on the same value node),
- Grounding/promotion of integer value nodes into `Ref(N)` anchors when the integer backbone explicitly constructs them.

This produces a structure-preserving relational term graph with explicit value projection, rather than a free algebra.

### 3.1 Infinity Stance (Potential, Not Completed)

MoO does not assume a completed infinite totality at runtime. Every graph is finite and parameterized by budgets (`limit`, `max_nodes`, `max_depth`, `operation_budget`). “Infinity” appears only as an extendable frontier: you can always continue iterating `+1` / `-1` outward from `Ref(1)` to ground more integers.

MoO also does not treat divergent sums as having ordinary numeric values. If you want regularization-style assignments (e.g. analytic continuation / Ramanujan summation, like the `-1/12` association), that belongs as an additional analysis lens with explicit rules, not as a replacement for ordinary meanings.

### 3.2 Constant Visibility Through Rational Closure

MoO does not construct transcendental constants directly. The current set-closure
probes instead ask when rational approximants to constants become visible under
finite construction from `1`.

This is a research lens, not a runtime axiom: constants such as `pi`, `e`, and
`ln2` are external targets used to measure the ordering of emergent rationals.
The interesting structure is the first-seen round, construction witness,
derivation multiplicity, and approximation error of each rational shadow.

See `TRANSCENDENTAL_ATTRACTORS_NOTE.md` for the current observation and research
program.

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
  - `2`: grounded integer anchors `Ref(N)` for `N != 1`.
  - `3`: speculative/analysis-layer nodes (rationals, integer-valued points not yet grounded, undefined nodes like division-by-zero).
- `epistemic_order` (reported, derived):
  - `1`: `Ref(1)` (primitive certainty event).
  - `2`: other grounded `Ref(N)` (iteration/memory-dependent certainty).
  - `3`: speculative nodes.
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

---

## 5. Primitive, Grounding, and Injection

### 5.1 Primitive

`Ref(1)` is seeded at graph initialization and is the only first-class primitive.

### 5.2 Grounding rule

Other integers become grounded when construction paths produce them (notably via grounded `+` / `-` paths in the current workflow).

### 5.3 Prototype injection path (`speculate_ref`)

The prototype includes `speculate_ref(n)` which can inject speculative integer points directly. This is used in demo flows to exercise grounding/promotion behavior.

Therefore, the current implementation is not a fully pure derivational model strictly from operations on `1`.

---

## 6. Operational Semantics (Current)

### 6.1 Addition and subtraction

- `G,G` inputs: normalize to integer, ensure grounded `Ref(N)` exists, and produce a derivation node.
- Mixed/speculative inputs with known exact values: compute exact rational result and keep derivation structure; integer results can resolve to `Ref(N)` anchors.
- Mixed/speculative inputs with known exact values: compute exact rational result and keep derivation structure; integer results can be grounded when the integer backbone explicitly constructs them.
- Unknown speculative values: create speculative node, optionally with `potential_val` when inferable.

### 6.2 Multiplication

- Uses exact rational arithmetic when values are known.
- Integer outputs become grounded only if corresponding `Ref(N)` already exists; otherwise remain speculative integer claims.
- Includes zero-annihilation behavior for partially unknown inputs where one side is known zero.

### 6.3 Division

- Division by zero returns a reusable dedicated speculative node.
- Non-integer outcomes are represented as speculative rational nodes with reduced `p/q` value metadata.
- Integer outcomes follow the same grounded-if-existing, otherwise speculative-claim rule.

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
- `to_resolve_dot()` and `resolve_events()` for legacy resolution/grounding diagnostics (under value-centric semantics, most emergence is observed through edges).
- node/report epistemic annotations: `epistemic_order` and `constructible_from_one`,
- `stats()` / field-map helpers for aggregate diagnostics.

`epistemic_order` is intended as a ranked stance on certainty:

- Order 1: the primitive `Ref(1)` certainty event,
- Order 2: grounded integer refs (iteration/memory dependent),
- Order 3: speculative nodes (claims, including non-integer rationals and ungrounded integer claims).

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
- An implementation-backed prototype with explicit operational behavior,
- Not yet a formally proved alternative algebraic foundation.

Recommended public positioning:

> An epistemic and structural exploration of arithmetic construction from a single certainty primitive, implemented as a structure-preserving relational term graph.

Avoid claims implying geometric, dimensional, or foundational replacement narratives.
