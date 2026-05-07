# Primitive Euclid Branch Sweep U120 v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u120_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

Compared with U80, which primitive Euclid branches become complete, remain
partial, or remain blocked under U120, and are the failures explained by missing
generator nodes, shell nodes, square components, or self-product witnesses?

This note does not claim a primitive-branch ordering law.

## Corpus

```text
out/experiments/strict_stage_graph_u120_20260507.sqlite
U120
nodes: 7798
edges: 20989
strict alignment: pass
```

Corpus bounds:

```text
max_stage: 120
max_abs_p: 200
max_abs_q: 200
max_abs_value: 4
retain_confirmed_edges: true
```

Target range:

```text
m <= 8
n < m
gcd(m,n) = 1
m - n odd
```

## Summary

U120:

```text
branch_count: 15
node_complete_branch_count: 1
strict_self_product_complete_branch_count: 0
generator_complete_count: 15
shell_complete_count: 15
square_complete_count: 1
```

Failure category counts:

```text
self_product_witness_missing: 1
square_components_missing: 14
```

U80 comparison:

```text
U80 generator_complete_count: 12
U80 shell_complete_count: 12
U80 square_complete_count: 1
U80 node_complete_branch_count: 1

U120 generator_complete_count: 15
U120 shell_complete_count: 15
U120 square_complete_count: 1
U120 node_complete_branch_count: 1
```

## Main Change From U80

U120 completes generator and shell visibility for all target branches in the
`m <= 8` sweep.

The three U80 `generator_visible_shell_incomplete` branches become
`square_components_missing`:

```text
13,84,85     gen/shell 0.71/0.33 -> 1.00/1.00
39,80,89     gen/shell 0.86/0.67 -> 1.00/1.00
15,112,113   gen/shell 0.71/0.33 -> 1.00/1.00
```

No new node-complete branch appears.

## Branch Table

```text
triple       m,n    category                      gen  shell  square  selfprod  first  complete
3,4,5        2,1    self_product_witness_missing  1.00 1.00   1.00    0.00      1      25
5,12,13      3,2    square_components_missing     1.00 1.00   0.33    0.00      1      -
8,15,17      4,1    square_components_missing     1.00 1.00   0.33    0.00      1      -
7,24,25      4,3    square_components_missing     1.00 1.00   0.33    0.00      2      -
20,21,29     5,2    square_components_missing     1.00 1.00   0.00    0.00      1      -
12,35,37     6,1    square_components_missing     1.00 1.00   0.00    0.00      1      -
9,40,41      5,4    square_components_missing     1.00 1.00   0.33    0.00      2      -
28,45,53     7,2    square_components_missing     1.00 1.00   0.00    0.00      1      -
11,60,61     6,5    square_components_missing     1.00 1.00   0.00    0.00      5      -
16,63,65     8,1    square_components_missing     1.00 1.00   0.00    0.00      1      -
33,56,65     7,4    square_components_missing     1.00 1.00   0.00    0.00      2      -
48,55,73     8,3    square_components_missing     1.00 1.00   0.00    0.00      2      -
13,84,85     7,6    square_components_missing     1.00 1.00   0.00    0.00      6      -
39,80,89     8,5    square_components_missing     1.00 1.00   0.00    0.00      5      -
15,112,113   8,7    square_components_missing     1.00 1.00   0.00    0.00      7      -
```

## Square-Component Reading

The bottleneck at U120 is square visibility.

Branches with one visible square component:

```text
5,12,13
8,15,17
7,24,25
9,40,41
```

In each case, the visible square component is `x_square`. The missing pieces
remain `y_square` and `r_square`.

All other later branches have no square components visible under the current
U120 / value-bound settings.

## Safe Claim

This report supports:

```text
Under the U120 strict corpus with the same p/q/value bounds, all primitive
Euclid targets with m <= 8 have complete generator and shell node visibility,
but only 3,4,5 has all square component nodes. U120 extends shell visibility
relative to U80 but does not produce the next node-complete primitive branch.
```

This report does not support:

```text
Primitive Euclid branches emerge in a reproducible graph-native order.
Graph cost explains branch emergence better than size controls.
Primes explain MoO geometry.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Next Use

The next decisive experiment should change square-retention conditions rather
than only increasing U. Under current settings, U120 makes the generator/shell
side visible but leaves square components blocked for later branches.

Useful next variants:

```text
increase max_abs_p / max_abs_q enough to retain y_square and r_square
or explicitly retain square outputs for target Euclid branches
or run a wider value-bound corpus and compare square-component phase-in
```
