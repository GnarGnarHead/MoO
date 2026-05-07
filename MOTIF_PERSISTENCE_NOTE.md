# Motif Persistence Study

> Status: empirical note.
>
> This note records the first persistence pass over the saved round-5
> target-blind MoO ledger. It does not recompute closure.

## Purpose

The motif graph study found high-output rational hinges and operation motifs in
the final round-5 graph. This study asks whether those structures persist across
round prefixes or appear only as final-round artifacts.

The script used for this is `motif_persistence_study.py`.

## Reproducible Run

Use the saved native ledger:

```sh
python3 native_emergence_scan.py --rounds 5 --include-ledger --write out/experiments/native_r5_full.json
```

Then run the persistence study:

```sh
python3 motif_persistence_study.py \
  --report out/experiments/native_r5_full.json \
  --top-k 12 \
  --write out/experiments/motif_persistence_r5.json \
  --pretty
```

The study slices the saved first-witness graph by `first_seen_round`. It tracks:

- cumulative and per-round child production,
- active rounds for parent hubs, parent pairs, and operation motifs,
- final major parent hubs and operation motifs,
- whether inspected speculative nodes land in those major structures,
- a deterministic matched-control set selected from comparable nontrivial
  ledger values.

## Round-5 Persistence Graph Size

| item | count |
| --- | ---: |
| ledger rows | `4439` |
| first-witness edges | `4438` |
| unique parents | `208` |
| nontrivial parent candidates | `156` |
| unique parent pairs | `2892` |
| nontrivial parent-pair candidates | `2178` |
| operation motifs | `67` |

## Persistent Hubs

The strongest multi-round parent hubs are mostly low-complexity infrastructure:

| parent | child count | nontrivial child count | active rounds |
| ---: | ---: | ---: | --- |
| `4` | `22` | `18` | `3, 4, 5` |
| `3` | `21` | `17` | `3, 4, 5` |
| `-3` | `54` | `47` | `4, 5` |
| `4/3` | `27` | `27` | `4, 5` |
| `-4` | `29` | `25` | `4, 5` |
| `-2/3` | `21` | `21` | `4, 5` |

This is useful but not surprising. Persistent activity first appears in the
arithmetic scaffold before the more complex final-round rational field opens.

## Final Major Hubs

The largest nontrivial final parent hub is still:

| parent | child count | nontrivial child count | active rounds | inspected children |
| ---: | ---: | ---: | --- | --- |
| `-4/3` | `404` | `400` | `5` | `34/21`, `87/32` |

Its operation profile remains broad:

| op | count |
| --- | ---: |
| `+` | `47` |
| `-` | `120` |
| `*` | `59` |
| `/` | `178` |

The important caution is that `-4/3` is not yet proven persistent in this
round-5 corpus. It is a major final-round hinge. To show persistence, we need
either round 6 or a second bounded corpus where comparable hinges reappear.

## Operation Motifs

All inspected speculative nodes land inside final major operation motifs:

| motif | child count | active rounds | inspected children |
| --- | ---: | --- | --- |
| `/ : mid_q_rational / mid_q_rational, both previous round` | `969` | `5` | `52/75` |
| `/ : mid_q_rational / low_q_rational, both previous round` | `674` | `5` | `87/32` |
| `- : mid_q_rational - low_q_rational, both previous round` | `245` | `5` | `22/7`, `34/21`, `99/70` |

One motif class has genuine round-prefix persistence:

| motif | child count | active rounds | timeline |
| --- | ---: | --- | --- |
| `/ : low_q_rational / low_q_rational, both previous round` | `173` | `4, 5` | `29 -> 173` |

This suggests a cascade:

```text
low-q rational motifs persist first;
mid-q major motifs bloom later;
probe-selected speculative nodes appear inside the mid-q bloom.
```

That is compatible with the "constructive arcs" reading, but it is not yet a
proof of it.

## Inspected vs Matched Controls

The study compared the five inspected speculative nodes:

```text
22/7, 87/32, 52/75, 99/70, 34/21
```

against 25 deterministic matched controls selected by first-seen round,
denominator scale, and absolute value distance.

| group | major parent hits | major motif hits | any major hits |
| --- | ---: | ---: | ---: |
| inspected | `2/5 = 0.40` | `5/5 = 1.00` | `5/5 = 1.00` |
| matched controls | `8/25 = 0.32` | `18/25 = 0.72` | `18/25 = 0.72` |

This is a positive result, but a modest one:

- The inspected speculative nodes are more concentrated in major structures than
  the controls.
- The gap is not decisive because the major operation motifs are broad.
- Parent-hub concentration is more selective than motif concentration, but only
  two inspected speculative nodes directly hit final major parents.

## Bounded Replay Robustness

To test whether the round-5 result was only an artifact of the exact default
bounds, three bounded replays were run:

```sh
python3 native_emergence_scan.py --rounds 5 --max-abs-p 100 --max-abs-q 80 \
  --max-abs-value 4.0 --top-k 8 --include-ledger \
  --write out/experiments/native_r5_q80.json

python3 native_emergence_scan.py --rounds 5 --max-abs-p 100 --max-abs-q 100 \
  --max-abs-value 3.0 --top-k 8 --include-ledger \
  --write out/experiments/native_r5_v3.json

python3 native_emergence_scan.py --rounds 5 --max-abs-p 100 --max-abs-q 100 \
  --max-abs-value 5.0 --top-k 8 --include-ledger \
  --write out/experiments/native_r5_v5.json
```

Each replay was then passed through `motif_persistence_study.py`, producing:

```text
out/experiments/motif_persistence_r5_q80.json
out/experiments/motif_persistence_r5_v3.json
out/experiments/motif_persistence_r5_v5.json
```

This was then expanded to a `3 x 3` bounded grid:

```text
q cap:      80, 90, 100
value cap:   3,  4,   5
```

The grid summary was produced with:

```sh
python3 motif_grid_summary.py --pretty \
  --write out/experiments/motif_grid_r5_summary.json
```

### Summary Table

| corpus | size | inspected present | top final parent | inspected major motif hits | controls major motif hits |
| --- | ---: | ---: | --- | ---: | ---: |
| default `q<=100, |v|<=4` | `4439` | `5/5` | `-4/3` with `404` children | `5/5 = 1.00` | `18/25 = 0.72` |
| tighter `q<=80, |v|<=4` | `3844` | `5/5` | `-4/3` with `398` children | `5/5 = 1.00` | `20/25 = 0.80` |
| tighter `q<=100, |v|<=3` | `1475` | `1/5` | `-4/3` with `177` children | `1/1 = 1.00` | `23/25 = 0.92` |
| wider `q<=100, |v|<=5` | `5222` | `5/5` | `-4/3` with `371` children | `5/5 = 1.00` | `18/25 = 0.72` |

### 3x3 Grid

| q cap | value cap | size | inspected present | `-4/3` children | baseline motif matches | controls major motif hits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `80` | `3` | `1385` | `1/5` | `177` | `0/5` | `23/25` |
| `80` | `4` | `3844` | `5/5` | `398` | `5/5` | `20/25` |
| `80` | `5` | `4484` | `5/5` | `364` | `5/5` | `20/25` |
| `90` | `3` | `1445` | `1/5` | `177` | `0/5` | `23/25` |
| `90` | `4` | `4148` | `5/5` | `402` | `5/5` | `20/25` |
| `90` | `5` | `4830` | `5/5` | `367` | `5/5` | `18/25` |
| `100` | `3` | `1475` | `1/5` | `177` | `0/5` | `23/25` |
| `100` | `4` | `4439` | `5/5` | `404` | `5/5` | `18/25` |
| `100` | `5` | `5222` | `5/5` | `371` | `5/5` | `18/25` |

The grid result is stronger than the first replay:

- `-4/3` is the top final parent hub in all nine cells.
- All six cells with `|v| >= 4` preserve all five inspected speculative nodes.
- Those same six cells preserve the baseline first-witness motif membership for
  all five inspected speculative nodes.
- All three cells with `|v| = 3` preserve only `34/21`; `22/7`, `87/32`,
  `52/75`, and `99/70` disappear.

The denominator replay is the cleanest robustness check. Lowering the
denominator cap from `100` to `80` preserves all inspected speculative nodes, keeps
`-4/3` as the top final parent hub, and preserves the same three inspected
operation motifs:

```text
- : mid_q_rational - low_q_rational, both previous round
/ : mid_q_rational / low_q_rational, both previous round
/ : mid_q_rational / mid_q_rational, both previous round
```

The wider value replay also preserves the main structure. The motif order shifts
slightly, but the inspected speculative nodes keep the same first-witness motif
families, and `-4/3` remains the top final parent hub.

The tighter value row is different. It is not a clean refutation; it removes
many necessary intermediate parents. Only `34/21` remains among the inspected
speculative nodes for every denominator cap tested. This shows that the construction
path is sensitive to the admissible intermediate field, especially because some
witnesses pass through values whose absolute value exceeds `3`.

## Robustness Interpretation

The bounded grid improves the case for real structure:

1. `-4/3` remains the leading final parent hub throughout the grid.
2. The inspected speculative nodes keep the same motif memberships across every
   tested cell with `|v| >= 4`.
3. The major motifs remain broad, so concentration is still not decisive by
   itself.
4. The `|v| = 3` row shows that MoO construction is path-sensitive: excluding
   intermediate witnesses can erase nodes even when the node
   itself would fit inside the final numeric window.

That last point is important. It supports the constructionist reading: the
availability of the path matters, not only the final value.

## Iteration 6 Update

The default corpus was later extended to `n = 6`:

```sh
python3 native_emergence_scan.py \
  --rounds 6 \
  --include-ledger \
  --write out/experiments/native_r6_full.json
```

The run saturated the current bounded value universe:

| item | count |
| --- | ---: |
| `n=5` retained values | `4439` |
| `n=6` new values | `6216` |
| `n=6` retained values | `10655` |
| bounded value ceiling | `10655` |
| `n=6` candidate events | `112684223` |
| `n=6` retained operation events | `9464091` |

The cheap persistence pass:

```sh
python3 motif_persistence_study.py \
  --report out/experiments/native_r6_full.json \
  --top-k 12 \
  --write out/experiments/motif_persistence_r6.json \
  --pretty
```

showed that `-4/3` remains active, but a new `n=6` hub layer overtakes it:

| final parent | child count | active rounds | inspected children |
| ---: | ---: | --- | --- |
| `-9/5` | `897` | `6` | |
| `-11/5` | `687` | `6` | |
| `-13/5` | `424` | `6` | |
| `-4/3` | `409` | `5, 6` | `34/21`, `87/32` |

The inspected speculative nodes still land in major operation motifs at `n=6`:

| group | major parent hits | major motif hits | any major hits |
| --- | ---: | ---: | ---: |
| inspected | `2/5 = 0.40` | `5/5 = 1.00` | `5/5 = 1.00` |
| matched controls | `6/25 = 0.24` | `15/25 = 0.60` | `16/25 = 0.64` |

This strengthens the motif story. The `n=5` hinge did not vanish; it became
part of a larger saturated `n=6` ecology.

## Interpretation

This does not write off the idea. It sharpens it.

The current evidence says:

1. MoO definitely has high-output rational influence structures.
2. The inspected speculative nodes are not outside those structures.
3. Final major operation motifs are broad enough that they also catch many
   controls.
4. The specific `-4/3` hinge is strong, survives the bounded grid, and remains
   active at `n=6`, but new `n=6` hubs overtake it.

So the next scientific claim should not be:

```text
The round-5 motifs prove transcendental convergence.
```

It should be:

```text
Round-5 probe-selected speculative nodes appear inside a late-blooming mid-q
motif layer; some of that layer is organized around high-output rational hinges
such as -4/3.
```

## Next Question

The next useful experiment is a witness-threshold audit:

```text
Which exact intermediate witnesses force the value threshold between |v| = 3
and |v| = 4 for 22/7, 87/32, 52/75, and 99/70?
```

That would turn the disappearance row into a concrete construction-path result
instead of only a boundary observation.
