# Primitive Euclid Branch Sweep U80 v1 Analysis

> Status: paired analysis note for
> `primitive_euclid_branch_sweep_u80_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Question

This note answers only:

```text
In U80, which primitive Euclid branches are complete, partial, or absent, and
are the failures explained by missing generator nodes, shell nodes, square
components, or self-product witnesses?
```

It does not claim a branch-ordering law.

## Corpus

```text
out/experiments/strict_stage_graph_smoke.sqlite
U80
nodes: 3522
edges: 9559
strict alignment: pass
```

Target range:

```text
m <= 8
n < m
gcd(m,n) = 1
m - n odd
```

## Summary

```text
branch_count: 15
node_complete_branch_count: 1
strict_self_product_complete_branch_count: 0
generator_complete_count: 12
shell_complete_count: 12
square_complete_count: 1
```

Failure category counts:

```text
self_product_witness_missing: 1
square_components_missing: 11
generator_visible_shell_incomplete: 3
absent_under_bounds: 0
shell_visible_generator_unrecovered: 0
complete_branch: 0
```

## Branch Table

```text
triple       m,n    category                            gen  shell  square  selfprod  first  complete
3,4,5        2,1    self_product_witness_missing        1.00 1.00   1.00    0.00      1      25
5,12,13      3,2    square_components_missing           1.00 1.00   0.33    0.00      1      -
8,15,17      4,1    square_components_missing           1.00 1.00   0.33    0.00      1      -
7,24,25      4,3    square_components_missing           1.00 1.00   0.33    0.00      2      -
20,21,29     5,2    square_components_missing           1.00 1.00   0.00    0.00      1      -
12,35,37     6,1    square_components_missing           1.00 1.00   0.00    0.00      1      -
9,40,41      5,4    square_components_missing           1.00 1.00   0.00    0.00      2      -
28,45,53     7,2    square_components_missing           1.00 1.00   0.00    0.00      1      -
11,60,61     6,5    square_components_missing           1.00 1.00   0.00    0.00      5      -
16,63,65     8,1    square_components_missing           1.00 1.00   0.00    0.00      1      -
33,56,65     7,4    square_components_missing           1.00 1.00   0.00    0.00      2      -
48,55,73     8,3    square_components_missing           1.00 1.00   0.00    0.00      2      -
13,84,85     7,6    generator_visible_shell_incomplete  0.71 0.33   0.00    0.00      6      -
39,80,89     8,5    generator_visible_shell_incomplete  0.86 0.67   0.00    0.00      5      -
15,112,113   8,7    generator_visible_shell_incomplete  0.71 0.33   0.00    0.00      7      -
```

## Reading

The first primitive branch `3,4,5` is node-complete:

```text
generator_coverage: 1.0
shell_coverage: 1.0
square_coverage: 1.0
first_complete_stage: 25
graph_cost_rank: 1
```

It is not strict self-product-complete:

```text
self_product_witness_coverage: 0.0
failure_category: self_product_witness_missing
```

That should be read through the strict-stage retention guardrail. Integer square
nodes can be present because the core loop later confirms them, while the
literal `v * v -> v*v` edge may be absent because the square exceeded output
retention bounds at the first possible strict edge stage.

The next eleven branches are not blocked by generator or shell visibility.
They have generator and shell components visible, but square components are
missing:

```text
5,12,13
8,15,17
7,24,25
20,21,29
12,35,37
9,40,41
28,45,53
11,60,61
16,63,65
33,56,65
48,55,73
```

For the earliest three after `3,4,5`, exactly one square component is visible:

```text
5,12,13   square_coverage 0.33
8,15,17   square_coverage 0.33
7,24,25   square_coverage 0.33
```

The last three target branches are generator-visible but shell-incomplete under
U80:

```text
13,84,85
39,80,89
15,112,113
```

No target branch is fully absent under bounds. Every target has at least some
generator or shell component visible.

## Safe Claim

This report supports:

```text
For primitive Euclid targets with m <= 8, the U80 strict corpus has one
node-complete branch, 3,4,5, but no strict self-product-complete branch. Most
later target branches have visible generator and shell components but missing
square components; the largest targets in this range are shell-incomplete.
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

The next report should compare this U80 sweep against later or differently
bounded strict corpora. Only then can the project test whether graph-native cost
predicts primitive branch emergence better than ordinary size, radius, or
parameter-size baselines.
