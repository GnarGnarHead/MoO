# Primitive Euclid Branch Sweep U120 Provenance v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u120_provenance_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

Of the visible square nodes in U120, how many are branch-local self-product
constructions versus core-confirmed integer-spine nodes, other graph witnesses,
or absent outputs?

MoO-native reading:

```text
A value appearing is not enough.
The same value can appear by different witnesses, and the witness matters.
```

## Summary

```text
branch_count: 15
node_complete_branch_count: 1
square_complete_count: 1
square_self_product_complete_count: 0
strict_self_product_complete_branch_count: 0
```

Square provenance across all target branches:

```text
self_product_edge: 0
core_confirmation_only: 7
other_graph_witness: 0
absent: 38
```

Failure category counts:

```text
self_product_witness_missing: 1
square_components_missing: 14
```

## Main Result

U120 completes generator and shell visibility for all target branches, but it
does not produce branch-local square self-product evidence.

The visible square nodes are still all classified as:

```text
core_confirmation_only
```

No square component in the `m <= 8` branch sweep is classified as:

```text
self_product_edge
other_graph_witness
```

## U80 Comparison

```text
U80  self_product_edge:       0
U80  core_confirmation_only:  6
U80  absent:                 39

U120 self_product_edge:       0
U120 core_confirmation_only:  7
U120 absent:                 38
```

U120 adds one more visible square node, but it enters by core confirmation, not
by retained branch-local self-product construction.

The major U120 improvement remains generator/shell visibility:

```text
U80  generator_complete_count: 12
U80  shell_complete_count:    12

U120 generator_complete_count: 15
U120 shell_complete_count:    15
```

## Field-Of-Observation Diagnostics

Absent square primary blockers:

```text
output_excluded_by_max_abs_value: 5
output_excluded_by_max_abs_p: 33
```

All blocker tags:

```text
output_excluded_by_max_abs_value: 38
output_excluded_by_max_abs_p: 33
```

Unlike U80, there are no operand-not-confirmed blockers in this target range.
At U120, the branch components are available; the missing square layer is a
field-of-observation problem under the current `max_abs_p=200` and
`max_abs_value=4` settings.

## Safe Claim

This report supports:

```text
In the U120 strict corpus, primitive Euclid targets with m<=8 have complete
generator and shell visibility, but the square layer is not branch-locally
constructed. All visible square nodes are core-confirmation-only, and absent
square nodes are explained by output retention bounds.
```

This report does not support:

```text
3,4,5 is branch-locally squared.
The next primitive branch has emerged as a branch-local square construction.
Primitive Euclid branches emerge in a graph-native ordering law.
Primes explain MoO geometry.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Next Use

The next decisive experiment should not merely increase U, and it should not
change the observation field only to rescue a desired geometry result. It
should either accept the current finding as unwitnessed branch-square emergence
under this field of observation, or preregister a general observation field and
ask the same witness question again:

```text
use a general square-output field for all eligible confirmed operands
or raise max_abs_value / max_abs_p by a general rule
or add a non-mutating event audit that records permitted-but-unwitnessed
relations without promoting speculative square outputs to operands
```

The clean next target is Tier C:

```text
x*x, y*y, r*r witnessed by branch-local strict self-product edges
```

Additive closure:

```text
x*x + y*y -> r*r
```

should remain a later, stronger tier because strict MoO cannot use speculative
square nodes as operands until they are confirmed.
