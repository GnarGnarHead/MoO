# Motif Graph Study

> Status: empirical note.
>
> This note records the first parent-motif study over the saved round-5
> target-blind MoO ledger. It does not recompute closure.

## Purpose

The residual study showed that isolated derivation count and attractor
approximation are different phenomena. This study asks a structural question:

```text
Are notable approximants isolated lucky outputs, or do they sit downstream of
reusable construction motifs?
```

The script used for this is `motif_graph_study.py`.

## Reproducible Run

Use the saved native ledger:

```sh
python3 native_emergence_scan.py --rounds 5 --include-ledger --write out/experiments/native_r5_full.json
```

Then run the motif graph study:

```sh
python3 motif_graph_study.py --report out/experiments/native_r5_full.json --top-k 20 --write out/experiments/motif_r5.json
```

The graph is the first-witness parent graph:

```text
parent a, parent b --op--> child
```

It tracks parent hubs, parent-pair motifs, operation motifs, and shared ancestry
for inspected approximants.

## Round-5 Motif Graph Size

| item | count |
| --- | ---: |
| ledger rows | `4439` |
| first-witness edges | `4438` |
| unique parents | `208` |
| unique parent pairs | `2892` |
| operation motifs | `67` |

## Main Signal

The clearest nontrivial parent hub is:

| parent | first seen | child count | nontrivial child count | inspected children |
| ---: | ---: | ---: | ---: | --- |
| `-4/3` | `4` | `404` | `400` | `34/21`, `87/32` |

Its operation profile is broad:

| op | count |
| --- | ---: |
| `+` | `47` |
| `-` | `120` |
| `*` | `59` |
| `/` | `178` |

This is a stronger structural signal than the residual ranking alone. `-4/3`
is not just an approximant; it behaves like a construction hinge.

## Inspected Approximants and Shared Motifs

The inspected attractor approximants are:

```text
22/7, 87/32, 52/75, 99/70, 34/21
```

Their first-witness motifs cluster into a few operation forms:

| motif | child count in graph | inspected children |
| --- | ---: | --- |
| `/ : mid_q_rational / mid_q_rational, both previous round` | `969` | `52/75` |
| `/ : mid_q_rational / low_q_rational, both previous round` | `674` | `87/32` |
| `- : mid_q_rational - low_q_rational, both previous round` | `245` | `22/7`, `34/21`, `99/70` |

This suggests that the approximants are not all produced by one single motif,
but they are not arbitrary either. They sit in a small family of round-5
operations using round-4 rational parents.

## Direct Parent Pairs

The direct parent-pair view is also informative:

| inspected child | parent pair | operation |
| ---: | --- | --- |
| `22/7` | `-10/3`, `-4/21` | subtraction |
| `87/32` | `-29/8`, `-4/3` | division |
| `52/75` | `-13/6`, `-25/8` | division |
| `99/70` | `3/14`, `-6/5` | subtraction |
| `34/21` | `2/7`, `-4/3` | subtraction |

Two inspected approximants directly use `-4/3`:

```text
34/21 = 2/7 - (-4/3)
87/32 = (-29/8) / (-4/3)
```

The shared parent is not itself the target; it is a hinge that helps produce
different attractor shadows.

## Shared Ancestry

At ancestry depth `3`, the inspected approximants share some obvious integer
infrastructure, but one non-integer ancestor stands out:

| ancestor | inspected descendants | child count |
| ---: | --- | ---: |
| `-3` | all five inspected approximants | `54` |
| `4` | all five inspected approximants | `22` |
| `3` | `22/7`, `99/70`, `52/75` | `21` |
| `-4/3` | `34/21`, `87/32` | `404` |

The integer ancestors are expected. The non-integer `-4/3` is more interesting
because it is also a high-output parent hub.

## Interpretation

This study supports the possibility of more complex structure. The current
picture is:

1. **Skeleton**: unavoidable arithmetic infrastructure.
2. **Hinges**: high-output nontrivial parents such as `-4/3`.
3. **Motif families**: operation patterns over round-4 rational parents.
4. **Attractor shadows**: sparse notable approximants downstream of those
   hinges and motifs.

The attractor approximants are not necessarily hubs. Instead, they may be
selected outputs of a larger construction ecology.

This is the empirical base for `CAMBRIDGE_ARC_MOTIFS_NOTE.md`, which treats
high-output rational hinges as possible finite analogues of major arcs or
rational cusps. That comparison is only an analogy, but it gives a useful
research vocabulary for separating local approximation events from wider
motif-level structure.

## Next Question

The next metric should treat motif families as objects:

```text
Which motif families produce chains whose outputs move coherently across rounds?
```

That would connect this motif graph study back to convergence instead of only
one-step parent structure.

The first pass at this is `MOTIF_PERSISTENCE_NOTE.md`. It finds that the
strongest final motifs catch all inspected approximants, but that several of
those motifs are final-round blooms rather than established multi-round
structures in the saved round-5 corpus.
