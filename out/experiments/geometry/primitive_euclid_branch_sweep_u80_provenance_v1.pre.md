# Primitive Euclid Branch Sweep U80 Provenance v1 Preregistration

> Status: preregistered geometry / number-theory bridge report.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Corpus

```text
out/experiments/strict_stage_graph_smoke.sqlite
```

## Command

```sh
python3 primitive_euclid_branch_sweep.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --max-m 8 \
  --experiment-id primitive_euclid_branch_sweep_u80_provenance_v1 \
  --with-checksums \
  --write out/experiments/geometry/primitive_euclid_branch_sweep_u80_provenance_v1.json \
  --pretty
```

## Question

Of the visible square nodes in U80, how many are branch-local self-product
constructions versus core-confirmed integer-spine nodes, other graph witnesses,
or absent outputs?

## Fixed Target Range

```text
m <= 8
n < m
gcd(m,n) = 1
m - n odd
```

## New Provenance Fields

For each `x*x`, `y*y`, and `r*r`:

```text
square_node_source:
  self_product_edge
  core_confirmation_only
  other_graph_witness
  absent

self_product_edge_present
self_product_edge_stage
self_product_edge_operands_confirmed_at_stage
incoming_edges
retention_blocker
```

## Guardrail

This report separates square-node presence from branch-local square
construction. It should not be used to claim a primitive-branch ordering law.
