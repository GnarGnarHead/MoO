# geometry_unit_shell_summary_u80_v1 Analysis

> Status: interpretation note for saved strict report.

## Question

Can MoO expose complete rational unit-quadratic-shell candidates through shared
graph-native invariants without importing Euclidean circle or `pi` semantics?

## Corpus

```text
db: out/experiments/strict_stage_graph_smoke.sqlite
strict stage: U80
nodes: 3,522
edges: 9,559
alignment: pass
```

The saved report is:

```text
out/experiments/geometry/geometry_unit_shell_summary_u80_v1.json
```

## Frozen Test

The preregistered command scanned unit-shell candidates from strict-corpus
parameter nodes with:

```text
max_denominator: 40
max_abs_value: 4
only_complete: true
limit: 12
```

## Result Summary

The report completed successfully and passed the preregistered candidate-success
rule:

```text
complete_point_count: 27
candidate_count after --only-complete: 27
missing_x_count: 0
missing_y_count: 0
graph_invariant_summary present: yes
```

This supports the narrow claim:

```text
MoO can inspect complete rational unit-quadratic-shell candidates in this
strict corpus through shared graph-native invariants.
```

It does not support:

```text
MoO defines the circle.
MoO constructs pi.
The unit-shell parametrization is an internal MoO derivation.
```

## Invariant Findings

Every listed complete candidate now carries:

```text
graph_invariant_summary.vocabulary_version: graph_invariants.v1
max_first_stage
total_incoming_derivation_events
aggregate_operation_signature
baseline_envelope
present/missing component counts
```

The strongest witness-mass rows are dominated by degenerate or axis-like shell
points:

```text
t = 1     -> (0, 1)
t = 0     -> (1, 0)
t = -1    -> (0, -1)
```

The first nondegenerate complete examples include:

```text
t = 1/2   -> (3/5, 4/5), max_first_stage 5
t = 1/3   -> (4/5, 3/5), max_first_stage 5
t = 2/3   -> (5/13, 12/13), max_first_stage 13
t = 1/5   -> (12/13, 5/13), max_first_stage 13
t = 3/4   -> (7/25, 24/25), max_first_stage 25
```

The denominator distribution shows the expected rational-shell/Pythagorean
pattern rather than a completed geometric object:

```text
1, 5, 13, 17, 25, 29, 37, 41, 53, 61, 65, 73
```

Symmetry is not yet a strong circle-like result:

```text
all_symmetry_variants_complete_count: 3
```

Those full-symmetry completions are explained by the degenerate/axis cases
under the current bounds. Nondegenerate candidates generally have only the
positive quadrant complete because negative component nodes are not all present
under this strict corpus and value bound.

## Controls

This report includes first-pass controls only:

```text
denominator height
component height
complete versus incomplete component presence
symmetry coverage
```

It does not yet compare candidates against denominator-matched non-shell
families or held-out stage growth.

## Decision

Decision:

```text
candidate success for graph-invariant reporting
lead only for circle-adjacent structure
no upgrade to circle, pi, or Order-4 claims
```

The useful progress is methodological: shell candidates can now be preserved
with the same invariant vocabulary that node dossiers and future Order-4 tests
will use.

## Next Question

The next geometry report should remove or separate degenerate axis cases and
ask:

```text
Among nondegenerate complete unit-shell candidates, do any families show
baseline-adjusted witness diversity, neighborhood overlap, or symmetry recovery
that survives denominator/component-height controls?
```
