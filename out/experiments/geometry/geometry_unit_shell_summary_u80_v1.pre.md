# geometry_unit_shell_summary_u80_v1 Preregistration

> Status: preregistered geometry-adjacent strict report.

## Question

Can MoO expose complete rational unit-quadratic-shell candidates through shared
graph-native invariants without importing Euclidean circle or `pi` semantics?

## Corpus

```text
db: out/experiments/strict_stage_graph_smoke.sqlite
strict stage: U80
max_abs_p: 200
max_abs_q: 200
max_abs_value: 4
operand rule: confirmed core-loop positive integers only
```

## Frozen Command

```sh
python3 moo_circle_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --unit-circle \
  --max-denominator 40 \
  --max-abs-value 4 \
  --only-complete \
  --limit 12 \
  --experiment-id geometry_unit_shell_summary_u80_v1 \
  --with-checksums \
  --write out/experiments/geometry/geometry_unit_shell_summary_u80_v1.json \
  --pretty
```

## Metrics

Primary:

```text
complete_point_count
top_low_stage_complete_points
top_high_witness_complete_points
```

Shared graph-invariant fields:

```text
max_component_first_stage
component_derivation_events
graph_invariant_summary.vocabulary_version
graph_invariant_summary.baseline_envelope
graph_invariant_summary.aggregate_operation_signature
```

Geometry-adjacent fields:

```text
symmetry_complete_variants
all_symmetry_variants_complete_count
denominator_distribution
```

## Controls And Guardrails

Controls:

```text
denominator height
component height
complete versus incomplete component presence
symmetry coverage
```

Disallowed language:

```text
MoO defines the circle.
MoO constructs pi.
The unit-shell parametrization is an internal MoO derivation.
```

Allowed language:

```text
MoO can inspect complete rational unit-quadratic-shell candidates in this
strict corpus through graph-native invariants.
```

## Decision Rule

Candidate success:

```text
the report completes without alignment failure
complete_point_count > 0
candidate rows include graph_invariant_summary with vocabulary_version
```

Negative or limiting result:

```text
complete_point_count = 0
invariant fields are missing or not comparable
symmetry coverage is weak enough to block stronger circle-like language
```
