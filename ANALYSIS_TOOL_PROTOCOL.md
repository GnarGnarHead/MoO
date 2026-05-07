# Analysis Tool Protocol

> Status: alignment note for probes, scouts, lenses, and speculative studies.
>
> This note defines how analysis tools may interact with MoO without replacing
> MoO. The graph is primary. Edges are the structure. Analysis tools are ways of
> choosing where and how to inspect that structure.

## Core Rule

An analysis tool is aligned only if it returns to the graph.

```text
strict-stage MoO graph
-> edge-derived analysis signal
-> candidate structure or region
-> exact nodes and edges
-> graph-context inspection
```

The candidate structure is not the conclusion. It is a reason to inspect.

## Required Boundaries

Every analysis tool must state:

```text
what graph corpus it reads

which edge records it uses

what projection or filter it applies

what nodes or neighborhoods it returns for inspection

what it refuses to conclude by itself
```

If a tool cannot identify the exact graph context behind its output, it is not
yet useful MoO evidence.

## What Tools May Do

Aligned analysis tools may:

```text
filter graph neighborhoods

project edge records into temporary signals

rank places for manual inspection

compare confirmation status across stages

look for structural signatures

use external concepts as labels after graph structure has been inspected
```

They may use counts, scores, spectra, constants, geometry labels, prime labels,
or convergence language only as scouting or interpretation aids.

## What Tools Must Not Do

Analysis tools must not:

```text
operate on speculative nodes

replace edge inspection with value lists

turn external labels into runtime semantics

use target constants as the first definition of importance

claim that a score, spectrum, or metric is MoO structure by itself

discard self-reference to `1`

hide the edges behind a summary
```

Speculative nodes are MoO nodes, but they are inspected rather than used as
operands until core-loop promotion.

## Evidence Ladder

Use this ladder when interpreting tool output:

```text
weak:
  value match
  decimal proximity
  high count
  visual pattern
  external label

stronger:
  exact construction edges
  coherent local neighborhood
  clear confirmation status
  repeated graph-context behavior across stages
  traceable relation to `1`
  survival under changed inspection projection
```

A weak signal may still be useful. It just remains a scout until the graph
context gives it meaning.

## Standard Output Shape

New analysis tools should prefer outputs shaped like:

```text
tool_name
graph_corpus
projection_or_filter
candidate_id
why_flagged
nodes
edges
neighborhood_query
confirmation_status
interpretation_limits
```

The most important fields are:

```text
nodes
edges
neighborhood_query
interpretation_limits
```

Those fields keep the tool accountable to MoO.

## Existing Tool Categories

### Geometry Probes

Geometry probes are speculative subsets of emergent construction patterns.
Circle, square, triangle, and area language are analysis-layer labels unless
the graph context earns them.

### Prime And Fermat Probes

Prime, Fermat, Goldbach, Sophie Germain, twin-prime, and related probes should
ask how those concepts interact with nearby graph structure. They should not
reduce MoO to a property test for known number theory.

### Convergence Probes

Convergence probes may use external constants only after MoO structure is
recorded. A value near `pi`, `e`, or another constant is not important by
itself. It matters only if there is a shared construction context, edge
structure, or persistent graph behavior.

### Spectral Scouts

Spectral scouts project edge-derived signals to find complex signatures. The
spectrum only says where to look. Meaning comes from inspecting the returned
graph neighborhood.

### Historical Closure Studies

Historical exploratory closure studies may still contain useful ideas, but they
often reused speculative nodes as operands. They must be read as hypothesis
artifacts, not aligned strict-stage MoO computation.

## Short Version

```text
The graph is the experiment.
Edges are the structure.
Analysis tools are scouts.
External concepts are labels, not foundations.
Every interesting result must return to exact MoO context.
```
