# Fermat Prime Non-Collapse Probe

> Status: speculative analysis probe.
>
> This is not a new MoO operation and not a proof attempt. It is a graph-inspection
> probe for prime-exponent branch structure.

## Framing

For odd prime `p`, Fermat's Last Theorem says there are no positive whole-number
solutions to:

```text
a^p + b^p = c^p
```

MoO should not treat exponentiation as a new primitive. In this probe,
`a^p`, `b^p`, and `c^p` are external repeated-multiplication targets. The
evidence must come from the graph:

```text
node + construction edges + local graph neighborhood
```

not from the bare equation.

The power targets are analysis-layer selections, not new MoO construction
rules. If a branch value or edge is not present in the saved graph corpus, the
probe treats that as absence in the current run rather than constructing it by
fiat.

## MoO Question

The MoO-readable question is:

```text
Do odd-prime power branches show a distinctive failure to collapse?
```

For `p = 2`, square branches can collapse:

```text
3^2 + 4^2 = 5^2
```

For odd prime `p`, the Fermat branch:

```text
left branch:  a -> a^p, b -> b^p, a^p + b^p
right branch: c -> c^p
```

does not collapse for positive whole-number values.

In MoO, that makes the failure itself the object of inspection:

```text
which branch nodes exist?
which construction edges produce them?
how close are near misses?
do prime exponents create recognizable non-overlap neighborhoods?
```

## Probe Command

```sh
python3 fermat_prime_probe.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --primes 3,5,7 \
  --min-base 2 \
  --max-base 8 \
  --top-k 8 \
  --pretty
```

The current `U80` smoke corpus has tight value bounds, so most higher power
branch nodes are expected to be absent. That absence is useful feedback: this
probe will become more meaningful on a larger graph corpus with bounds chosen to
retain power branches.

## Interpretation Discipline

The probe reports:

```text
collision_count
nearest_non_collapses
graph_rich_branches
```

`collision_count` should remain zero for odd prime exponents over positive
whole-number bases.

`nearest_non_collapses` are not evidence by themselves. They are only candidate
addresses for graph inspection.

`graph_rich_branches` are more MoO-relevant because they ask which Fermat-style
branch targets are actually present as graph nodes with construction edges.
The stricter signal is `found_branch_edges`, not just `found_branch_nodes`: a
whole-number node may exist because the core loop reached it, even when the
specific power/sum branch edge is absent under the current corpus bounds.

## What Would Be Interesting

Potentially useful future observations:

```text
odd-prime branches repeatedly approach collapse but miss by structured gaps
near misses share construction neighborhoods
prime exponents differ from composite exponents in graph-rich branch structure
p = 2 collapse behavior separates sharply from odd-prime non-collapse behavior
```

That would not prove anything about Fermat's theorem. It would give MoO a clean
prime-exponent probe for graph non-collapse.
