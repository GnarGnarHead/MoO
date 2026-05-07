# Convergence Structure Over The MoO Ledger

> Status: first structure-first convergence study over the bounded strict-stage
> MoO node-summary ledger.
>
> This is useful as a preliminary chain study, but it is not graph-native. Future
> convergence work should use the SQLite graph corpus so chain nodes can be
> compared by full edge neighborhoods, not only node summaries.
>
> Source ledger:
> purged; this note is historical context for the saved report only.
>
> Report:
> `out/experiments/stage_indexed_convergence_rough_20260430.json`

## Framing

Approximating points are not meaningful by themselves.

A speculative rational node such as:

```text
355/113
```

has value only if it belongs to a broader convergence structure. The point is
not "this fraction is close to pi." The point is whether the fraction appears
as part of a shared, record-improving rational chain inside the MoO ledger.

This study therefore treats external constants as probes only after the ledger
has been generated.

For each target, the script keeps only speculative rational nodes that improve
the best approximation available by stage. It then checks the chain for native
rational structure:

```text
consecutive determinant
side alternation around the target
recurrence: current = a * previous + older
```

The decimal error is reported only as an external label.

## Run Summary

The study scanned:

```text
candidate speculative rationals: 1,500,992
targets: pi, e, ln2, sqrt2, phi
total record-chain nodes: 76
total unimodular steps: 64
total recurrence-supported steps: 32
```

Here "unimodular" means consecutive record nodes have:

```text
|p2*q1 - p1*q2| = 1
```

That is important because determinant-1 adjacency is a structural relation
between rationals. It means the chain is not merely a loose list of close
points; many steps are adjacent in the rational lattice.

## Probe Chains

### pi

Final retained probe shadow:

```text
355/113
```

Record chain length:

```text
18
```

Structural summary:

```text
unimodular steps: 14
recurrence-supported steps: 1
side flips: 3
determinant counts: |det|=1 -> 14, |det|=4 -> 3
```

Selected chain segment:

```text
22/7
179/57
201/64
223/71
245/78
267/85
289/92
311/99
333/106
355/113
```

The `22/7` and `355/113` appearances are therefore not isolated facts in this
bounded ledger. They sit in a rational corridor.

### e

Final retained probe shadow:

```text
1457/536
```

Structural summary:

```text
record chain length: 16
unimodular steps: 13
recurrence-supported steps: 6
side flips: 7
determinant counts: |det|=1 -> 13, |det|=4 -> 2
```

Supported recurrence coefficients observed:

```text
1, 2, 1, 1, 3, 1
```

### ln2

Final retained probe shadow:

```text
1143/1649
```

Structural summary:

```text
record chain length: 14
unimodular steps: 13
recurrence-supported steps: 6
side flips: 7
determinant counts: |det|=1 -> 13
```

This is the cleanest determinant result in the run: every transition in the
record chain is determinant-adjacent.

### sqrt2

Final retained probe shadow:

```text
1393/985
```

Structural summary:

```text
record chain length: 13
unimodular steps: 11
recurrence-supported steps: 7
side flips: 8
determinant counts: |det|=1 -> 11, |det|=4 -> 1
```

### phi

Final retained probe shadow:

```text
1597/987
```

Structural summary:

```text
record chain length: 15
unimodular steps: 13
recurrence-supported steps: 12
side flips: 13
determinant counts: |det|=1 -> 13, |det|=4 -> 1
```

The retained phi chain is the strongest recurrence signal:

```text
3/2
5/3
8/5
13/8
21/13
34/21
55/34
89/55
144/89
233/144
377/233
610/377
987/610
1597/987
```

Every later recurrence-supported step has coefficient `1`, matching the
Fibonacci-style structure expected from the external phi probe.

## Main Takeaway

This is the right kind of evidence to preserve.

The useful claim is not:

```text
MoO found a good approximation to pi/e/ln2/sqrt2/phi.
```

The useful claim is:

```text
External constants select record-improving chains inside the bounded MoO
speculative rational field, and many of those chains have shared rational
structure: determinant adjacency, side alternation, and recurrence.
```

That is still probe-selected, not target-blind discovery. But it is no longer a
single-point approximation story.

## Next Step

The next analysis should ask whether these convergence chains are special
relative to matched rational controls.

Useful controls:

```text
same final stage range
same denominator range
same numerator/denominator size
same first-witness operation
random record chains for numeric decoy targets
```

The core question:

```text
Do known constants select unusually structured chains,
or do all external targets produce similar determinant and recurrence patterns?
```

That is the right test before treating any one chain as meaningful.
