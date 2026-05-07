# order4_unit_shell_t_3_over_4_u80_v1 Preregistration

## Question

Can the strict-stage U80 smoke corpus support an exact unit-quadratic-shell
dossier for the rational parameter `t = 3/4`, with `t`, `x`, and `y` read
through graph evidence rather than circle or pi language?

## Evidence Layer

```text
evidence_layer: strict
claim_status: observation
```

This is not an Order-4 projected-object claim yet. It is a prerequisite
unit-shell observation that may later support projected-invariant work.

## Corpus

Planned corpus path:

```text
out/experiments/strict_stage_graph_smoke.sqlite
```

Planned corpus setup command:

```sh
python3 strict_stage_moo.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --max-stage 80 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --quiet \
  --pretty
```

Expected corpus rule:

```text
strict-stage MoO
operands = confirmed core-loop positive integers only
speculative outputs are recorded, not operated on
```

## Frozen Test

Use the exact rational unit-shell parametrization:

```text
x = (1 - t*t) / (1 + t*t)
y = (2*t) / (1 + t*t)
```

For `t = 3/4`, inspect whether the resulting `x` and `y` are present as graph
nodes in the strict corpus and whether the exact check holds:

```text
x*x + y*y = 1
```

Machine report command:

```sh
python3 moo_circle_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --unit-circle \
  --node 3/4 \
  --experiment-id order4_unit_shell_t_3_over_4_u80_v1 \
  --write out/experiments/dynamics/order4_unit_shell_t_3_over_4_u80_v1.json \
  --pretty
```

## Metrics

Primary metric:

```text
complete_point: t, x, and y component nodes are present in the strict corpus.
```

Secondary metrics:

```text
quadratic_check.exact
max_component_first_stage
component_derivation_events
incoming_edge_examples for t, x, and y
symmetry_coverage
corpus.alignment.status
```

## Controls

This first run is a protocol-smoke observation, not a promoted candidate. The
control requirement is therefore limited to:

```text
strict corpus alignment must pass
the report must preserve claim-boundary language
the report must not claim a Euclidean circle or pi construction
```

Future candidate work must add denominator-matched, construction-cost-matched,
and placebo quadratic-shell controls.

## Thresholds

Observation succeeds if:

```text
corpus.alignment.status == pass
quadratic_check.exact == true
completion.complete_point == true
incoming graph evidence is present for t, x, and y
```

Observation fails or downgrades if:

```text
strict alignment fails
the component nodes are absent
the exact shell check fails
the report only provides value-level data without graph evidence
```

## Allowed Claim Language

```text
The strict U80 corpus contains the exact rational unit-quadratic-shell point
generated from t = 3/4, with graph-visible component nodes and construction
witnesses.
```

## Disallowed Claim Language

```text
MoO defines the Euclidean circle.
MoO constructs pi.
This unit-shell point is an Order-4 projected object.
The unit-shell parametrization is an internal MoO derivation of a circle.
```

## Decision Rule

If the observation succeeds, write an analysis note and use it only as a
protocol-smoke artifact plus a possible input to later controlled
quadratic-shell studies.

If it fails, record the failure and do not reinterpret the result as geometric
evidence.
