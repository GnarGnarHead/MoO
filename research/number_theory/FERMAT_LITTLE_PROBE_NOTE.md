# Fermat Little Return-Corridor Probe

> Status: speculative analysis probe.
>
> This is not a new MoO operation and not a proof attempt. It is a graph
> inspection probe for return structure around prime moduli.

## Framing

Fermat's Little Theorem says that, for prime `m`, the value:

```text
a^m - a
```

is divisible by `m`.

MoO should not add modular arithmetic or exponentiation as primitives. This
probe computes the target corridor externally, then asks what the existing MoO
graph actually contains:

```text
a -> a^m -> a^m - a -> (a^m - a) / m
```

The MoO evidence is the graph:

```text
node + construction edges + local graph neighborhood + confirmation status
```

not the bare theorem.

The target values are analysis-layer selections, not new MoO constructions.
If the required nodes or edges are absent from the graph, the probe reports
that absence rather than manufacturing the corridor inside MoO.

## Certainty Anchor Rule

Base `1` is included by default.

In ordinary theorem-probing it is easy to treat `a = 1` as a trivial case. In
MoO that is the wrong default. Self-reference through `1` is exactly the kind
of correlation that matters, because `1` is the only certainty and the anchor
from which later structure becomes interpretable.

The probe may still be run with `--min-base 2` for a comparison pass, but that
is a filtered view, not the default MoO view.

## Probe Command

```sh
python3 fermat_little_probe.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --max-modulus 12 \
  --max-base 8 \
  --top-k 5 \
  --pretty
```

## Interpretation Discipline

The probe reports:

```text
prime_summary
composite_summary
prime_return_failures
composite_integral_returns
graph_rich_returns
```

The clean arithmetic contrast is whether the return is integral. The stricter
MoO signal is whether the return corridor is present in the graph as edges, not
only as values.

The current small graph corpus can show low-stage corridors, especially around
`1` and `2`, but larger modulus/base corridors need a larger graph corpus with
bounds chosen to retain the relevant power, subtraction, and division nodes.

## What Would Be Interesting

Potentially useful future observations:

```text
prime moduli produce return corridors that stay structurally coherent
composite moduli show broken or partial return corridors
self-reference through 1 repeatedly appears as the organizing anchor
graph-rich returns share neighborhoods or confirmation profiles
```

That would not prove Fermat's Little Theorem. It would give MoO a clean
prime/composite probe for return structure around the certainty anchor.
