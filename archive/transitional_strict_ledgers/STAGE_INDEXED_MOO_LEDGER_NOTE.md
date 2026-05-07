# Stage-Indexed MoO Ledger Run

> Status: transitional node-summary ledger.
>
> This run preserved speculative rational nodes and first construction records, but it did
> not preserve every edge occurrence as a graph-native corpus. For current core
> MoO graph work, prefer `../../GRAPH_CORPUS_NOTE.md`, `moo_graph_corpus.py`, and
> `strict_stage_moo.py`.
>
> Summary artifact:
> `out/experiments/stage_indexed_moo_field_rough_20260430.json`
>
> Persisted node ledger:
> purged; do not use this run as active storage.

## Framing

This is a bounded MoO run, not an integer-skeleton shortcut.

The rule is:

```text
confirmed core-loop iterations are operands
speculative outputs are recorded
speculative outputs are real nodes, but not operands until core-loop promotion
```

The run used confirmed operands through:

```text
U1679
```

and retained speculative nodes inside these bounds:

```text
|p| <= 2000
q <= 2000
|value| <= 4
```

So the result is full only inside those explicit bounds. It is not a completed
unbounded MoO field.

## Result

The run stopped at the node cap:

```text
stop reason:       max_nodes
confirmed operands: 1..1679
candidate events:  11,276,164
retained events:    2,482,605
unique nodes:       1,501,001
speculative nodes:  1,500,997
```

Retained status counts:

```text
Order 1 certainty:                    1
Order 2 confirmed core iterations:    3
Order 3 rationals:            1,500,992
Order 3 relational integers:          5
Order 3 not-yet core iterations:      0
```

The low Order 2 count is a consequence of the retained value bound
`|value| <= 4`. The run still used confirmed operands up to `1679`; it simply
did not retain larger positive integers as ledger nodes under this bounded
view.

## Transcendental Probe Shadows

These are external probes over the retained speculative rational field. They
are not MoO-native identities.

```text
pi:
  355/113
  first stage U355 via 355 / 113
  error ~2.67e-7

e:
  1457/536
  first stage U1457 via 1457 / 536
  error ~1.75e-6

ln2:
  1143/1649
  first stage U1649 via 1143 / 1649
  error ~1.81e-7

sqrt2:
  1393/985
  first stage U1393 via 1393 / 985
  error ~3.64e-7

phi:
  1597/987
  first stage U1597 via 1597 / 987
  error ~4.59e-7
```

## First Structural Read

The dominant rational nodes by derivation multiplicity are the simple low
denominator ratios:

```text
1/2   first U2   839 derivation events
3/2   first U3   559 derivation events
1/3   first U3   559 derivation events
2/3   first U3   559 derivation events
4/3   first U4   419 derivation events
1/4   first U4   419 derivation events
3/4   first U4   419 derivation events
```

That is not surprising, but it is useful grounding: under strict stage-indexed
MoO, the densest early rational structures are simple division corridors from
confirmed operands.

The target probes then appear as later, sharper rational shadows inside the
same speculative field. For example:

```text
355/113 appears at U355
1597/987 appears at U1597
1143/1649 appears at U1649
```

The next useful question is not whether these are close in decimal value. It is
whether their first-witness stages, operation signatures, and neighborhood
structure differ from ordinary retained rationals with similar numerator and
denominator sizes.

## Next Step

Use this persisted ledger for analysis before increasing bounds:

```text
1. Compare probe-shadow nodes against matched rational controls.
2. Inspect local neighborhoods around 355/113, 1457/536, 1143/1649, 1393/985, and 1597/987.
3. Measure whether those nodes sit in unusual derivation-multiplicity or denominator neighborhoods.
4. Only then decide whether a larger bounded run is worth the RAM/disk cost.
```
