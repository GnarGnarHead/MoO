# Project Alignment Note

> Status: canonical layer map for keeping MoO results in alignment.

## Core Commitment

The aligned MoO framing is:

```text
1 is the only certainty
positive whole numbers enter by the core iteration of 1
speculative constructions are real MoO nodes
speculative constructions carry weaker epistemic status until confirmed
speculative nodes are inspected and speculated on, not operated on
only confirmed core-loop iterations are operands
promotion by the core loop is what permits further speculation
MoO does not speculate on speculations
projected objects are analysis anchors, not certainties or operands
```

This is both an ontology/status rule and a compute rule. A speculative node
exists once it is constructed and recorded; it is just not as epistemologically
sound as `1` or a confirmed iteration of `1`. Because it is speculative, it is
not used as an operand. It can be inspected, compared, labeled, or selected by a
probe, but it is not operated on unless the core loop later confirms it.
Once promoted to that higher epistemological certainty, it can participate in
further speculation.
Any result that operates on speculative nodes may still be useful as historical
context, but it is not aligned MoO computation.

The primary method of inspection is graph inspection. Values, approximations,
probe labels, and node summaries are not primary evidence unless they are read
through construction edges, repeated paths, neighborhoods, and confirmation
transitions.

Order-4 projected objects may be proposed from stable graph families, but they
remain analysis-layer anchors. They are not runtime nodes, operands, confirmed
facts, theorems, or completed objects inside strict MoO.

## Layer 1: Strict-Stage MoO

This is the aligned core compute layer.

Rule:

```text
operands = confirmed core-loop iterations only
outputs = recorded speculative nodes, which are real graph nodes
speculative outputs are inspected, not operated on
promoted outputs may later act as operands
```

Current proper graph corpora:

```text
graph-first smoke corpus: out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite
confirmed operands: 1..80
nodes: 3,522
edges: 9,559

current expanded corpus: out/experiments/strict_stage_graph_u120_20260430.sqlite
confirmed operands: 1..120
nodes: 7,798
edges: 20,989
```

Main scripts/notes:

```text
moo_graph_corpus.py
strict_stage_moo.py
moo_graph_query.py
stage_indexed_moo_ledger.py
stage_indexed_convergence_study.py
GRAPH_CORPUS_NOTE.md
archive/transitional_strict_ledgers/STAGE_INDEXED_MOO_LEDGER_NOTE.md
research/strict_stage/CONVERGENCE_STRUCTURE_NOTE.md
```

The older `stage_indexed_moo_field_rough_20260430` run reached confirmed
operands `1..1679`, but it was a node-summary artifact. Its JSONL ledger has
been purged. Core MoO graph work should use the SQLite corpus because it
preserves edge occurrences.

This layer can say:

```text
34/21 exists as an Order 3 rational at U34
87/32 exists as an Order 3 rational at U87
convergence probes must be studied as chains, not isolated points
```

This layer cannot say:

```text
-4/3 is an active downstream construction center
```

because speculative nodes are not operated on in aligned MoO.

## Layer 2: Exploratory Closure

This is a hypothesis-generation layer, not the core MoO rule.

Historical rule:

```text
operands = all retained generated values
speculative nodes were reused as operands
```

This is where the older `n=5` / `n=6` motif and saturation studies live.
In those notes, `n` means closure round, not the core iteration count of `1`.
Because these scans operate on speculative nodes, they are hypothesis artifacts
rather than aligned MoO computation.

Main scripts/notes include:

```text
native_emergence_scan.py
moo_set_closure.py
moo_observatory.py
constant_probe.py
motif_graph_study.py
motif_persistence_study.py
motif_mass_study.py
archive/exploratory_closure/CONSTRUCTION_CENTERS_NOTE.md
archive/exploratory_closure/MOTIF_GRAPH_NOTE.md
archive/exploratory_closure/MOTIF_PERSISTENCE_NOTE.md
archive/exploratory_closure/SATURATION_LAYER_NOTE.md
```

This layer can say:

```text
-4/3 emerges as an exploratory closure hinge/center
probe-selected nodes appear downstream of closure motifs
```

This layer cannot be presented as:

```text
the strict MoO core
```

Its value is that it shows what speculative structure does if it is allowed to
echo and recombine. That may be philosophically interesting, but it is a
different rule.

## Purged Miscommunication: Integer Skeleton

The positive-integer skeleton work was a miscommunication. It was not a MoO
field run and should not remain as an active project layer.

The only insight worth retaining is negative:

```text
cheap integer summaries must not be substituted for the speculative rational
MoO field
```

The related scripts, reports, and note should be treated as discarded artifacts,
not as part of the active MoO research program.

## Layer 3: External Probes

External constants, geometry labels, and related mathematical concepts are
analysis probes, not runtime objects.

This includes:

```text
pi, e, ln2, sqrt2, phi
circle / square / triangle language
continued-fraction and Farey-style baselines
Ramanujan / Hardy-Littlewood / Cambridge analogy
```

Allowed claim:

```text
an external probe selects a speculative node or chain for inspection
```

Disallowed claim:

```text
MoO has constructed the completed non-rational constant or Euclidean object
```

For convergence work, an approximating point alone is not evidence. The object
of interest is:

```text
shared convergence structure inside the MoO ledger
```

## Layer 4: Projected Objects

Projected objects are analysis-layer anchors inferred from strict graph
families by explicit projection rules.

Rule:

```text
exact source family -> projection rule -> inferred inspection anchor
```

They can be used to ask:

```text
what held-out graph structure should this anchor organize or predict?
```

They cannot be used as:

```text
runtime nodes
operands
confirmed facts
theorems
completed constants
proof that MoO defines Euclidean objects
```

Current vocabulary:

```text
Order-4 projected object
asymptotic inspection anchor
projected invariant
non-rational projected constant
deterministic construction bloom
constructional coordinate system over existing foundations
```

Avoid:

```text
Order-4 certainty
MoO constructs pi
MoO defines the Euclidean circle
MoO is chaotic
MoO replaces standard foundations
```

See `ORDER4_PROJECTION_PROTOCOL.md`.

## Vocabulary Cleanup

Use these terms consistently:

```text
U_n:
  the strict-stage universe after the core loop has confirmed 1..n

closure round n:
  a historical exploratory set-closure iteration that operated on speculative nodes

speculative node:
  any retained construction not confirmed as a positive whole-number iteration

probe-selected node:
  a speculative node selected after the fact by an external target or concept

Order-4 projected object:
  a non-operational analysis-layer anchor inferred from exact graph evidence by
  an explicit projection rule

center / hinge:
  allowed for exploratory closure results, but not automatically a strict-stage
  property
```

## Current Alignment Rule

When documenting or discussing a result, state its layer first:

```text
strict-stage MoO
exploratory closure
external probe / concept analysis
```

If the layer is not stated, the result should not be treated as established.
