# Primitive Euclid Branch Sweep U240 Provenance v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u240_provenance_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

Does increasing depth to U240 under the same bounds produce branch-local
self-product square provenance, or does it only add core-confirmation-only
square nodes from the integer spine?

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

Square provenance:

```text
self_product_edge: 0
core_confirmation_only: 14
other_graph_witness: 0
absent: 31
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

U240 adds square-node presence, but all added square nodes arrive by
core-loop confirmation only.

## New Node-Complete Branch

At U240, `5,12,13` becomes node-complete:

```text
5,12,13
25:  core_confirmation_only
144: core_confirmation_only
169: core_confirmation_only
```

This is exactly the witness distinction the provenance classifier was added to
preserve:

```text
5,12,13 is square-node-complete at U240.
5,12,13 is not branch-locally square-constructed at U240.
```

## Depth-Vs-Field Reading

The result supports the depth-vs-field diagnosis:

```text
Increasing U exposes more integer-spine square nodes.
It does not create retained branch-local self-product edges under current
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
The branch-square emergence has not yet been witnessed.
```

That is a statement about this field of observation, not a reason to tune the
instrument around the desired result.

## Safe Claim

This report supports:

```text
Under the U240 strict corpus with the same bounds, 5,12,13 becomes
square-node-complete, but all visible square nodes in the m<=8 sweep are still
core-confirmation-only. No target branch has retained branch-local
self-product square provenance.
```

This report does not support:

```text
5,12,13 is branch-locally squared.
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
move is either to accept this as an unwitnessed branch-square emergence under
the current field, or to preregister a general observation/audit rule and ask
the same witness question again:

```text
use a general square-output field for all eligible confirmed operands
or raise max_abs_p and max_abs_value by a general rule
or add a non-mutating event audit that records permitted-but-unwitnessed
relations without promoting speculative square outputs to operands
```

The next target is Tier C:

```text
x*x, y*y, r*r are witnessed by retained branch-local strict self-product edges
```

Only after Tier C should additive closure be tested as a stronger Tier D event.
