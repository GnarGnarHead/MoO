# Euler Reciprocal Mass And Circle Lens

> Status: strict research-branch governance.
>
> Euler is useful to MoO because `pi` appears in his work through exact
> arithmetic shadows: reciprocal-square mass, finite products, zeros, and prime
> factorization. This note does not claim that MoO constructs `pi` or defines
> the Euclidean circle. Any later `pi` or circle-like Order-4 language must
> follow `../../ORDER4_PROJECTION_PROTOCOL.md`.

## Claim Boundary

Allowed now:

```text
MoO has unit-quadratic-shell probes over strict graph corpora.
MoO can inspect rational quadratic-shell candidates through graph evidence.
MoO can later inspect Euler-style reciprocal-square and product structures.
MoO may later propose pi-shadow or circle-like Order-4 projected anchors only
after exact source families, projection rules, controls, and held-out tests.
```

Not allowed yet:

```text
MoO defines the circle.
MoO constructs pi.
MoO has sine, angle, circumference, or area as internal objects.
Order-4 anchors can be used as operands or treated as completed Euclidean
objects.
```

The first internal object is not a circle. It is a rational quadratic shell.

## Quadratic Shell First

Define a MoO point as an ordered pair of constructed rational nodes:

```text
(x, y)
```

Define the exact rational form:

```text
Q(x, y) = x*x + y*y
```

For a constructed rational `r`, define:

```text
Shell(r) = {(x, y): Q(x, y) = r*r}
```

This imports no angle, circumference, area, or real completion. It is an
algebraic predicate over rational nodes, and each participating node must be
read through the strict graph corpus.

The correct early claim is:

```text
MoO has rational points satisfying a quadratic invariant.
```

not:

```text
MoO has defined the circle.
```

## Unit-Shell Parametrization

The classical rational parametrization:

```text
x = (1 - t*t) / (1 + t*t)
y = (2*t) / (1 + t*t)
```

is allowed as an analysis-layer generator of exact rational candidates. It is
not, by itself, an internal derivation of the circle.

The strict graph question is:

```text
For a constructed rational t, are the corresponding x and y nodes present in
the strict corpus, and what are their construction witnesses?
```

The first implementation is read-only:

```sh
python3 moo_circle_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --node 3/4 --pretty
python3 moo_circle_probe.py --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --pretty
```

Report language must say `unit_quadratic_shell` or `quadratic_shell`.
`circle-compatible rational probe` belongs only in external interpretation
notes until orbit/refinement criteria exist.

## Q-Preserving Transformations Later

Only after the shell report exists should MoO inspect transformations.

A candidate transformation is admissible only if it is exact-rational and
preserves `Q`:

```text
Q(T(x, y)) = Q(x, y)
```

The first family to inspect is:

```text
[[a, -b],
 [b,  a]]

where a*a + b*b = 1
```

These should be called `Q-preserving transformations`, not rotations, until MoO
has earned angle/orbit language through exact graph behavior.

## Euler Lenses

Euler is best folded in through exact finite rational structures before any
appeal to completed geometry.

### Basel Mass Lens

Track exact rational partial sums:

```text
S_N = 1 + 1/4 + 1/9 + ... + 1/N^2
```

MoO-native observables:

```text
nodes for 1/n^2
partial-sum nodes S_N
first stages
confirmation status
witness diversity
denominator growth
convergence-chain graph structure
```

Allowed claim:

```text
MoO can inspect exact finite reciprocal-square term and partial-sum nodes when
they are present in a strict corpus.
```

Disallowed claim:

```text
MoO constructs pi from zeta(2).
```

### Euler Product Lens

Track finite prime products:

```text
P_N = product over p <= N of 1 / (1 - 1/p^2)
```

MoO-native observable:

```text
Does prime-indexed reciprocal-square construction differ from matched composite
controls in cost, witnesses, neighborhoods, or return behavior?
```

### Zero/Product Lens

Euler's sine-product insight is useful only as a later structural analogy.

Allowed early object:

```text
exact finite product families and return-to-zero corridors
```

Disallowed early object:

```text
sine as a MoO-native function
```

### Delayed Objects

Delay these until strict shell/orbit/return/refinement structures exist:

```text
pi
circumference
area
angle
sine
Euler's e^(ix)
polygon perimeter limits
```

## Controls

Any circle or `pi` lead must beat controls before promotion:

```text
denominator-matched rational controls
construction-cost matched node controls
parametric placebo curves
graph-shuffle nulls
operation-label shuffle nulls
nearby corpus-bound sensitivity checks
held-out strict corpora
```

Failure criteria:

```text
matched placebo curves score similarly
the effect disappears under small bound changes
only one hand-picked node supports it
the metric was chosen after seeing the result
raw approximation to pi is no better than continued-fraction baselines
graph shuffles preserve the signal
```

## First Milestone

Implement:

```text
moo_circle_probe.py
```

as a read-only SQLite report over strict graph corpora.

It should initially report:

```text
unit-shell candidate from t
x and y exact rationals
x*x + y*y = 1 exact check
t/x/y node presence
first stages and confirmation stages
incoming witness counts
operation histograms
baseline features
sign-symmetry coverage
claim_status: observation
```

No new runtime semantics, no schema changes, and no `pi` probe in the first
milestone.
