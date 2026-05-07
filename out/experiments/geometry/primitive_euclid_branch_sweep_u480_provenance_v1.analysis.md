# Primitive Euclid Branch Sweep U480 Provenance v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u480_provenance_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

Does increasing depth to U480 under the same bounds retain self-relation
branch witness rows, or does it only add square values witnessed through the
counting-spine branch?

MoO-native reading:

```text
A value appearing is not enough.
The same value can appear by different witnesses, and the witness matters.
```

## Corpus

```text
out/experiments/strict_stage_graph_u480_20260507.sqlite
U480
nodes: 21888
edges: 211609
strict alignment: pass
```

Corpus bounds:

```text
max_stage: 480
max_abs_p: 200
max_abs_q: 200
max_abs_value: 4
retain_confirmed_edges: true
```

## Summary

```text
branch_count: 15
node_complete_branch_count: 3
square_complete_count: 3
square_self_product_complete_count: 0
strict_self_product_complete_branch_count: 0
```

Machine witness source counts:

```text
self_product_edge: 0
core_confirmation_only: 18
other_graph_witness: 0
absent: 27
```

MoO translation:

```text
witnessed_through_self_relation_branch: 0 retained rows
witnessed_through_counting_spine: 18 square values
permitted_but_not_witnessed_or_not_visible_in_field: 27 square positions
```

Failure category counts:

```text
self_product_witness_missing: 3
square_components_missing: 12
```

## U80 / U120 / U240 / U480 Comparison

```text
U80:
  node_complete_branch_count: 1
  square_complete_count: 1
  self_product_edge: 0
  core_confirmation_only: 6
  absent: 39

U120:
  node_complete_branch_count: 1
  square_complete_count: 1
  self_product_edge: 0
  core_confirmation_only: 7
  absent: 38

U240:
  node_complete_branch_count: 2
  square_complete_count: 2
  self_product_edge: 0
  core_confirmation_only: 14
  absent: 31

U480:
  node_complete_branch_count: 3
  square_complete_count: 3
  self_product_edge: 0
  core_confirmation_only: 18
  absent: 27
```

U480 adds square-node presence. In MoO language, those square values are
witnessed through the counting-spine branch. This does not mean they are absent
from the square branch; it means this report has not retained the
self-relation branch witness for them.

## Node-Complete Branches

The square-value-complete formula-family cases are:

```text
3,4,5:
  first_complete_stage: 25
  square sources: core_confirmation_only = 3

5,12,13:
  first_complete_stage: 169
  square sources: core_confirmation_only = 3

8,15,17:
  first_complete_stage: 289
  square sources: core_confirmation_only = 3
```

The new U480 node-complete formula-family case is `8,15,17`. It becomes
square-value-complete because `64`, `225`, and `289` are visible through the
counting-spine branch. The report does not retain `8*8`, `15*15`, and `17*17`
as self-relation branch witnesses.

## Partial Square Visibility

Several later branches have partial square visibility:

```text
7,24,25:
  square_coverage: 1/3

20,21,29:
  square_coverage: 2/3

12,35,37:
  square_coverage: 1/3

9,40,41:
  square_coverage: 1/3

11,60,61:
  square_coverage: 1/3

16,63,65:
  square_coverage: 1/3

13,84,85:
  square_coverage: 1/3

15,112,113:
  square_coverage: 1/3
```

Each visible square in those partial branches is also witnessed through the
counting-spine branch according to the current machine field
`core_confirmation_only`.

## Depth-Vs-Field Reading

The U480 run strengthens the earlier diagnosis:

```text
Increasing U exposes more spine-witnessed integer square values.
It does not retain self-relation branch witnesses under the current field of
observation.
```

MoO reading:

```text
The values appear.
The square values are witnessed through the counting-spine branch.
The shell/square interaction branch has not yet been characterized by this
report.
```

This is the same qualitative result as U80/U120/U240, with more counting-spine
coverage.

## Safe Claim

This report supports:

```text
Under the U480 strict corpus with the same bounds, 8,15,17 becomes the third
square-value-complete primitive Euclid formula-family case in the m<=8 sweep.
All visible square values are witnessed through the counting-spine branch by
the current report machinery. No target case has retained self-relation branch
witness rows for all three square values.
```

This report does not support:

```text
8,15,17 has a characterized shell/square interaction branch.
Primitive Euclid branches emerge in a graph-native ordering law.
Graph cost explains branch emergence better than size controls.
Primes explain MoO geometry.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Next Use

Do not treat U480 as a win condition. The aligned next move is either to accept
this as counting-spine visibility without a characterized shell/square
interaction branch, or to preregister a general branch-lineage audit and ask
the same witness question again:

```text
use a general square-output field for all eligible confirmed operands
or raise max_abs_p and max_abs_value by a general rule
or add a non-mutating event audit that records permitted-but-unwitnessed
relations without promoting speculative square outputs to operands
```

The next target remains:

```text
x*x, y*y, r*r are witnessed by retained self-relation branch rows
```
