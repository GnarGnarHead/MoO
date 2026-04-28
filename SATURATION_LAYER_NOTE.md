# Saturation Layer Study

> Status: empirical note.
>
> This note compares the `n = 5` emergence layer with the `n = 6` saturation
> layer in the default bounded MoO corpus. It does not recompute closure.

## Purpose

The `n = 6` run saturated the current bounded value universe:

```text
max_abs_p = 100
max_abs_q = 100
max_abs_value = 4
```

That changes the question. Once all bounded values are present, raw presence is
no longer informative. The important signal becomes first appearance:

```text
What appears before saturation, and through which construction motifs?
```

The script used for this is `saturation_layer_study.py`.

## Reproducible Run

Use the saved `n = 6` native ledger:

```sh
python3 saturation_layer_study.py \
  --report out/experiments/native_r6_full.json \
  --top-k 12 \
  --write out/experiments/saturation_r6.json \
  --pretty
```

The output is:

```text
out/experiments/saturation_r6.json
```

## Saturation Status

| item | count |
| --- | ---: |
| `n=5` retained values | `4439` |
| `n=6` new values | `6216` |
| `n=6` retained values | `10655` |
| bounded value ceiling | `10655` |
| `n=6` candidate events | `112684223` |
| `n=6` retained operation events | `9464091` |

Under these exact bounds, `n = 7` cannot add new retained values. It can only
add derivation-event counts for values already present.

## Layer Contrast

| layer | new values | q median | q min | q max | median derivation events |
| --- | ---: | ---: | ---: | ---: | ---: |
| `n=5` emergence | `4231` | `40` | `5` | `100` | `1298` |
| `n=6` saturation | `6216` | `66` | `11` | `100` | `116` |

The saturation layer is much thinner per value by derivation count, but broader
by value count. It fills the high-denominator remainder of the bounded field.

Denominator buckets:

| bucket | `n=5` | `n=6` |
| --- | ---: | ---: |
| `2-5` | `18` | `0` |
| `6-10` | `101` | `0` |
| `11-25` | `964` | `318` |
| `26-50` | `1439` | `1572` |
| `51-100` | `1709` | `4326` |

First-witness operations:

| op | `n=5` | `n=6` |
| --- | ---: | ---: |
| `+` | `361` | `82` |
| `-` | `771` | `520` |
| `*` | `352` | `306` |
| `/` | `2747` | `5308` |

The saturation layer is overwhelmingly division-built.

## Parent Hubs By Layer

Top `n=5` parent hubs:

| parent | child count | first seen | inspected children |
| ---: | ---: | ---: | --- |
| `-4/3` | `404` | `4` | `34/21`, `87/32` |
| `-5/3` | `341` | `4` | |
| `-11/3` | `251` | `4` | |
| `-7/3` | `237` | `4` | |

Top `n=6` parent hubs:

| parent | child count | first seen | inspected children |
| ---: | ---: | ---: | --- |
| `-9/5` | `897` | `5` | |
| `-11/5` | `687` | `5` | |
| `-13/5` | `424` | `5` | |
| `-10/7` | `249` | `5` | |

This is the key structural shift:

```text
n=5 hubs are mostly round-4 parents feeding emergence.
n=6 hubs are mostly round-5 parents feeding saturation.
```

So `-4/3` was not invalidated. It became part of the earlier hinge layer, while
newer `n=5` values became the dominant parents of the saturated boundary.

## Motifs By Layer

Top `n=5` motifs:

| motif | child count | inspected children |
| --- | ---: | --- |
| `/ : mid_q / mid_q, both previous round` | `969` | `52/75` |
| `/ : mid_q / low_q, both previous round` | `674` | `87/32` |
| `/ : low_q / mid_q, both previous round` | `572` | |
| `- : mid_q - low_q, both previous round` | `245` | `22/7`, `34/21`, `99/70` |

Top `n=6` motifs:

| motif | child count | inspected children |
| --- | ---: | --- |
| `/ : mid_q / mid_q, both previous round` | `1617` | |
| `/ : mid_q / high_q, both previous round` | `990` | |
| `/ : low_q / high_q, both previous round` | `584` | |
| `/ : high_q / low_q, both previous round` | `550` | |
| `/ : low_q / mid_q, both previous round` | `469` | |
| `/ : mid_q / low_q, both previous round` | `397` | |

The `n=6` saturation layer is not dominated by the inspected approximants. It
is dominated by high-denominator division motifs that fill the remaining
bounded field.

## Motif Transition

| transition item | count |
| --- | ---: |
| `n=5` motif families | `47` |
| `n=6` motif families | `46` |
| shared motif families | `30` |
| `n=6`-only motif families | `16` |
| `n=5`-only motif families | `17` |

Strong shared motifs:

| motif | `n=5` | `n=6` | growth |
| --- | ---: | ---: | ---: |
| `/ : mid_q / mid_q, both previous round` | `969` | `1617` | `+648` |
| `/ : low_q / mid_q, both previous round` | `572` | `469` | `-103` |
| `/ : mid_q / low_q, both previous round` | `674` | `397` | `-277` |
| `- : mid_q - low_q, both previous round` | `245` | `176` | `-69` |

Top `n=6`-only motifs:

| motif | `n=6` count |
| --- | ---: |
| `/ : mid_q / high_q, both previous round` | `990` |
| `/ : low_q / high_q, both previous round` | `584` |
| `/ : high_q / low_q, both previous round` | `550` |
| `/ : high_q / mid_q, both previous round` | `222` |

This supports a layered picture:

```text
n=5: mid-q emergence layer
n=6: high-q saturation layer
```

## Inspected Approximants

All inspected approximants first appear in the `n=5` emergence layer:

| fraction | target reading | first witness motif |
| ---: | --- | --- |
| `22/7` | near `pi` | `- : mid_q - low_q, both previous round` |
| `87/32` | near `e` | `/ : mid_q / low_q, both previous round` |
| `52/75` | near `ln(2)` | `/ : mid_q / mid_q, both previous round` |
| `99/70` | near `sqrt(2)` | `- : mid_q - low_q, both previous round` |
| `34/21` | near `phi` | `- : mid_q - low_q, both previous round` |

That is the strongest current framing:

```text
The inspected attractor shadows appear before saturation, in the mid-q emergence
layer, not as arbitrary late fillers in the saturated high-q layer.
```

## Interpretation

This makes `n = 6` valuable even though it saturated the bounded universe.

The result is not:

```text
All rationals appear, therefore the approximants are uninteresting.
```

The result is:

```text
All bounded rationals appear by n=6, so first appearance becomes the signal.
The inspected approximants appear at n=5, before the high-q saturation layer,
and they appear through a small set of major motifs.
```

This is the cleaner MoO claim to pursue.

## Next Question

The next study should score every value in the saturated corpus by:

```text
first_seen_round
first_witness_motif
parent hub ancestry
construction aperture
derivation-event prominence after saturation
```

Then compare inspected approximants against the full `10655`-value population,
not just a small matched-control set.
