# Primitive Euclid Branch Sweep U80 v1 Preregistration

> Status: preregistered geometry / number-theory bridge report.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Corpus

```text
out/experiments/strict_stage_graph_smoke.sqlite
```

Expected corpus rule:

```text
only confirmed positive core-loop integers are operands
speculative rational nodes are recorded but not used as operands
```

## Command

```sh
python3 primitive_euclid_branch_sweep.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --max-m 8 \
  --experiment-id primitive_euclid_branch_sweep_u80_v1 \
  --with-checksums \
  --write out/experiments/geometry/primitive_euclid_branch_sweep_u80_v1.json \
  --pretty
```

## Target Range

```text
m <= 8
n < m
gcd(m,n) = 1
m - n odd
```

## Question

In U80, which primitive Euclid branches are complete, partial, or absent, and
are the failures explained by missing generator nodes, shell nodes, square
components, or self-product witnesses?

## Required Branch Categories

```text
complete_branch
generator_visible_shell_incomplete
shell_visible_generator_unrecovered
square_components_missing
self_product_witness_missing
absent_under_bounds
```

## Required Fields

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

## Guardrail

This report establishes the measurement apparatus and first branch visibility
only. Do not use one U80 report to claim a reproducible primitive-branch
ordering law. That requires multiple strict corpora, later U stages, or
held-out comparisons.
