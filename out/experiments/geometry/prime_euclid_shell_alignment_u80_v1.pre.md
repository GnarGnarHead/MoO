# Prime-Euclid Shell Alignment U80 v1 Preregistration

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
python3 moo_circle_square_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --max-denominator 20 \
  --max-abs-value 5 \
  --require-complete-family \
  --limit 6 \
  --experiment-id prime_euclid_shell_alignment_u80_v1 \
  --with-checksums \
  --write out/experiments/geometry/prime_euclid_shell_alignment_u80_v1.json \
  --pretty
```

## Question

Do complete rational shell-square alignment candidates in the U80 strict corpus
also expose the classical generative grammar after rational normalization?

Measured bridge:

```text
rational shell
-> common-denominator integerized triple
-> primitive integer triple
-> Euclid m,n recovery
-> prime-factor fields
-> strict graph node and witness audit for m,n,m*m,n*n and generated components
```

## Primary Fields

```text
candidate_count
complete_family_count
with_euclid_parameter_count
with_complete_euclid_parameter_nodes_count
with_any_euclid_generator_witness_count
primitive_integer_triple
common_denominator
gcd_integerized_xyz
Euclid m,n
prime mod 4 classes
odd 3 mod 4 prime exponents
strict generator witness presence
stage_spread
phase_delta
```

## Guardrails

This report may support:

```text
The corpus contains rational shell-square candidates whose primitive integer
triples have recovered Euclid parameters and named graph timing / witness
fields for the associated generative components.
```

It may not support:

```text
Primes are the missing piece.
Prime factors explain MoO geometry.
MoO proves Fermat's two-square theorem.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Controls Not Yet Satisfied

This first report exposes the fields. It does not yet prove prime organization
beyond controls. A stronger pass needs matched controls for:

```text
component height
denominator height
common denominator
primitive radius size
first_stage bucket
Euclid m,n size
```
