# Primitive Euclid Branch Sweep U120 v1 Preregistration

> Status: preregistered geometry / number-theory bridge report.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Corpus

```text
out/experiments/strict_stage_graph_u120_20260507.sqlite
```

Corpus command:

```sh
python3 strict_stage_moo.py \
  --db out/experiments/strict_stage_graph_u120_20260507.sqlite \
  --max-stage 120 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --quiet \
  --pretty \
  --summary out/experiments/strict_stage_graph_u120_20260507_summary.json
```

Expected corpus rule:

```text
only confirmed positive core-loop integers are operands
speculative rational nodes are recorded but not used as operands
```

## Report Command

```sh
python3 primitive_euclid_branch_sweep.py \
  --db out/experiments/strict_stage_graph_u120_20260507.sqlite \
  --max-m 8 \
  --experiment-id primitive_euclid_branch_sweep_u120_v1 \
  --with-checksums \
  --write out/experiments/geometry/primitive_euclid_branch_sweep_u120_v1.json \
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

Compared with U80, which primitive Euclid branches become complete, remain
partial, or remain blocked under U120, and are the failures explained by missing
generator nodes, shell nodes, square components, or self-product witnesses?

## Guardrail

This is still a single later-stage comparison, not a branch-ordering theorem.
The safe claim is about U80-to-U120 visibility changes under the named bounds.
