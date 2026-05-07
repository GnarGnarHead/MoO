# Primitive Euclid Branch Sweep U240 Provenance v1 Preregistration

> Status: preregistered geometry / number-theory bridge report.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Corpus

```text
out/experiments/strict_stage_graph_u240_20260507.sqlite
```

Corpus command:

```sh
python3 strict_stage_moo.py \
  --db out/experiments/strict_stage_graph_u240_20260507.sqlite \
  --max-stage 240 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --quiet \
  --pretty \
  --summary out/experiments/strict_stage_graph_u240_20260507_summary.json
```

## Report Command

```sh
python3 primitive_euclid_branch_sweep.py \
  --db out/experiments/strict_stage_graph_u240_20260507.sqlite \
  --max-m 8 \
  --experiment-id primitive_euclid_branch_sweep_u240_provenance_v1 \
  --with-checksums \
  --write out/experiments/geometry/primitive_euclid_branch_sweep_u240_provenance_v1.json \
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

Does increasing depth to U240 under the same bounds produce branch-local
self-product square provenance, or does it only add core-confirmation-only
square nodes from the integer spine?

## Guardrail

This is a depth-vs-retention diagnostic. It is not a win condition and does not
support a primitive-branch ordering law by itself.
