# Next Steps

> Status: pause point.
>
> Current compute priority is elsewhere. MoO research is parked at generated
> iteration `n = 6` for the default bounded corpus.

## Current State

The latest completed construction depth is:

```text
generated iteration: n = 6
seed state: 1
```

The main saved corpus is:

```text
out/experiments/native_r6_full.json
```

Baseline bounded universe:

```text
rounds: 6
max_abs_p: 100
max_abs_q: 100
max_abs_value: 4
values retained at n=5: 4439
values retained at n=6: 10655
bounded value ceiling: 10655
```

The `n = 6` run saturated the current bounded value universe. Under these exact
bounds, a later iteration cannot add new retained rational values. It may still
add derivation-event counts, but not new values.

The most important result so far:

```text
Round-5 attractor approximants appear inside a late-blooming mid-q motif layer;
some of that layer is organized around high-output rational hinges such as
-4/3.
```

This is evidence of structure, not a proof of transcendental convergence.

## Main Findings To Preserve

1. The inspected approximants were:

```text
22/7      near pi
87/32     near e
52/75     near ln(2)
99/70     near sqrt(2)
34/21     near phi
```

2. In the default `n=5` corpus, all five landed in final major operation
   motifs.

3. The strongest final parent hub was:

```text
-4/3
child_count = 404
inspected children = 34/21, 87/32
```

At `n = 6`, `-4/3` remains active and still directly covers `34/21` and
`87/32`, but it is no longer the top final hub:

```text
-9/5   child_count = 897
-11/5  child_count = 687
-13/5  child_count = 424
-4/3   child_count = 409
```

This is useful: the `n = 5` hinge did not disappear, but a new layer of
stronger `n = 6` hubs appeared.

4. The `3 x 3` bounded replay grid showed:

```text
q caps:      80, 90, 100
value caps:   3,  4,   5
```

- `-4/3` was the top final parent hub in all nine cells.
- All six cells with `|v| >= 4` preserved all five inspected approximants.
- Those six cells preserved the baseline motif membership of all five.
- All three cells with `|v| = 3` preserved only `34/21`.

Interpretation:

```text
MoO is path-sensitive. The final value fitting a bound is not enough; the
construction route has to fit the admissible intermediate field.
```

## Existing Analysis Artifacts

Core reports:

```text
out/experiments/native_r5_full.json
out/experiments/native_r6_full.json
out/experiments/residual_r5.json
out/experiments/motif_r5.json
out/experiments/motif_persistence_r5.json
out/experiments/motif_persistence_r6.json
out/experiments/motif_grid_r5_summary.json
out/experiments/saturation_r6.json
```

Bounded replay ledgers:

```text
out/experiments/native_r5_q80.json
out/experiments/native_r5_q80_v3.json
out/experiments/native_r5_q80_v5.json
out/experiments/native_r5_q90_v3.json
out/experiments/native_r5_q90_v4.json
out/experiments/native_r5_q90_v5.json
out/experiments/native_r5_v3.json
out/experiments/native_r5_v5.json
```

Bounded replay persistence reports:

```text
out/experiments/motif_persistence_r5_q80.json
out/experiments/motif_persistence_r5_q80_v3.json
out/experiments/motif_persistence_r5_q80_v5.json
out/experiments/motif_persistence_r5_q90_v3.json
out/experiments/motif_persistence_r5_q90_v4.json
out/experiments/motif_persistence_r5_q90_v5.json
out/experiments/motif_persistence_r5_v3.json
out/experiments/motif_persistence_r5_v5.json
```

Docs:

```text
TRANSCENDENTAL_ATTRACTORS_NOTE.md
RELATED_WORKS_NOTE.md
RESEARCH_TOOLS_NOTE.md
RESIDUAL_EMERGENCE_NOTE.md
MOTIF_GRAPH_NOTE.md
MOTIF_PERSISTENCE_NOTE.md
SATURATION_LAYER_NOTE.md
CONSTRUCTION_CENTERS_NOTE.md
CAMBRIDGE_ARC_MOTIFS_NOTE.md
```

## Recommended Next Experiment

Use the saturated `n = 6` corpus to score all retained values before increasing
bounds or running derivation-only deeper iterations.

Question:

```text
What distinguishes values first seen in the n=5 emergence layer from values
first seen in the n=6 saturation layer?
```

The first pass is recorded in `SATURATION_LAYER_NOTE.md`. It showed:

```text
n=5: mid-q emergence layer containing the inspected attractor approximants
n=6: high-q, division-heavy saturation layer
```

The center interpretation is recorded in `CONSTRUCTION_CENTERS_NOTE.md`:

```text
MoO appears to produce rational construction centers and motif centers.
The inspected approximants are not themselves centers; they are attractor
shadows downstream of internally generated centers.
```

The next concrete analysis should score every value by:

```text
first_seen_round
first_witness_motif
parent hub ancestry
construction aperture
derivation-event prominence after saturation
```

After that, do the witness-threshold audit.

Question:

```text
Which exact intermediate witnesses force the value threshold between |v| = 3
and |v| = 4 for 22/7, 87/32, 52/75, and 99/70?
```

Why this is the best next step:

- It is cheaper than increasing bounds or running deeper derivation-only passes.
- It uses the now-complete finite corpus under the current bounds.
- It can compare inspected approximants against all `10655` retained values,
  not just a small control set.
- The later witness-threshold audit explains the strongest grid result.

Useful target output:

```text
fraction
first witness under |v| <= 4
which parent is excluded by |v| <= 3
parent ancestry to depth 2 or 3
minimum observed value aperture over the saved grid
```

## Completed Heavy Experiment

The `n = 6` run completed successfully:

```text
n=5 retained values: 4439
n=6 new values: 6216
n=6 retained values: 10655
bounded ceiling: 10655
n=6 candidate events: 112684223
n=6 retained operation events: 9464091
```

The saved report is:

```text
out/experiments/native_r6_full.json
```

The cheap motif-persistence report is:

```text
out/experiments/motif_persistence_r6.json
```

## Do Not Do Next

Do not queue `n = 7` or `n = 8` under the same bounds for value discovery.

The current bounded value universe is saturated at `n = 6`:

```text
current retained values: 10655
bounded ceiling: 10655
```

An `n = 7` run could still increase derivation-event counts for already-known
values, but it should not produce new retained values unless the bounds change.

## Low-Compute Commands

These are safe to run while compute is limited:

```sh
python3 -m py_compile *.py
python3 motif_grid_summary.py --pretty
python3 motif_persistence_study.py --report out/experiments/native_r5_full.json --top-k 12 --pretty
python3 motif_persistence_study.py --report out/experiments/native_r6_full.json --top-k 12 --pretty
python3 residual_emergence_study.py --report out/experiments/native_r5_full.json --top-k 12 --pretty
```
