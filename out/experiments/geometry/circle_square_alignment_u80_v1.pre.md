# circle_square_alignment_u80_v1 Preregistration

> Status: preregistered geometry branch-alignment report.

## Question

Can MoO identify nondegenerate rational quadratic-shell families whose shell
components and square components are all present in the same strict graph corpus
with named graph-invariant timing and witness fields?

## Corpus

```text
db: out/experiments/strict_stage_graph_smoke.sqlite
strict stage: U80
max_abs_p: 200
max_abs_q: 200
corpus max_abs_value: 4
operand rule: confirmed core-loop positive integers only
```

The report intentionally scans with `max_abs_value 5` so the classical `3,4,5`
family can be audited. Confirmed positive integer nodes may exist beyond the
corpus output-retention value cap, but retained non-integer outputs still obey
the corpus bounds.

## Frozen Command

```sh
python3 moo_circle_square_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --max-denominator 20 \
  --max-abs-value 5 \
  --require-complete-family \
  --limit 6 \
  --experiment-id circle_square_alignment_u80_v1 \
  --with-checksums \
  --write out/experiments/geometry/circle_square_alignment_u80_v1.json \
  --pretty
```

## Metrics

Primary:

```text
candidate_count
complete_family_count
stage_spread
phase_delta
strict_self_product_witness_count
total_incoming_derivation_events
```

Shared graph-invariant fields:

```text
graph_invariant_summary.vocabulary_version
graph_invariant_summary.baseline_envelope
graph_invariant_summary.aggregate_operation_signature
graph_invariant_summary.neighborhood_overlap
```

## Controls And Guardrails

Minimum controls:

```text
nondegenerate shells only
denominator height
component height
complete family presence
strict self-product witness eligibility
```

Important strict-stage caveat:

```text
absence of a literal v * v edge is not failure for speculative rational v
```

For confirmed integer sources, absence of a retained `v * v` edge may also
reflect output-retention bounds at the first possible strict stage.

Disallowed language:

```text
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
Classical squaring-the-circle impossibility is refuted.
```

Allowed language:

```text
This strict corpus contains circle-square alignment candidates: rational
quadratic-shell families whose associated square components are present with
bounded stage timing and graph-native witness support.
```

## Decision Rule

Candidate success:

```text
the report completes without alignment failure
complete_family_count > 0
candidate rows include graph_invariant_summary with vocabulary_version
```

Limiting result:

```text
complete_family_count = 0
all candidates are degenerate
stage spreads are too large for any near-term phase-alignment claim
self-product witness language is explained entirely by strict operand/bound
rules
```
