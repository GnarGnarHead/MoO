# Residual Emergence Study

> Status: empirical note.
>
> This note records the first target-blind residual study over the round-5 MoO
> closure ledger. It is a calibration result, not a theorem.

## Purpose

Raw derivation multiplicity mostly finds the arithmetic skeleton: `0`, `1`,
`-1`, `1/2`, unit fractions, and boundary-denominator artifacts. That is useful,
but too blunt for the external constant-probe question.

This study asks a narrower question:

```text
After filtering the obvious skeleton, which values are unusually prominent
relative to peers from the same first-seen round and denominator band?
```

The script used for this is `residual_emergence_study.py`.

## Reproducible Run

First compute the target-blind ledger once:

```sh
python3 native_emergence_scan.py --rounds 5 --include-ledger --write out/experiments/native_r5_full.json
```

Then run the residual study without recomputing closure:

```sh
python3 residual_emergence_study.py --report out/experiments/native_r5_full.json --top-k 25 --write out/experiments/residual_r5.json
```

The residual score is:

```text
log1p(derivation_events) - median(log1p(derivation_events) in bucket)
```

scaled by a robust median absolute deviation. Buckets are:

```text
first_seen_round x denominator_band
```

with a round-only fallback for small buckets.

Default filters remove:

- integers,
- denominators smaller than `3`,
- unit fractions,
- values with `abs(value) < 0.05`,
- values near the configured denominator boundary (`q >= 0.9 * max_abs_q`).

## Round-5 Source

The source ledger contains:

| item | count |
| --- | ---: |
| total values | `4439` |
| non-integers | `4430` |
| integers | `9` |
| included after filters | `3899` |
| excluded after filters | `540` |

The filter reasons overlap; a value may have more than one reason.

## Main Residual Signal

The strongest residual values are not the external-probe-selected nodes. The top
residuals are dominated by a small rational lattice around values such as:

| value | first seen | derivation events | residual z | first witness |
| ---: | ---: | ---: | ---: | --- |
| `-3/8` | `4` | `399` | `3.20` | `-3 * 1/8` |
| `3/8` | `4` | `399` | `3.20` | `-3/2 / -4` |
| `-7/60` | `5` | `99` | `2.76` | `-7/3 * 1/20` |
| `7/60` | `5` | `98` | `2.75` | `-7/3 * -1/20` |
| `-9/56` | `5` | `90` | `2.65` | `3/14 / -4/3` |
| `9/56` | `5` | `90` | `2.65` | `-3/14 / -4/3` |
| `4/63` | `5` | `90` | `2.65` | `-4/3 * -1/21` |

This looks like an internal high-traffic rational lattice generated around
round-4 values such as `-4/3`, `3/14`, `1/20`, `1/21`, and `-7/3`.

## Inspected Speculative Nodes

The earlier probe-selected speculative nodes are still present and
constructively clean, but they are not generally top residual hubs under this
metric.

| value | external probe reading | derivation events | residual z | note |
| ---: | --- | ---: | ---: | --- |
| `22/7` | near `pi` | `41` | `-0.77` | nontrivial parents, mixed operation signature |
| `87/32` | near `e` | `24` | `0.46` | nontrivial parents, mixed operation signature |
| `52/75` | near `ln2` | `4` | `-0.67` | clean division witness, low multiplicity |
| `99/70` | near `sqrt2` | `6` | `-0.29` | clean subtraction witness, low multiplicity |
| `34/21` | near `phi` | `47` | `0.79` | strongest residual among this inspected set |

This matters. It says:

```text
being close to an external constant is not the same as being a residual
derivation hub.
```

## Interpretation

The residual study does not write off the external-probe idea. It separates two
phenomena:

- **Residual prominence**: values unusually central after accounting for round
  and denominator band.
- **External probe selection**: speculative nodes that are later recognized as
  close to known constants.

The first residual study supports the existence of nontrivial MoO-native
structure beyond the arithmetic skeleton. It does not, by itself, identify the
externally probe-selected nodes as the most prominent residual hubs.

That is a useful constraint. The next metric should study chains and
approximation direction, not isolated derivation count.

## Working Hypothesis After This Study

MoO closure appears to have at least three distinguishable layers:

1. **Skeleton hubs**: `0`, `1`, `-1`, `1/2`, unit fractions.
2. **Residual rational lattices**: internally high-traffic values like `3/8`,
   `7/60`, `9/56`, and `4/63`.
3. **Probe-selected speculative nodes**: values like `22/7`, `87/32`,
   `52/75`, `99/70`, and `34/21`, which are meaningful only after an explicit
   external test rather than through raw residual multiplicity.

The science should keep these layers separate.
