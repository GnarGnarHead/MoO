# Modulus of One (MoO)

MoO is a constructionist arithmetic prototype that starts from one primitive grounded node, `Ref(1)`, and builds a canonicalized relational term graph with value interning and snapping rules using `+`, `-`, `*`, and `/`.

## Current Implementation

- Runtime object: canonicalized arithmetic term-DAG/graph (shared nodes, edge history).
- Identity model: enforced canonical value identity via interning and snapping.
- Grounded layer: unique grounded `Ref(N)` nodes for grounded integers.
- Speculative layer: rationals and integer claims until grounding resolves them.
- Collapse behavior: speculative nodes are rewired to grounded nodes when `potential_val` matches, then removed from active speculative storage.
- Prototype injection: `speculate_ref()` can inject speculative integer claims for demo/testing flows.

## What It Is Not

- Not a replacement for established mathematical foundations.
- Not a geometric or dimensional framework.
- Not a proof that classical arithmetic is invalid.

## Project Focus

- Preserve operational provenance while computing canonical value identity.
- Observe grounded vs speculative dynamics.
- Instrument snapping and construction behavior through JSON/DOT/stats outputs.

See [VISION.md](VISION.md) for the implementation-aligned specification and roadmap split.
