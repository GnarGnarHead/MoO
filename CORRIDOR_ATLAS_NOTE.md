# Blind Corridor Atlas

> Status: first target-blind native corridor atlas over the saved `n=6` corpus.
>
> This note deliberately avoids external constant names and geometry labels. It
> asks only: where does MoO's own construction pressure gather?

## Framing

A **corridor** is a recurring first-witness construction region:

```text
operation motif
direct report-level hub
generated-pair channel
```

In this note, the old graph words should be translated as:

```text
parent -> earlier generated construction
child  -> recorded result
hub    -> report-level hub
```

A "child" in older report fields means a recorded first-witness result already
present in the saved `n=6` ledger. It does not mean a projected descendant
beyond the current iteration.

All such constructions and results are generated from `1`; they are not
independent operands.

This is not a claim that the corridor has already been interpreted. The point is
to preserve the native structure before naming it.

The atlas asks:

```text
Which construction regions are heavy before we decide what they mean?
```

## Command

The report was generated from saved ledgers only:

```sh
python3 corridor_atlas_study.py \
  --pretty \
  --write out/experiments/corridor_atlas_r6.json
```

Sources:

```text
native report:    out/experiments/native_r6_full.json
aperture report:  out/experiments/construction_aperture_r6.json
```

No closure recomputation was performed.

## Corpus Summary

```text
values:                    10655
first-witness edges:       10654
operation corridors:          83
report-level hubs:           1571
generated pairs:             7226
```

Older report fields may still use these labels:

```text
parent hubs  -> report-level hubs
parent pairs -> generated-pair channels
```

## Main Native Result

The strongest operation corridors are division-heavy and sit between
mid-/low-denominator rational layers.

Top operation corridors by recorded-result count:

```text
/: mid_q / mid_q, both previous round
recorded results: 2586
derivation mass:   1339957
median aperture:   4

/: mid_q / low_q, both previous round
recorded results: 1071
derivation mass:   1518129
median aperture:   4

/: low_q / mid_q, both previous round
recorded results: 1041
derivation mass:    974868
median aperture:   4
```

The largest corridor by recorded-result count is `mid_q / mid_q`. The largest by
derivation mass among the top corridors is `mid_q / low_q`.

This says something simple and important:

```text
The saturated n=6 field is not organized evenly. A great deal of native
construction pressure gathers in division corridors between already-formed
rational layers.
```

## Aperture Pattern

The main corridors are mostly aperture-4 escape-and-return structures.

For the largest corridor:

```text
/: mid_q / mid_q, both previous round
recorded results:         2586
escape-and-return:        2512
final outside cap 3:        66
ancestry fits cap 3:         8
```

For the second corridor:

```text
/: mid_q / low_q, both previous round
recorded results:         1071
escape-and-return:        1054
final outside cap 3:         2
ancestry fits cap 3:        15
```

So aperture `4` is not just a feature of the external probe nodes. It is a
major native construction layer.

## Report-Level Hubs

Top direct report-level hubs by nontrivial recorded-result count:

```text
-9/5       recorded results 897   derivation mass 538979
-11/5      recorded results 687   derivation mass 358997
-13/5      recorded results 424   derivation mass 196436
-4/3       recorded results 409   derivation mass 990523
-5/3       recorded results 341   derivation mass 758833
-10/7      recorded results 249   derivation mass  48262
-11/3      recorded results 253   derivation mass 395564
-12/5      recorded results 236   derivation mass 106055
```

This confirms the earlier center warning. `-4/3` is not erased; it remains an
important older high-mass hinge. But the blind atlas shows that the strongest
`n=6` recorded-result-count report-level hubs are newer generated values such as
`-9/5`, `-11/5`, and `-13/5`.

The shared supports across the top operation corridors are:

```text
-9/5, -11/5, -13/5, -4/3, -5/3, -10/7, -12/5, -14/5, -7/3, -11/3
```

This is useful because it is not an external interpretation. It is a native
address list for the strongest construction traffic.

## Generated-Pair Channels

The top generated-pair channels are much smaller than the operation corridors.
The leading pair channels have only five recorded results each:

```text
[-4/3, 35/24]     recorded results 5
[-4/3, -19/8]     recorded results 5
[-4/3, -21/8]     recorded results 5
[-5/3, -3/14]     recorded results 5
[-4/3, 25/12]     recorded results 5
[-5/3, -7/16]     recorded results 5
[-4/3, -7/16]     recorded results 5
[-3, -2/3]        recorded results 4
```

Interpretation:

```text
The current atlas is not showing one dominant generated pair. It is showing
broad operation corridors plus recurring report-level hubs.
```

That matters. The structure is more like a field of channels than one magic
edge.

## High-Mass Values

By raw derivation events, the top nontrivial values are still close to the
arithmetic skeleton:

```text
-2/3, 2/3, 3/4, -3/4, 4/3, -4/3, -3, 3, -5/4, 5/4, 5/6, -5/6
```

That is expected. Raw derivation mass alone mostly finds familiar scaffold
values.

The more interesting native-high-corridor values, using a combined corridor
score, are:

```text
95/63, 9/14, 7/10, -9/14, -95/63, -7/10,
15/28, 13/10, 17/10, 9/28, 11/10, -15/28
```

These are not claims of known significance. They are candidates for later
inspection because they sit inside heavy corridors without needing external
labels.

## Interpretation

The blind atlas suggests:

```text
MoO's saturated n=6 structure is dominated by rational division corridors,
especially mid/low denominator interactions whose first-witness ancestry often
escapes to aperture 4 and returns.
```

The useful shape is:

```text
round-4 and round-5 rational report-level hubs
-> division-heavy corridor
-> observed round-5 and round-6 high/mid-q values
-> aperture-4 escape-and-return profile
```

That is a native structure. It should be cataloged before trying to name it as
constant-related, geometry-related, or anything else.

## What This Does Not Say

- It does not prove that any corridor corresponds to a known constant.
- It does not prove that the heavy report-level hubs are universal centers.
- It does not inspect all possible derivations, only saved first witnesses.
- It does not replace the previous binding result; it gives that result a blind
  background.

## Next Questions

1. Do the same operation corridors persist across the saved bounded replay grid?
2. Are `-9/5`, `-11/5`, and `-13/5` real layer report-level hubs or
   saturation artifacts?
3. Do the high-corridor values with no current interpretation form smaller
   families?
4. After the blind pass, which concept/probe cohorts pass through these native
   corridors?
