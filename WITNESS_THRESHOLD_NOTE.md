# Witness Threshold Audit

> Status: completed local audit.
>
> This note records the first pass at explaining why the inspected round-5
> speculative nodes survive under `|v| <= 4` but mostly disappear under
> `|v| <= 3`.
> The audit uses saved native ledgers and does not recompute closure.

## Inputs

Baseline reports:

```text
low aperture:   out/experiments/native_r5_v3.json
high aperture:  out/experiments/native_r5_full.json
```

Shared bounds except value aperture:

```text
rounds: 5
max_abs_p: 100
max_abs_q: 100
low max_abs_value: 3
high max_abs_value: 4
```

Audit command:

```sh
python3 witness_threshold_study.py --pretty --write out/experiments/witness_threshold_r5.json
```

The script compares first-witness ancestry in the `|v| <= 4` ledger against
presence, timing, and admissibility in the `|v| <= 3` ledger.

## Main Result

Across the saved `q = 80, 90, 100` grid:

```text
minimum observed value cap for 22/7:  4
minimum observed value cap for 87/32: 4
minimum observed value cap for 52/75: 4
minimum observed value cap for 99/70: 4
minimum observed value cap for 34/21: 3
```

At `|v| <= 3`, only `34/21` survives among the inspected set.

The important detail is that most missing values are not missing because their
final numeric value lies outside the low aperture:

```text
22/7    final value is outside |v| <= 3
87/32   final value is inside |v| <= 3, but witness parent -29/8 is outside
52/75   final value is inside |v| <= 3, but witness parent -25/8 is outside
99/70   final value is inside |v| <= 3, and immediate parents survive, but one
        parent arrives one round too late
34/21   survives under |v| <= 3 by an alternate witness
```

## Target Details

### 22/7

High-aperture first witness:

```text
-4/21 - -10/3 = 22/7
```

Under `|v| <= 3`:

- `22/7` is directly excluded because `22/7 > 3`;
- `-10/3` is also excluded because `|-10/3| > 3`;
- `-4/21` survives but is delayed from round 4 to round 5.

This is the least subtle case: the final value itself needs the wider aperture.

### 87/32

High-aperture first witness:

```text
-29/8 / -4/3 = 87/32
```

Under `|v| <= 3`:

- `87/32` is numerically admissible;
- `-4/3` survives at round 4;
- `-29/8` is excluded because `|-29/8| = 3.625`.

So `87/32` is not blocked by its final value. It is blocked by a round-4
excursion outside the tighter aperture.

### 52/75

High-aperture first witness:

```text
-13/6 / -25/8 = 52/75
```

Under `|v| <= 3`:

- `52/75` is numerically admissible;
- `-13/6` survives at round 4;
- `-25/8` is excluded because `|-25/8| = 3.125`.

This is another aperture-mediated return: the final value is small, but the
construction needs a larger intermediate.

### 99/70

High-aperture first witness:

```text
3/14 - -6/5 = 99/70
```

Under `|v| <= 3`:

- `99/70` is numerically admissible;
- `-6/5` survives at round 4;
- `3/14` survives, but slips from round 4 to round 5;
- therefore the same witness would first be available at round 6, outside the
  saved round-5 budget.

The delay traces back to high-aperture ancestry involving `7/2` and `4`.

This is the cleanest evidence that the aperture change is not merely a final
value filter. It changes construction timing.

### 34/21

High-aperture first witness:

```text
2/7 - -4/3 = 34/21
```

Under `|v| <= 3`, that same witness is delayed because `2/7` slips from round 4
to round 5. But `34/21` still appears at round 5 through an alternate witness:

```text
-17/6 / -7/4 = 34/21
```

This makes `34/21` a useful control. It is not immune to aperture effects, but
it has an alternate path that keeps it inside the lower aperture.

## Interpretation

The `|v| = 3 -> 4` threshold is a construction-aperture effect, not merely a
location effect.

The wider aperture admits a round-4 scaffold just outside the tighter field:

```text
-25/8
-10/3
7/2
-7/2
-29/8
4
```

Those values are not the inspected speculative nodes themselves. They are
intermediate structures that let the round-5 layer fold back into smaller
values such as `87/32`, `52/75`, and `99/70`.

That supports the current MoO framing:

```text
final value location is not enough;
the construction route and round timing are part of the observable structure.
```

## Next Use

Promote `construction_aperture` into a reusable metric.

For each value, track:

- whether the final value fits a bound;
- the maximum absolute value needed by its first-witness ancestry;
- whether tighter bounds delay a parent;
- whether alternate witnesses preserve the value under tighter constraints.

This would let MoO ask a sharper question:

```text
Which values require temporary excursions beyond the final value region in
order to become constructible by a given round?
```
