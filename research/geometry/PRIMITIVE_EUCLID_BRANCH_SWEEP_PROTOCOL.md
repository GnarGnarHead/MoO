# Primitive Euclid Branch Sweep Protocol

> Status: active geometry / number-theory bridge protocol.
>
> This note defines the branch-level follow-up to circle-square alignment. It
> tracks complete, partial, and absent primitive Euclid branches in a strict MoO
> graph corpus. It does not claim a branch-ordering law from one corpus.

## Purpose

The earlier circle-square probe detects rational shell candidates:

```text
x*x + y*y = r*r
```

The branch sweep instead starts from primitive Euclid parameters:

```text
m > n
gcd(m,n) = 1
m - n odd

x = min(m*m - n*n, 2*m*n)
y = max(m*m - n*n, 2*m*n)
r = m*m + n*n
```

Then it asks:

```text
Which primitive branches are complete, partial, or absent in this strict graph
corpus, and what is missing?
```

MoO-native reading:

```text
The target is not value completion by itself.
The target is witnessed emergence.
```

A square node appearing through the counting spine is not the same event as a
square emerging through the Euclid branch. The report may use bookkeeping terms
such as `provenance`, `retention`, and `bounds`, but interpretation should read
them as witness and field of observation. See `../../MOO_REALIGNMENT_NOTE.md`.

## First-Class Absence

Each target branch receives a category:

```text
complete_branch
generator_visible_shell_incomplete
shell_visible_generator_unrecovered
square_components_missing
self_product_witness_missing
absent_under_bounds
```

This makes a small corpus useful even when later branches are not complete.

## Required Fields

Every branch report preserves:

```text
primitive_triple
m,n
euclid_valid
radius
component_height
m_plus_n
m_times_n
generator_coverage
shell_coverage
square_coverage
self_product_witness_coverage
first_visible_stage
first_complete_stage
generator_phase_spread
shell_phase_spread
square_phase_spread
failure_category
graph_cost_rank
radius_size_rank
component_height_rank
parameter_size_rank
```

## Coverage Definitions

Generator coverage:

```text
m
n
m*m
n*n
m*m - n*n
2*m*n
m*m + n*n
```

Shell coverage:

```text
x
y
r
```

Square coverage:

```text
x*x
y*y
r*r
```

Self-product witness coverage:

```text
strict edge x * x -> x*x
strict edge y * y -> y*y
strict edge r * r -> r*r
```

Strict-stage guardrail:

```text
Integer square nodes can be present while the literal self-product edge is
missing because the current field of observation may exclude the edge at the
first possible strict stage.
```

## Stage Fields

```text
first_visible_stage:
  earliest first_stage among any generator, shell, or square node present

first_complete_stage:
  latest first_stage among generator, shell, and square nodes when all such
  nodes are present; null otherwise

generator_phase_spread:
  max(first_stage) - min(first_stage) over generator nodes when complete

shell_phase_spread:
  max(first_stage) - min(first_stage) over x,y,r when complete

square_phase_spread:
  max(first_stage) - min(first_stage) over x*x,y*y,r*r when complete
```

## Rank Fields

First-pass rank definitions:

```text
graph_cost_rank:
  dense rank among node-complete branches by first_complete_stage,
  then component_height, then m_plus_n

radius_size_rank:
  dense rank by r = m*m + n*n

component_height_rank:
  dense rank by max(x,y,r)

parameter_size_rank:
  dense rank by (m+n, max(m,n), m*n)
```

The graph-cost rank is descriptive in a single corpus. It becomes evidence
only after comparison across multiple strict corpora or held-out stages.

## Square Provenance

Square node presence is not the same as branch-local construction.

For each square component:

```text
x*x
y*y
r*r
```

the sweep records:

```text
node_present
confirmed_stage
first_stage
incoming_edges
self_product_edge_present
self_product_edge_stage
self_product_edge_operands_confirmed_at_stage
square_node_source
retention_blocker if absent
```

Allowed square provenance classes:

```text
self_product_edge:
  the square node has a strict branch-local edge v * v -> v*v

core_confirmation_only:
  the square node appears through the integer spine at its confirmation stage,
  without an earlier graph witness

other_graph_witness:
  the square node has graph provenance, but not from the branch-local
  self-product edge

absent:
  the square node is absent from the corpus
```

Absent square nodes receive a retention diagnostic:

```text
operand_not_confirmed
output_excluded_by_max_abs_value
output_excluded_by_max_abs_p
output_excluded_by_max_abs_q
edge_not_generated_at_current_U
unknown
```

Here `retention diagnostic` is a tool/report term. The MoO reading is:

```text
why this field of observation did not witness the relation
```

Use the distinction:

```text
square_node_complete:
  x*x, y*y, r*r nodes are present

square_self_product_complete:
  x*x, y*y, r*r are each witnessed by branch-local self-product edges
```

Do not treat `square_node_complete` as construction completion.

MoO reading:

```text
square_node_complete:
  the values appear

square_self_product_complete:
  the square layer is witnessed through the branch
```

## First Experiment

Initial report:

```text
primitive_euclid_branch_sweep_u80_v1
```

Target range:

```text
m <= 8
n < m
gcd(m,n) = 1
m - n odd
```

The analysis note should answer only:

```text
In U80, which primitive Euclid branches are complete, partial, or absent, and
are the failures explained by missing generator nodes, shell nodes, square
components, or self-product witnesses?
```

Do not use the U80 report alone to claim that primitive Euclid branches emerge
in a reproducible graph-native order.
