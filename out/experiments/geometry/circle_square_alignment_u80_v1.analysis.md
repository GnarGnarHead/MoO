# circle_square_alignment_u80_v1 Analysis

> Status: interpretation note for saved strict report.

## Question

Can MoO identify nondegenerate rational quadratic-shell families whose shell
components and square components are all present in the same strict graph corpus
with named graph-invariant timing and witness fields?

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
out/experiments/geometry/circle_square_alignment_u80_v1.json
```

## Frozen Test

The preregistered command scanned nonnegative, nondegenerate rational shell
pairs with:

```text
max_denominator: 20
max_abs_value: 5
require_complete_family: true
limit: 6
```

A complete family means all six nodes are present:

```text
x, y, r, x*x, y*y, r*r
```

## Result Summary

The report completed successfully:

```text
candidate_count: 8
complete_family_count: 8
with_any_strict_self_product_witness_count: 4
with_all_strict_self_product_witnesses_count: 0
```

This supports the narrow claim:

```text
This U80 strict corpus contains nondegenerate circle-square alignment
candidates: rational quadratic-shell families whose associated square
components are present with graph-native timing and witness fields.
```

MoO correction:

```text
This is report machinery for value families.
It is not yet a branch-lineage result.
```

It does not support:

```text
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
Classical squaring-the-circle impossibility is refuted.
```

## Top Candidates

Lowest combined stage spread:

```text
3, 4, 5         spread 23  phase_delta 20  selfprod 0  events 514
3/5, 4/5, 1     spread 24  phase_delta 20  selfprod 1  events 360
3/4, 1, 5/4     spread 24  phase_delta 20  selfprod 1  events 366
1, 4/3, 5/3     spread 24  phase_delta 20  selfprod 1  events 366
1/2, 2/3, 5/6   spread 34  phase_delta 30  selfprod 0  events 109
3/7, 4/7, 5/7   spread 42  phase_delta 42  selfprod 0  events 36
```

Highest family witness mass:

```text
3, 4, 5         events 514  spread 23
3/4, 1, 5/4     events 366  spread 24
1, 4/3, 5/3     events 366  spread 24
3/5, 4/5, 1     events 360  spread 24
6/5, 8/5, 2     events 249  spread 63
1/2, 2/3, 5/6   events 109  spread 34
```

## Interpretation

The first strong machine observation is not surprising, but it is useful:

```text
the 3,4,5 shell is the strongest complete family by witness mass
```

That is expected classical algebra, but MoO now records it in graph-native
terms:

```text
shell stage spread: 3
square-component stage spread: 16
combined stage spread: 23
phase_delta: 20
total incoming derivation events: 514
baseline envelope max component height: 25
```

The `phase_delta` result is important. In this corpus, shell components become
visible much earlier than the full square-component value family. Square-value
visibility lags shell-value visibility by about 20 stages for the low-spread
candidates.

MoO-native caution:

```text
square-component value visibility is not the same as square-branch witnessing
```

The branch question is where the shell-relation branch and self-relation /
square branch interact, not merely whether the six component values are present.

## Self-Product Caveat

No candidate has strict self-product witnesses for all three square components.

For rational shell components, that is expected:

```text
speculative rational nodes are not operands in strict-stage MoO
```

For the integer `3,4,5` family, the report still does not find retained
`3*3`, `4*4`, or `5*5` rows. That is a field/generator caveat, not a
mathematical absence: at the first possible strict stages, those square outputs
fall outside the corpus field of observation, and later core-loop confirmation
does not retroactively store that original self-product row.

So the right machine reading is:

```text
square nodes are present
literal self-product edge evidence is bound/generator-conditioned
```

MoO reading:

```text
the square values may be witnessed through the counting-spine branch while the
self-relation branch witness is permitted but not retained in this field
```

## Decision

Decision:

```text
candidate success for circle-square alignment reporting
lead only for geometry interpretation
no upgrade to circle, pi, or classical squaring claims
```

The report validates the report object:

```text
shell-relation candidates and square-like component readings can be inspected
in one strict graph corpus with shared invariant language.
```

It does not yet validate branch interaction in the MoO sense.

## Next Question

The next scan should separate two questions:

```text
1. branch-lineage audit:
   use `branch_lineage.py` to establish square/even/prime-branch readings
   before interpreting shell-square interaction.

2. rational branch alignment:
   ignore literal self-product edges for speculative rational components and
   rank complete shell-square families by stage spread, witness mass,
   denominator/component-height controls, and neighborhood overlap.
```

That split will prevent the square-language from being overcontrolled by a
storage policy artifact.
