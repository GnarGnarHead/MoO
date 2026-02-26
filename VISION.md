# Modulus of One (MoO)
## Vision and Prototype Specification
Version: 0.2-docs-aligned
Status: Implementation-aligned design note

---

## 1. Purpose

This document defines what MoO currently implements in `constructionist_math.py`, separates that from philosophical intent, and states a conservative roadmap.

It is a documentation alignment pass, not a claim of a new mathematical foundation.

---

## 2. Scope and Positioning

MoO is a constructionist epistemic experiment built around one primitive certainty event represented as `1`.

It is not:

- a replacement for ZFC/Peano-style foundations,
- a geometric or dimensional embedding framework,
- a proof that classical arithmetic is invalid.

The current code is a computational model of relational arithmetic construction with explicit derivation identity and value-equivalence tracking.

---

## 3. Current Mathematical Object

MoO currently implements:

- A single primitive grounded node (`Ref(1)`),
- Closure under arithmetic operations (`+`, `-`, `*`, `/`) at the graph level,
- Explicit value-equivalence classes (`p/q`) across nodes,
- Non-destructive resolution links from speculative nodes to grounded anchors,
- A shared term-DAG/graph representing derivations.

This produces a structure-preserving relational term graph with explicit value projection, rather than a free algebra.

---

## 4. Core Runtime Model (Current Implementation)

### 4.1 Node classes

- Grounded nodes (`status == "G"`): integer anchor references `Ref(N)`.
- Speculative nodes (`status == "S"`): non-grounded claims, including non-integer rationals and integer claims not yet grounded.

### 4.2 Graph-level identity and value projection

The graph enforces identity operationally via:

- `nodes_by_int`: one grounded `Ref(N)` per grounded integer,
- `value_classes`: many derivation nodes may share one reduced rational value `(p, q)`,
- `_snap_speculative_to_ref`: speculative nodes with matching `potential_val` record non-destructive resolution to grounded `Ref(N)`.

### 4.3 Edge history

Edges preserve operation provenance (`op`, `inputs`, `output`, metadata). Resolution events do not delete derivation nodes.

Structural preservation is primary; numeric identity is represented as value-equivalence and resolution relations.

---

## 5. Primitive, Grounding, and Injection

### 5.1 Primitive

`Ref(1)` is seeded at graph initialization and is the only first-class primitive.

### 5.2 Grounding rule

Other integers become grounded when construction paths produce them (notably via grounded `+` / `-` paths in the current workflow).

### 5.3 Prototype injection path (`speculate_ref`)

The prototype includes `speculate_ref(n)` which can inject speculative integer claims directly. This is used in demo flows to exercise snapping behavior.

Therefore, the current implementation is not a fully pure derivational model strictly from operations on `1`.

---

## 6. Operational Semantics (Current)

### 6.1 Addition and subtraction

- `G,G` inputs: normalize to integer, ensure grounded `Ref(N)` exists, and produce a derivation node.
- Mixed/speculative inputs with known exact values: compute exact rational result and keep derivation structure; integer results can resolve to `Ref(N)` anchors.
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

Identity and resolution behavior is implemented operationally, but not yet axiomatized or formally proven as a mathematical system.

Current operational rules:

- explicit value-equivalence tracking for speculative and grounded nodes,
- unique grounded identity for each grounded integer,
- enforced speculative-to-grounded resolution via `potential_val` matching and snapping events.

Derivationally distinct equal-valued structures are preserved as separate nodes.

---

## 8. Interface and Outputs

Primary inspection interfaces (stable in spirit, preserve signatures/shape):

- `to_json()` / `to_jsonable()` for machine-readable graph state,
- `to_dot()` for graph visualization,
- `to_snap_dot()` and `snap_events()` for snapping telemetry,
- `stats()` / field-map helpers for aggregate diagnostics.

---

## 9. Conceptual Roadmap vs Current Implementation

### 9.1 Current

- Structure-preserving arithmetic graph with shared nodes,
- Value-identity tracked via equivalence classes and non-destructive resolutions,
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
3. Invariants that should be preserved under rewiring/snap operations.
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
