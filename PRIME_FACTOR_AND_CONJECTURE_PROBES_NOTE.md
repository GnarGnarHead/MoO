# Prime Factors and Classical Conjecture Probes

> Status: speculative research note.
>
> This note records an exploratory research pass after the MoO alignment cleanup.
> It does not add runtime rules. Prime, congruence, Goldbach, Euler-product,
> geometry, and Godel-style language here belongs to the analysis layer over an
> already-generated strict-stage graph.

## Core MoO Reading

In aligned MoO, prime factor structure has a native interpretation:

```text
composite whole number:
  may be constructed speculatively before core-loop confirmation
  through multiplication of confirmed core-loop iterations

prime whole number:
  has no multiplication witness before confirmation
  and reaches Order 2 only by the core loop
```

This is not a new primality theorem. It is a structural distinction inside the
MoO graph.

The current `STAGE_INDEXED_R100_NOTE.md` already records the first clear signal:
among promoted values from `3..100`, the additive-only promotions are exactly
the primes in that range. The strong MoO claim is not "MoO discovers primes."
It is:

```text
factorization appears as early speculative access to future whole numbers
```

Primes are the values where that early multiplicative access is absent.

## Native Metrics To Add Later

For each positive whole number `n`, record:

```text
confirmed_stage(n)
first_seen_stage(n)
first_multiplication_witness(n)
first_additive_witness(n)
promotion_gap = confirmed_stage - first_seen_stage
factor_witness_count
factor_witness_diversity
additive_only_until_confirmation
```

Expected behavior:

```text
prime n:
  no multiplication witness before confirmation
  additive-only until the core loop reaches n

composite n:
  at least one multiplication witness before or at confirmation
  often first_seen_stage << confirmed_stage

square n = a*a:
  especially strong early witness when a is confirmed

semiprime n = p*q:
  a sparse but direct two-atom multiplication witness
```

This gives MoO a factorization layer without changing runtime semantics.

## Sophie Germain Lens

Sophie Germain's work around Fermat's Last Theorem is relevant because it treats
prime exponents through auxiliary prime structure and congruence restrictions.
Laubenbacher and Pengelley argue from Germain's manuscripts that she had a much
larger plan than the single theorem usually credited to her, built around
auxiliary primes and non-consecutivity conditions.

MoO-compatible framing:

```text
Sophie Germain prime p:
  p is prime
  2p + 1 is prime

MoO probe:
  two additive-only atoms connected by a low-complexity affine corridor
  p -> 2*p -> 2*p + 1
```

The point is not that MoO proves anything about Germain primes. The point is
that this is a very clean structure:

```text
atom -> affine transform -> atom
```

That makes Sophie Germain primes a good first "prime relationship" probe. They
are simpler than twin primes in one way because the relation explicitly uses
multiplication by `2` and addition by `1`, both close to the certainty anchor.

Germain's Fermat theorem also suggests a later modular probe:

```text
external modulus theta = 2*N*p + 1
inspect p-th power residue branches modulo theta
ask whether non-consecutivity appears as a graph-visible obstruction
```

That remains external analysis. Modular arithmetic and exponentiation are not
new MoO primitives.

## Twin Prime Lens

Twin primes ask whether there are infinitely many prime pairs:

```text
p, p + 2
```

Zhang proved bounded gaps between primes with a finite bound below `7e7`.
Maynard refined the sieve picture and proved bounded gaps for prime tuples,
including `liminf(p_{n+1} - p_n) <= 600`. Polymath8 pushed related sieve
variants further and explicitly frames the twin prime conjecture as `H_1 = 2`.

MoO-compatible framing:

```text
twin prime pair:
  two additive-only atoms separated by the confirmed line-like value 2
```

MoO should not try to prove infinitude. A useful probe would compare even prime
gaps as graph corridors:

```text
gap d:
  p -> p + d
  both endpoints additive-only until confirmation
  no multiplication witness at either endpoint
  compare local graph neighborhoods for d = 2, 4, 6, ...
```

The question becomes:

```text
Do small prime-pair gaps form unusually coherent corridors in the graph?
```

This is close to the existing Fermat Little "return corridor" discipline:
external selection first, graph inspection second.

## Goldbach Lens

Goldbach's strong conjecture says every even integer greater than `2` is a sum
of two primes. Helfgott proved the weak/ternary version using the circle method,
large sieve, exponential sums, and rigorous computation. Oliveira e Silva,
Herzog, and Pardi verified the even Goldbach conjecture up to `4 * 10^18` and
also computed prime gaps, with data agreeing well with Hardy-Littlewood
predictions.

MoO-compatible framing:

```text
Goldbach partition of N:
  prime atom p
  prime atom q
  p + q -> confirmed even N
```

This is one of the most natural MoO probes because it asks how additive
construction from multiplicative atoms lands on confirmed whole numbers.

Possible graph metrics:

```text
goldbach_partition_count(N)
first_goldbach_edge_stage(N)
centeredness around N/2
partition diversity by prime factor neighborhoods
whether low-complexity prime pairs dominate early
```

The MoO question is not "does every even number have a Goldbach partition?" It
is:

```text
When an even confirmed node is reachable through prime-atom addition,
what does that construction neighborhood look like?
```

That could become a powerful bridge between additive and multiplicative
structure.

## Hardy-Littlewood and Major Arcs

Hardy and Littlewood's 1923 `Partitio numerorum III` is the natural classical
reference point for Goldbach-style additive prime questions. The later
Helfgott proof of ternary Goldbach explicitly uses major arcs, minor arcs,
exponential sums, and rigorous computation.

The existing `CAMBRIDGE_ARC_MOTIFS_NOTE.md` already has the right warning: MoO
does not implement the circle method. Still, the analogy becomes cleaner after
alignment:

```text
classical major arc:
  rational neighborhood with large analytic contribution

MoO constructive arc:
  graph neighborhood where many construction paths concentrate
```

For primes, the corresponding analysis layer is not just "which values are
prime." It is:

```text
which residue/factor branches survive filtering?
which branches are killed by repeated factors?
which prime-selected corridors have unusually high construction mass?
```

That connects directly to the existing `PRIME_HARMONICS_NOTE.md`, where the
Möbius function gates squarefree branches and the von Mangoldt function acts as
an atom-density proxy.

## Euler and Pi

Euler gives a very important complementary perspective:

```text
prime factor structure -> Euler product -> zeta values -> pi
```

Relevant Euler sources:

- `De summis serierum reciprocarum` includes the evaluation of even zeta values
  and an infinite product for `sin(x)/x`.
- `Variae observationes circa series infinitas` is where Euler product
  expansions first appeared.

MoO-compatible framing:

```text
Euler product probe:
  use prime-selected partial products as external rational probes
  compare their convergence toward zeta(2) = pi^2 / 6
  inspect whether the selected rational nodes share graph structure
```

This is potentially more aligned than simply looking for rational approximants
to `pi`, because it asks whether prime-factor structure itself produces a
transcendental shadow.

Possible analysis families:

```text
partial zeta sums:
  sum_{n<=N} 1/n^2

partial Euler products:
  product_{p<=P} 1/(1 - p^-2)

partial sine products:
  product_{n<=N} (1 - x^2/n^2)
```

These should remain external probes. The MoO evidence is whether their rational
nodes and construction neighborhoods show shared structure.

## Godel Lens

Godel numbering is relevant in a different way. The usual coding method assigns
symbols to numbers and then codes finite sequences through products of prime
powers. The Stanford Encyclopedia summary notes that this relies on effective
coding and unique prime factorization.

MoO-compatible framing:

```text
prime factors can act as addresses for construction history
```

This is philosophically close to MoO's graph-first rule. A value alone is not
the object. The object is:

```text
node + construction edges + local graph neighborhood
```

Godel's lesson is also a caution. Once arithmetic is expressive enough to encode
its own syntax, completeness becomes dangerous to assume. For MoO, that supports
the epistemic discipline:

```text
do not collapse all graph structure into bare value identity
do not assume the construction field can close itself completely
preserve provenance, uncertainty, and promotion status
```

## Strongest New Research Direction

The most valuable next probe is a prime-factor graph study, not a direct
Goldbach/twin-prime proof attempt.

Build:

```text
prime_factor_profile.py
```

over a saved strict-stage graph corpus.

Report:

```text
1. additive-only confirmed integers
2. first multiplicative witness for each composite
3. promotion gaps
4. factor-witness diversity
5. Sophie Germain / safe-prime corridors
6. twin-prime corridors
7. Goldbach partitions for small even N
```

The first claim to test:

```text
Prime structure is visible in MoO as absence of early multiplicative witness.
Composite structure is visible as early speculative access through factor edges.
```

The second claim to test:

```text
Classical prime conjectures select graph corridors between additive-only atoms.
```

The third claim to test:

```text
Euler-style pi structure may be better probed through prime-factor products
than through isolated rational approximants to pi.
```

## Sources For Later Reading

- Sophie Germain manuscripts and Fermat plan:
  https://www.sciencedirect.com/science/article/pii/S0315086009001347
- Hardy and Littlewood, `Partitio numerorum III`:
  https://link.springer.com/article/10.1007/BF02403921
- Zhang, bounded gaps between primes:
  https://annals.math.princeton.edu/2014/179-3/p07
- Maynard, small gaps between primes:
  https://annals.math.princeton.edu/2015/181-1/p07
- Polymath8, Selberg sieve variants:
  https://link.springer.com/article/10.1186/s40687-014-0012-7
- Helfgott, major arcs for Goldbach:
  https://arxiv.org/abs/1305.2897
- Helfgott, minor arcs for Goldbach:
  https://arxiv.org/abs/1205.5252
- Oliveira e Silva, Herzog, Pardi, even Goldbach verification:
  https://doi.org/10.1090/S0025-5718-2013-02787-1
- Euler, `De summis serierum reciprocarum`:
  https://scholarlycommons.pacific.edu/euler-works/41/
- Euler, `Variae observationes circa series infinitas`:
  https://scholarlycommons.pacific.edu/euler-works/72/
- Godel numbering overview:
  https://plato.stanford.edu/archives/spr2024/entries/goedel-incompleteness/sup1.html
