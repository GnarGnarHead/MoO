# Graph-First MoO Corpus

> Status: canonical storage direction for aligned MoO.
>
> Current expanded corpus:
> `out/experiments/strict_stage_graph_u120_20260430.sqlite`
>
> Smoke corpus:
> `out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite`

## Why This Exists

MoO is fundamentally a construction graph, not a list of values.

The graph is the primary method of inspection. A value is only a coordinate in
the graph; the evidence is how that value is produced, how often paths collapse
onto it, which confirmed inputs surround it, and how it relates to nearby nodes.

The core object is:

```text
confirmed iterations
speculative nodes
construction events
many paths collapsing onto the same value
shared construction inputs and graph neighborhoods
```

The previous node-summary strict-stage ledger preserved node summaries and first
construction records. That was useful, but not graph-native. The JSONL artifact
has been purged so it is no longer treated as an active research substrate.

The graph-first corpus fixes that.

Any non-graph report should be treated as a scout or summary. It can point at a
node, but it does not replace graph inspection.

## Canonical Tables

The SQLite corpus stores:

```text
nodes
  node_id
  p
  q
  label
  kind
  first_stage
  confirmed_stage
  first_edge_id

edges
  edge_id
  stage
  op
  left_node_id
  right_node_id
  result_node_id

stages
  stage
  candidate_events
  retained_events
  new_nodes
  new_edges
  total_nodes
  total_edges
  elapsed_seconds
```

The `edges` table is the important shift. It means MoO can ask graph questions
directly:

```text
which constructions produce 34/21?
which nodes share construction inputs?
which paths collapse onto the same value?
what is the local graph neighborhood of a probe-selected node?
which structures are dense by edge count rather than just value proximity?
```

## Strict-Stage Rule

The graph corpus follows the aligned rule:

```text
operands = confirmed core-loop iterations only
outputs = retained speculative nodes
speculative outputs are inspected, not operated on
promotion by the core loop permits later operation
```

At stage `U_n`, new edge occurrences are generated for ordered operand pairs
where at least one operand is the newly confirmed core-loop value `n`. This
stores each confirmed-operand construction at its first possible stage.

## Smoke Run

Command:

```sh
python3 strict_stage_moo.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --max-stage 80 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --summary out/experiments/strict_stage_graph_smoke_20260430_v2_summary.json \
  --quiet --pretty
```

Result:

```text
final stage: U80
nodes:       3,522
edges:       9,559
alignment:   pass
```

Expanded U120 result:

```text
final stage: U120
nodes:       7,798
edges:       20,989
alignment:   pass
```

Node kinds:

```text
certainty:              1
positive integers:     79
rationals:          3,437
relational integers:   5
```

Edge operations:

```text
seed:    1
+:       6
-:   3,550
*:     160
/:   5,842
```

## Graph Query Example

Command:

```sh
python3 moo_graph_query.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --node 34/21 \
  --limit 8 \
  --pretty
```

Result:

```text
34/21 exists as a rational node.
first stage: U34
incoming edges:
  U34: 34 / 21 -> 34/21
  U68: 68 / 42 -> 34/21
outgoing edges:
  none
```

The lack of outgoing edges is correct under aligned MoO. `34/21` is a real
speculative rational node; it is recorded in MoO, but speculative nodes are
inspected rather than operated on.

## Current Query Tools

The graph corpus can now be read through MoO-facing queries:

```sh
python3 moo_graph_query.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --summary --pretty

python3 moo_graph_query.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --node 34/21 --neighborhood --limit 8 --pretty

python3 moo_graph_query.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --compare 34/21 55/34 --limit 8 --pretty

python3 moo_graph_query.py \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --confirmations --limit 20 --pretty
```

These are read-only instruments over the stored graph. They do not change the
MoO run. Their job is to expose:

```text
how a speculative node was produced
which confirmed inputs sit around it
which other nodes share those inputs
which whole-number values were first seen speculatively before the core loop confirmed them
```

## Relationship To Older Artifacts

The old node-summary strict-stage run remains useful only as historical context;
its JSONL ledger has been purged and should not be treated as active storage.

The older exploratory closure corpus remains useful for motif hypotheses, but
it reuses speculative nodes as operands and is not the strict-stage core.

Going forward, serious MoO graph work should use:

```text
moo_graph_corpus.py
strict_stage_moo.py
moo_graph_query.py
```

and should treat node-only ledgers as transitional artifacts.
