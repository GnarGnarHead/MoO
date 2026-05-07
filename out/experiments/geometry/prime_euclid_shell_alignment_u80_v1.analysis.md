# Prime-Euclid Shell Alignment U80 v1 Analysis

> Status: paired analysis note for
> `prime_euclid_shell_alignment_u80_v1.json`.
>
> Evidence layer: strict graph corpus.
>
> Claim status: lead.

## Result Summary

Corpus:

```text
out/experiments/strict_stage_graph_smoke.sqlite
U80
nodes: 3522
edges: 9559
strict alignment: pass
```

Report summary:

```text
candidate_count: 8
complete_family_count: 8
with_any_strict_self_product_witness_count: 4
with_all_strict_self_product_witnesses_count: 0
with_euclid_parameter_count: 8
with_complete_euclid_parameter_nodes_count: 8
with_any_euclid_generator_witness_count: 8
```

## Main Observation

Every complete low-denominator shell-square candidate in this U80 pass clears
to the same primitive integer triple:

```text
3, 4, 5
```

Recovered Euclid parameters:

```text
m = 2
n = 1
m*m - n*n = 3
2*m*n = 4
m*m + n*n = 5
```

This means the first visible shell-square overlap is not yet a family of many
prime structures. It is a family of rational shadows / scalings of the same
primitive `3,4,5` structure.

## Representative Candidates

Low stage-spread candidates:

```text
3, 4, 5          -> primitive 3,4,5; common_denominator 1; stage_spread 23; phase_delta 20
3/5, 4/5, 1      -> primitive 3,4,5; common_denominator 5; stage_spread 24; phase_delta 20
3/4, 1, 5/4      -> primitive 3,4,5; common_denominator 4; stage_spread 24; phase_delta 20
1, 4/3, 5/3      -> primitive 3,4,5; common_denominator 3; stage_spread 24; phase_delta 20
1/2, 2/3, 5/6    -> primitive 3,4,5; common_denominator 6; stage_spread 34; phase_delta 30
3/7, 4/7, 5/7    -> primitive 3,4,5; common_denominator 7; stage_spread 42; phase_delta 42
```

The scaled candidate:

```text
6/5, 8/5, 2
```

integerizes to:

```text
6, 8, 10
```

and then reduces by `gcd = 2` back to:

```text
3, 4, 5
```

## Prime Reading

Primitive factor structure:

```text
3 = 3
4 = 2^2
5 = 5
```

Mod-4 classes:

```text
3 is 3 mod 4
2 is the special even prime
5 is 1 mod 4
```

This is exactly the classical first Pythagorean / Gaussian-norm pattern. The
report does not show that primes explain MoO geometry. It shows that the first
complete shell-square candidates sit on the smallest primitive triple and that
the strict graph already contains the associated Euclid parameter nodes.

Do not use `r*r = 25` as the main obstruction signal. At the completed
radius-square level, even prime exponents are tautological. The useful
inspection target is the primitive radius `5`, the legs `3,4`, and the recovered
Euclid parameters `2,1`.

## Graph Reading

For all eight candidates:

```text
Euclid parameters recovered: yes
parameter nodes present: yes
some Euclid generator witness present: yes
```

The strict graph sees the low-level grammar around:

```text
1
2
4
3
5
```

That is promising because the probe is no longer only asking whether
`x*x + y*y = r*r` holds. It is auditing whether the construction graph contains
the classical generators behind the shell.

## Limits

The result is still narrow:

```text
all complete candidates reduce to 3,4,5
no candidate has all literal strict self-product witnesses
not every Euclid generator edge is retained
size / denominator / parameter controls are not yet satisfied
```

The absence of all literal self-product witnesses is not a geometric failure.
Under strict-stage MoO, rational nodes are not operands, and integer square
edges can be absent when the square fell outside output-retention bounds at the
first possible strict stage.

## Safe Claim

This report supports:

```text
The U80 strict corpus contains complete rational shell-square candidates that
all normalize to the primitive 3,4,5 integer triple; each recovers Euclid
parameters m=2,n=1 and exposes the associated parameter nodes and at least one
strict Euclid-generator witness in the graph.
```

This report does not support:

```text
Primes are the missing piece.
Prime factors explain MoO geometry.
MoO proves new number theory.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## Next Questions

1. Does a larger or differently bounded strict corpus admit complete candidates
   whose primitive triples are not `3,4,5`, such as `5,12,13` or `8,15,17`?
2. Do shell-square candidates group by primitive triple with predictable stage
   spreads, denominator behavior, and witness mass?
3. Are Euclid parameter nodes and generator witnesses visible before, during,
   or after the shell-square family becomes complete?
4. Does prime / Euclid structure explain timing after matching by component
   height, denominator, primitive radius, first-stage bucket, and `m,n` size?
