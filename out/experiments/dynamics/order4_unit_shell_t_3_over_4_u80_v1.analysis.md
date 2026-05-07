# order4_unit_shell_t_3_over_4_u80_v1 Analysis

## Question

Can the strict-stage U80 smoke corpus support an exact unit-quadratic-shell
dossier for `t = 3/4`, with graph-visible component nodes and construction
witnesses?

## Corpus

Machine report:

```text
out/experiments/dynamics/order4_unit_shell_t_3_over_4_u80_v1.json
```

Corpus:

```text
out/experiments/strict_stage_graph_smoke.sqlite
```

Corpus configuration:

```text
max_stage: 80
max_abs_p: 200
max_abs_q: 200
max_abs_value: 4
retain_confirmed_edges: true
```

Corpus summary from the report:

```text
nodes: 3522
edges: 9559
latest_stage: U80
alignment.status: pass
speculative_input_edges: 0
non_core_operand_edges: 0
db_sha256: cd7955fac53e0c293aba05112d6001742ce6bd9d2d7ed8faf71c2e218dceaa5e
```

## Frozen Test

The preregistered unit-shell parametrization was:

```text
x = (1 - t*t) / (1 + t*t)
y = (2*t) / (1 + t*t)
```

For `t = 3/4`, the report computed:

```text
x = 7/25
y = 24/25
x*x + y*y = 1
```

The exact quadratic check passed.

## Metrics

Primary metric:

```text
complete_point: true
```

Component status:

```text
t = 3/4:
  present: true
  status: speculative
  first_stage: 4
  derivation_events: 20

x = 7/25:
  present: true
  status: speculative
  first_stage: 25
  derivation_events: 3

y = 24/25:
  present: true
  status: speculative
  first_stage: 25
  derivation_events: 3
```

Completion summary:

```text
complete_point: true
max_component_first_stage: 25
component_derivation_events: 26
quadratic_check.exact: true
```

## Controls

This run was preregistered as a protocol-smoke observation, not a promoted
candidate. The limited controls passed:

```text
strict corpus alignment passed
the exact rational shell check passed
the report included claim-boundary language
the report did not claim a Euclidean circle or pi construction
```

Future candidate work still needs:

```text
denominator-matched controls
construction-cost-matched controls
placebo quadratic forms
held-out shell families
symmetry-completion checks across signs
```

## Result Summary

The strict U80 corpus contains the exact rational unit-quadratic-shell point
generated from `t = 3/4`.

The graph-visible witnesses are simple strict-stage division events:

```text
t = 3/4:
  U4:  3 / 4   -> 3/4
  U8:  6 / 8   -> 3/4
  U12: 9 / 12  -> 3/4

x = 7/25:
  U25: 7 / 25   -> 7/25
  U50: 14 / 50  -> 7/25
  U75: 21 / 75  -> 7/25

y = 24/25:
  U25: 24 / 25  -> 24/25
  U50: 48 / 50  -> 24/25
  U75: 72 / 75  -> 24/25
```

The latest component first appears at `U25`, so this exact unit-shell point is
fully visible in the U80 strict corpus.

## Candidate Findings

This is a successful unit-shell observation:

```text
t, x, and y are all present as strict graph corpus nodes
the exact quadratic-shell identity holds
the component nodes have incoming construction witnesses
the corpus alignment check passed
```

This can be retained as a protocol-smoke artifact and as a possible input to a
later controlled quadratic-shell study.

## Failed / Negative Findings

Symmetry coverage is incomplete:

```text
variant_count: 4
complete_variant_count: 1
all_variants_complete: false
```

The negative sign variants involving `-7/25` and `-24/25` are not present as
complete component pairs in this corpus. This matters because a fuller
circle-like invariant would need more than one positive-quadrant rational point.

The report does not establish:

```text
a Euclidean circle
pi
rotation
angle
circumference
area
an Order-4 projected object
```

## Caveats

The source parameter `t = 3/4` was hand-selected as a small exact protocol
smoke test. This result should not be read as evidence that unit-shell points
are unusual in the corpus.

All component nodes are speculative rationals. They are real graph nodes, but
they are not operands in strict-stage MoO.

The relation status remains:

```text
external_parametrized_candidate_relation
```

The parametrization is an external analysis probe until MoO-native orbit,
refinement, and Q-preserving transformation criteria are tested.

## Decision

Retain as a successful protocol-smoke observation.

Do not promote it to an Order-4 projected object. Do not use it as evidence
that MoO defines the Euclidean circle or constructs pi.

## Next Question

Run a corpus-level unit-shell summary and compare complete points against
baseline controls:

```sh
python3 moo_circle_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --unit-circle \
  --only-complete \
  --experiment-id order4_unit_shell_summary_u80_v1 \
  --write out/experiments/dynamics/order4_unit_shell_summary_u80_v1.json \
  --pretty
```

The next analysis should ask whether complete unit-shell points are common,
whether their component costs are ordinary for their denominators, and whether
symmetry completion improves under larger or differently bounded strict corpora.
