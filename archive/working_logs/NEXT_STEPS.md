# Next Steps

> Status: archived pause point.
>
> Current default bounded corpus is parked at generated iteration `n = 6`.
> Current canonical strict-stage graph corpus smoke run has confirmed operands
> through `U80`.
> Some document references preserve their original flat-layout names. Use
> `../../DOCS_INDEX.md` for the current repository map.

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

The canonical storage direction is now graph-first SQLite. A strict-stage graph
corpus smoke run has been built:

```text
db:      out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite
summary: out/experiments/strict_stage_graph_smoke_20260430_v2_summary.json
note:    GRAPH_CORPUS_NOTE.md
```

Smoke result:

```text
confirmed operands: 1..80
nodes:              3,522
edges:              9,559
```

The earlier strict-stage node-summary run reached confirmed core-loop operands
through `U1679`, preserving bounded speculative rational summaries and first
construction records. The JSONL ledger has been purged; only the summary and
derived reports remain as historical context:

```text
summary: out/experiments/stage_indexed_moo_field_rough_20260430.json
note:    STAGE_INDEXED_MOO_LEDGER_NOTE.md
```

That run is transitional because it stored node summaries rather than full graph
edges:

```text
unique retained nodes: 1,501,001
speculative nodes:    1,500,997
retained events:      2,482,605
confirmed operands:   1..1679
```

A first convergence-chain study over that ledger is recorded in:

```text
report: out/experiments/stage_indexed_convergence_rough_20260430.json
note:   CONVERGENCE_STRUCTURE_NOTE.md
```

This study preserves the key discipline:

```text
approximating points are not meaningful alone
they matter only if they belong to shared convergence structure
```

Initial result:

```text
candidate speculative rationals: 1,500,992
record-chain nodes across pi/e/ln2/sqrt2/phi: 76
unimodular chain steps: 64
recurrence-supported steps: 32
```

The most important result so far:

```text
Round-5 probe-selected speculative nodes appear inside a late-blooming mid-q
motif layer; some of that layer is organized around high-output rational hinges
such as -4/3.
```

Philosophical alignment:

```text
I think, therefore 1.
```

`1` is the only certainty. MoO began as a failed attempt to prove `2` from `1`;
that failure matters because `2` requires iteration, memory, and preservation of
a prior `1`. In this framing, `2` is infinite distance from `1`. Every later
value in the ledgers is generated from `1`, not assumed as an independent
operand.

This is evidence of structure, not a proof of transcendental convergence.

## Main Findings To Preserve

1. The inspected speculative nodes were:

```text
22/7
87/32
52/75
99/70
34/21
```

Their constant labels are external probe readings, not MoO-native identity.

2. In the default `n=5` corpus, all five landed in final major operation
   motifs.

3. The strongest final report-level hub was:

```text
-4/3
recorded result count = 404
inspected results = 34/21, 87/32
```

At `n = 6`, `-4/3` remains active and still directly covers `34/21` and
`87/32`, but it is no longer the top final report-level hub:

```text
-9/5   recorded result count = 897
-11/5  recorded result count = 687
-13/5  recorded result count = 424
-4/3   recorded result count = 409
```

This is useful: the `n = 5` hinge did not disappear, but a new layer of
stronger `n = 6` report-level hubs appeared.

4. The `3 x 3` bounded replay grid showed:

```text
q caps:      80, 90, 100
value caps:   3,  4,   5
```

- `-4/3` was the top final report-level hub in all nine cells.
- All six cells with `|v| >= 4` preserved all five inspected speculative nodes.
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
WITNESS_THRESHOLD_NOTE.md
CONSTRUCTION_APERTURE_NOTE.md
CONCEPT_BRANCHES_NOTE.md
BINDING_STRUCTURE_NOTE.md
GEOMETRIC_PROBES_NOTE.md
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
n=5: mid-q emergence layer containing the inspected speculative nodes
n=6: high-q, division-heavy saturation layer
```

The center interpretation is recorded in `CONSTRUCTION_CENTERS_NOTE.md`:

```text
MoO appears to produce rational construction centers and motif centers.
The inspected speculative nodes are not themselves centers; they appear
downstream of internally generated centers.
```

The first corpus-wide scoring pass is now partially complete. Existing scores
cover:

```text
first_seen_round
first_witness_motif
support-concentration ancestry
construction aperture
derivation-event prominence after saturation
```

The remaining refinement is to make `construction_aperture` less dependent on
the saved first-witness ordering by searching for alternate lower-aperture
witnesses.

The witness-threshold audit has also been completed.

Question:

```text
Which exact intermediate witnesses force the value threshold between |v| = 3
and |v| = 4 for 22/7, 87/32, 52/75, and 99/70?
```

Why this is the best next step:

- It is cheaper than increasing bounds or running deeper derivation-only passes.
- It uses the now-complete finite corpus under the current bounds.
- It can compare inspected speculative nodes against all `10655` retained values,
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

The witness-threshold audit is now recorded in `WITNESS_THRESHOLD_NOTE.md`.
The saved report is:

```text
out/experiments/witness_threshold_r5.json
out/experiments/construction_aperture_r5.json
out/experiments/construction_aperture_r6.json
```

Result:

```text
22/7    is excluded directly by |v| <= 3
87/32   is blocked by parent -29/8
52/75   is blocked by parent -25/8
99/70   is blocked by round delay: 3/14 appears one round too late
34/21   survives by an alternate witness
```

The next refinement is to turn this into a general `construction_aperture`
metric: for every value, measure whether it needs temporary excursions beyond
the final value region in order to appear by a given round.

That first metric is now recorded in `CONSTRUCTION_APERTURE_NOTE.md`. In the
saturated `n=6` corpus, `10145` values fit inside `|v| <= 3`, but `9930` of
those have saved first-witness ancestry that leaves `|v| <= 3` before returning.

Important limitation:

```text
current metric = saved first-witness aperture
not yet       = minimum aperture over all possible witnesses
```

The next analysis should search for alternate lower-aperture witnesses, starting
with the saved `n=5` cap grid before recomputing anything expensive.

The first concept-family study is now recorded in `CONCEPT_BRANCHES_NOTE.md`.
It separates the likely anchor from the measured family:

```text
point/certainty anchor: 1 / primitive seed
line/relation anchor: 2 / first constructed separation
the square anchor: 4 / fourfold
the squares family: exact square values and self-product timing
the triangle anchor: 3 / threefold
the triangles family: exact triangular values and weak formula-route timing
```

For the squares family in the saturated `n=6` corpus:

```text
exact rational square values: 49
self-product first witnesses: 9
self-product-on-time values: 47
```

This suggests the squares family is visible natively through root
availability and self-product timing, even when the saved first witness is not
itself multiplication.

The triangle calibration is also recorded in `CONCEPT_BRANCHES_NOTE.md`:

```text
exact nonnegative triangular values: 43
triangle formula route available:    29
triangle formula on-time values:      2
integer triangular scaffold values:   3
```

Interpretation:

```text
trianglehood is accessible as an abstraction, but it is not yet a clean native
timing branch like squarehood. Anchor 3 is meaningful as first nontrivial
additive closure, while the rational triangular family is a diffuse cohort.
```

The first binding-profile study is now recorded in `BINDING_STRUCTURE_NOTE.md`.
It treats external constants only as probes that select already-emergent
speculative nodes.

Result:

```text
probe-selected nodes:       22/7, 87/32, 52/75, 99/70, 34/21
present in corpus:          5 / 5
first-seen round:           5 / 5 at round 5
first-witness aperture:     5 / 5 at aperture 4
first-witness operations:   3 subtraction, 2 division
```

Interpretation:

```text
The inspected nodes are not just approximants. They share a late, aperture-4,
mid-q construction layer with recurring motif and ancestry structure.
```

Saved report:

```text
out/experiments/binding_structure_r6.json
```

## Motif-Mass Study

The first measure-style pass is now recorded in `MOTIF_MASS_NOTE.md`.

It reads saved reports only and does not recompute closure:

```sh
python3 motif_mass_study.py --pretty --write out/experiments/motif_mass_r6.json
```

Result:

```text
values:                    10655
first-witness edges:       10654
operation motifs:             83
report-level hubs:           1571
generated pairs:             7226
```

Largest operation motif:

```text
/: mid_q_rational / mid_q_rational, both previous round
recorded results: 2586
derivation mass:  1339957
```

Binding probes compared with saved matched controls:

```text
binding median motif dependent count: 421
control median motif dependent count: 226
binding major motif rate:           1.00
control major motif rate:           0.60
median aperture:                    4 for both
```

Interpretation:

```text
The binding probes are not distinctive merely because they sit at aperture 4.
The current signal is that all five sit inside major operation motifs, with
higher median motif mass than matched controls.
```

Saved report:

```text
out/experiments/motif_mass_r6.json
```

## Blind Corridor Atlas

The first target-blind corridor atlas is now recorded in
`CORRIDOR_ATLAS_NOTE.md`.

It uses no external constant names or geometry labels:

```sh
python3 corridor_atlas_study.py --pretty --write out/experiments/corridor_atlas_r6.json
```

Result:

```text
values:                    10655
first-witness edges:       10654
operation corridors:          83
report-level hubs:           1571
generated pairs:             7226
```

Top operation corridors:

```text
/: mid_q / mid_q, both previous round   recorded results 2586
/: mid_q / low_q, both previous round   recorded results 1071
/: low_q / mid_q, both previous round   recorded results 1041
```

Top shared report-level hubs across the strongest operation corridors:

```text
-9/5, -11/5, -13/5, -4/3, -5/3, -10/7, -12/5, -14/5, -7/3, -11/3
```

Interpretation:

```text
MoO's saturated n=6 structure is dominated by division-heavy rational
corridors, especially mid/low denominator interactions with aperture-4
escape-and-return behavior.
```

Here "dependents" means observed first-witness dependents already present inside
the saved `n=6` ledger, not projected descendants beyond `n`.

Saved report:

```text
out/experiments/corridor_atlas_r6.json
```

## Speculative Analysis Layer

Geometry probes should remain pure analysis-layer work for now. They are
speculative subsets of the emergent arithmetic pattern, not runtime semantics.

The philosophical anchor ladder to preserve is:

```text
1        -> point / certainty / center
2        -> line / first generated value beyond certainty / infinite distance from 1
3        -> triangle / threefold
4        -> square / fourfold
infinity -> unbounded extension / rotation-limit reading
```

This helps, but only as framing. It should not override the MoO rule that
speculative nodes enter the corpus only when the construction actually produces
them.

The right first framing is:

```text
emergent construction field
-> explicit constraint signature
-> probe subset
-> possible concept branch
```

Good first probes:

- square/fourfold signatures: anchor `4`, self-products, odd-increment growth,
  area/grid behavior, and diagonal shadows;
- triangle/threefold signatures: anchor `3`, triangular-number growth, and
  threefold constraint probes;
- circle signatures: `pi`/`tau` shadows, polygon-refinement behavior, and
  area/circumference projections;
- circle-square bridge signatures: `sqrt(pi)`, `pi/2`, `sqrt2/2`, `1/2`, and
  `1/sqrt(pi)`.

See `GEOMETRIC_PROBES_NOTE.md`.

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
python3 binding_structure_study.py --pretty
python3 motif_mass_study.py --pretty
python3 corridor_atlas_study.py --pretty
```
