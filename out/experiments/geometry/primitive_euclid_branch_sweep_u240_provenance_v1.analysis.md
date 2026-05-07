# Primitive Euclid Branch Sweep U240 Provenance v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u240_provenance_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

Does increasing depth to U240 under the same bounds retain self-relation branch
witness rows, or does it only add square values witnessed through the
counting-spine branch?

MoO-native reading:

```text
A value appearing is not enough.
The same value can appear by different witnesses, and the witness matters.
```

## Corpus

```text
out/experiments/strict_stage_graph_u240_20260507.sqlite
U240
nodes: 21648
edges: 72445
strict alignment: pass
```

Corpus bounds:

```text
max_stage: 240
max_abs_p: 200
max_abs_q: 200
max_abs_value: 4
retain_confirmed_edges: true
```

## Summary

```text
branch_count: 15
node_complete_branch_count: 2
square_complete_count: 2
square_self_product_complete_count: 0
strict_self_product_complete_branch_count: 0
```

Machine witness source counts:

```text
self_product_edge: 0
core_confirmation_only: 14
other_graph_witness: 0
absent: 31
```

MoO translation:

```text
witnessed_through_self_relation_branch: 0 retained rows
witnessed_through_counting_spine: 14 square values
permitted_but_not_witnessed_or_not_visible_in_field: 31 square positions
```

Failure category counts:

```text
self_product_witness_missing: 2
square_components_missing: 13
```

## U80 / U120 / U240 Comparison

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
```

U240 adds square-node presence. In MoO language, those square values are
witnessed through the counting-spine branch. This does not mean they are absent
from the square branch; it means this report has not retained the
self-relation branch witness for them.

## New Node-Complete Branch

At U240, `5,12,13` becomes square-value-complete as a formula-family case:

```text
5,12,13
25:  core_confirmation_only
144: core_confirmation_only
169: core_confirmation_only
```

This is exactly the witness distinction the provenance classifier was added to
preserve:

```text
5,12,13 is square-value-complete at U240.
Its square values are witnessed through the counting-spine branch in this
report.
The shell/square interaction branch is not characterized by this report.
```

## Depth-Vs-Field Reading

The result supports the depth-vs-field diagnosis:

```text
Increasing U exposes more integer-spine square nodes.
It does not retain self-relation branch witness rows under current
field-of-observation settings.
```

For absent square nodes at U240, primary blockers are:

```text
output_excluded_by_max_abs_p: 31
```

All absent square nodes are also blocked by:

```text
output_excluded_by_max_abs_value: 31
```

There are no longer operand-not-confirmed blockers in this target range. The
remaining obstruction is the current field of observation, not depth.

MoO reading:

```text
The values appear.
The square values are witnessed through the counting-spine branch.
The shell/square interaction branch has not yet been characterized by this
report.
```

That is a statement about this field of observation, not a reason to tune the
instrument around the desired result.

## Safe Claim

This report supports:

```text
Under the U240 strict corpus with the same bounds, 5,12,13 becomes
square-value-complete as a primitive Euclid formula-family case. All visible
square values in the m<=8 sweep are witnessed through the counting-spine branch
by the current report machinery. No target case has retained self-relation
branch witness rows for all three square values.
```

This report does not support:

```text
5,12,13 has a characterized shell/square interaction branch.
Primitive Euclid branches emerge in a graph-native ordering law.
Graph cost explains branch emergence better than size controls.
Primes explain MoO geometry.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Next Use

The next experiment should not merely increase U, and it should not alter the
field of observation only to make a desired relation appear. The aligned next
move is either to accept this as counting-spine visibility without a
characterized shell/square interaction branch, or to preregister a general
branch-lineage audit and ask the same witness question again:

```text
use a general square-output field for all eligible confirmed operands
or raise max_abs_p and max_abs_value by a general rule
or add a non-mutating event audit that records permitted-but-unwitnessed
relations without promoting speculative square outputs to operands
```

The next target is Tier C:

```text
x*x, y*y, r*r are witnessed by retained self-relation branch rows
```

Only after Tier C should additive closure be tested as a stronger Tier D event.
