# Modulus of One (MoO)

MoO is a constructionist arithmetic prototype that starts from one primitive grounded node, `Ref(1)`, and builds a structure-preserving relational term graph using `+`, `-`, `*`, and `/`.

## Current Implementation

- Runtime object: structure-preserving arithmetic term-DAG/graph (shared nodes, edge history).
- Identity model: derivation identity is preserved; value identity is tracked via explicit equivalence classes.
- Grounded layer: unique grounded `Ref(N)` nodes for grounded integers.
- Speculative layer: rationals and integer claims until grounding resolves them.
- Resolution behavior: speculative nodes link to grounded anchors via non-destructive `resolves_to` relations.
- Prototype injection: `speculate_ref()` can inject speculative integer claims for demo/testing flows.

## What It Is Not

- Not a replacement for established mathematical foundations.
- Not a geometric or dimensional framework.
- Not a proof that classical arithmetic is invalid.

## Project Focus

- Preserve operational provenance while computing value-equivalence classes.
- Observe grounded vs speculative dynamics.
- Instrument snapping and construction behavior through JSON/DOT/stats outputs.

See [VISION.md](VISION.md) for the implementation-aligned specification and roadmap split.
