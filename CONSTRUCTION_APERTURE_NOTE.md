# Construction Aperture Study

> Status: first corpus-wide metric.
>
> This note records a first pass at measuring how wide a construction path has
> to open before a value becomes visible. The current metric uses saved
> first-witness ancestry from native ledgers; it does not yet prove globally
> minimal aperture over all possible derivations.

## Definition

For a value `x`, define the observed first-witness construction aperture as:

```text
aperture_first(x) =
    max(abs(y)) over y in the saved first-witness ancestry of x
```

Then:

```text
aperture_excess(x) = aperture_first(x) - abs(x)
```

And for a reference cap `C`:

```text
escape_and_return_C(x) =
    abs(x) <= C and aperture_first(x) > C
```

This means the final value lies inside the cap, but its saved first-witness
construction path leaves that cap before folding back.

## Command

The main saved report was generated with:

```sh
python3 construction_aperture_study.py \
  --source-report out/experiments/native_r6_full.json \
  --include-rows \
  --write out/experiments/construction_aperture_r6.json
```

For comparison, the same metric was also run on the `n=5` emergence corpus:

```sh
python3 construction_aperture_study.py \
  --source-report out/experiments/native_r5_full.json \
  --include-rows \
  --write out/experiments/construction_aperture_r5.json
```

## Saturated n=6 Result

Source:

```text
out/experiments/native_r6_full.json
```

Summary:

```text
values: 10655
values with positive aperture excess: 10611

first-witness aperture buckets:
  <= 1      3
  (1,2]    6
  (2,3]    206
  (3,4]    10440
```

For the reference cap `|v| <= 3`:

```text
final values fitting cap:       10145
ancestries fitting cap:           215
escape-and-return values:        9930
```

By first-seen round:

```text
round 3:     5
round 4:   121
round 5:  3829
round 6:  5975
```

This is a strong sign that the default `|v| <= 4` corpus is not simply a
collection of final locations. Much of the saturated field appears through
paths that temporarily use the outer construction scaffold.

The most common first-witness aperture maxima were:

```text
4       9973 values
7/2      201 values
3        184 values
11/3      84 values
19/6      41 values
```

The dominance of `4` is meaningful but also a warning: because the source corpus
itself is capped at `|v| <= 4`, this metric often reports the outer wall of the
chosen aperture. The next version should search for lower-aperture alternate
witnesses before treating `4` as intrinsic.

## n=5 Comparison

Source:

```text
out/experiments/native_r5_full.json
```

Summary:

```text
values: 4439
values with positive aperture excess: 4400

first-witness aperture buckets:
  <= 1      3
  (1,2]    6
  (2,3]    190
  (3,4]    4240
```

For the reference cap `|v| <= 3`:

```text
final values fitting cap:       4154
ancestries fitting cap:          199
escape-and-return values:       3955
```

The `n=5` and `n=6` corpora therefore agree on the broad structure: late
emergent values frequently live inside the lower cap while depending on
first-witness ancestry outside it.

## Inspected Speculative Nodes

All inspected speculative nodes have first-witness aperture `4` in the `n=6`
corpus:

| value | first witness | aperture | cap-3 status |
| --- | --- | ---: | --- |
| `22/7` | `-4/21 - -10/3` | `4` | final value outside cap |
| `87/32` | `-29/8 / -4/3` | `4` | escape-and-return |
| `52/75` | `-13/6 / -25/8` | `4` | escape-and-return |
| `99/70` | `3/14 - -6/5` | `4` | escape-and-return |
| `34/21` | `2/7 - -4/3` | `4` | escape-and-return |

This agrees with the witness-threshold audit while generalizing it. The
inspected nodes are not exceptional merely because they require aperture `4`;
many values do. Their possible interest has to come from aperture plus motif,
center, timing, target-blind ancestry, persistence, and any explicitly external
probe comparison.

## Interpretation

The construction-aperture metric sharpens the project framing:

```text
final value location is not the full object;
the construction corridor is part of the observable.
```

Values can be small in final magnitude while requiring larger intermediate
structures to appear by a given round. This is exactly the kind of
certainty-to-uncertainty-to-return transition that the MoO framing cares about.

## Limitations

This first pass measures:

```text
saved first-witness ancestry
```

It does not measure:

```text
minimum aperture over all derivations
```

The difference matters. A value whose first witness uses `4` may still have an
alternate witness entirely inside `|v| <= 3`, as `34/21` demonstrated in the
witness-threshold audit.

Therefore, construction aperture should currently be read as:

```text
observed first-witness aperture under the source corpus and ordering
```

not as an intrinsic invariant.

## Next Step

The next refinement should search for alternate witnesses with lower aperture.

Candidate metric:

```text
aperture_min_observed(x, r) =
    lowest cap C in a saved or recomputed cap sweep where x appears by round r
```

A cheap first version can reuse the saved `n=5` cap grid:

```text
value caps: 3, 4, 5
q caps: 80, 90, 100
```

A stronger later version would recompute selected values across a finer cap
sweep, such as:

```text
3.00, 3.125, 3.25, 3.5, 3.625, 3.75, 4.00
```

That would separate true aperture dependence from first-witness ordering.
