# Project Misalignment Audit

> Status: diagnostic note.
>
> This note documents how the repository is currently out of alignment with the
> resolved MoO framing, and why. It is not a purge list and not a command to
> delete material. It is a map of where the repo's language, tools, and research
> artifacts drift away from the current understanding.

## Resolved MoO Frame

The current MoO framing is:

```text
1 is the only certainty.

Past iterations of 1 are second-order count.

Speculative points are outputs of interactions between second-order counts.

Edges are the structure.

The graph is the primary object of inspection.

Speculative points are real MoO nodes, but they are not operands.
MoO does not speculate on speculations.
```

So the important object is not a bare value, not a target approximation, not an
edge count, and not a classical theorem projected onto the graph.

The important object is the actual relation:

```text
count interaction --operation--> speculative or confirmed landing point
```

and the larger structures made by those relations.

## Main Misalignment

The repository contains several layers that were produced before this framing
was clear. Those layers are not all worthless, but they are not equally aligned.

The main conflict is:

```text
resolved MoO:
  edges are the structure
  speculative points are not operands
  values are only coordinates inside the graph

older repo artifacts:
  compute closure sets of values
  reuse speculative values as operands
  rank values by counts, hubs, motifs, residuals, or target proximity
  describe value-level reports as if they were MoO-native structure
```

That means a lot of the repo is currently a mixture of:

```text
aligned MoO machinery
historical exploratory closure work
external analysis probes
assistant/user miscommunication artifacts
```

## 1. Ambiguous Meaning of `n`

Older notes and scripts often use `n` or `round` to mean a closure round:

```text
round 5 closure
n = 6 saturation
```

Resolved MoO uses the core iteration/count framing:

```text
U12 or stage 12 = the count has iterated through 1..12
```

These are not the same.

Why this matters:

```text
closure round:
  repeatedly applies operations to retained generated values
  can operate on speculative outputs

core iteration stage:
  only confirmed count values are operands
  speculative outputs are recorded but not operated on
```

Any note that says `n=5`, `round 5`, or `saturation at n=6` may be using an old
closure meaning rather than the resolved MoO count meaning.

## 2. Speculating on Speculations

The most important computational misalignment is the old closure model.

Older closure tools allowed generated speculative values to become operands in
later rounds. That is now out of alignment.

Resolved MoO:

```text
confirmed counts interact
-> speculative points are recorded
-> speculative points are inspected
-> speculative points are not operands
```

Old exploratory closure:

```text
generated values interact again
-> speculative-on-speculative expansion
-> large closure fields
-> saturation layers, hubs, motif mass, residual rankings
```

Why this matters:

The old closure artifacts may still contain suggestive patterns, but they cannot
be treated as direct MoO computation. They are historical exploratory artifacts.

## 3. Values Became Too Important

Many notes and scripts drift toward value-level interpretation:

```text
best approximant to pi
top residual value
high child-count value
value ranked by motif mass
probe-selected rational
```

Resolved MoO does not forbid looking at values, but values are not the structure.

A value is only meaningful through:

```text
the edge or edges that produce it
its position in the graph
its relation to count interactions
its speculative/confirmed status
the repeated structure of relations around it
```

Why this matters:

If a report says a value is interesting but does not preserve the edge structure
that makes it interesting, it is only a scouting artifact.

## 4. Edge Counts Replaced Edge Structure

Several studies summarize graph behavior by counts:

```text
child_count
derivation_events
motif mass
hub count
top-k values
residual score
```

Those summaries can be useful for navigation, but they are not the MoO object.

Resolved MoO cares about the actual relations:

```text
a + b -> c
a - b -> c
a * b -> c
a / b -> c
```

and about how those relations form larger structures.

Why this matters:

Counting edges can hide the thing MoO is trying to reveal. An edge count is a
map label; the edge itself is the terrain.

## 5. Imported Research Language Drifted Too Far

The repo contains research language from:

```text
Hardy-Littlewood / circle method
Ramanujan
continued fractions
transcendental attractors
geometry probes
prime harmonics
Fermat / Goldbach / twin primes
Godel numbering
```

Some of this may still be valuable. The misalignment is not that these topics
exist. The misalignment is when they are allowed to define MoO from the outside.

Resolved MoO order:

```text
1. build or inspect MoO edge structure
2. observe what speculative points and relation patterns emerge
3. only then apply external interpretations as probes
```

Misaligned order:

```text
1. choose an external target or famous theorem
2. search for nearby values
3. call the match MoO evidence
```

Why this matters:

External mathematics can provide lenses, but it cannot be allowed to replace the
internal structure.

## 6. "MoO-Native" Is Overused

Several older notes call closure-derived quantities "MoO-native":

```text
MoO-native observables
MoO-native binding profile
native emergence ledger
target-blind native corpus
```

This is misleading under the resolved framing if the source was an old closure
run that operated on speculative values.

Better distinctions:

```text
aligned MoO:
  strict-stage graph where only confirmed counts are operands

historical closure-native:
  patterns internal to the old closure artifact

external probe:
  outside interpretation applied after graph construction
```

Why this matters:

Something can be internally consistent within a historical closure report while
still not being aligned MoO.

## 7. Graph Storage Is Better Aligned Than Many Notes

The strict-stage graph corpus is currently the closest implementation to the
resolved MoO framing:

```text
confirmed count operands
recorded speculative output nodes
edge occurrences preserved
SQLite graph inspection
alignment checks for speculative operands
```

But many surrounding notes and older scripts still point back to JSON ledgers,
closure rounds, target probes, and value summaries.

Why this matters:

The project now has a more aligned storage path, but the research layer still
contains older interpretations that can pull the reader back into the wrong
model.

## 8. The Probe Layer Is Not Wrong, But It Is Unstable

The probe layer is valuable only when it stays in the correct order:

```text
MoO structure first
probe second
interpretation last
```

A probe is out of alignment when it:

```text
treats target proximity as evidence by itself
constructs target values outside the graph and reads them back as MoO structure
uses theorem language as if it were runtime semantics
reduces graph structure to a ranked list of values
```

A probe is more aligned when it:

```text
selects candidate nodes or edges for inspection
preserves the exact graph relations
states that the external label is only a handle
keeps speculative conclusions separate from runtime claims
```

## Why This Happened

The misalignment has a few causes.

First, the project developed through exploration. The early closure tools were
useful for generating patterns quickly, but they were based on a different
implicit rule: generated values could be reused as operands.

Second, the conversation repeatedly slid into ordinary mathematical language:

```text
numbers
values
approximants
hubs
centers
branches
proofs
targets
```

Those words are convenient, but they can hide the MoO ontology.

Third, outside research analogies were introduced too early. Hardy-Littlewood,
Ramanujan, geometry, primes, and transcendental language can be useful, but only
after the MoO structure is already being read correctly.

Fourth, implementation convenience encouraged summaries:

```text
counts
rankings
top-k lists
JSON ledgers
score tables
```

Those are easy to compute, but they are not the structure itself.

Fifth, there was a persistent language mismatch. The resolved MoO language is:

```text
certainty
second-order count
speculative points
edges as structure
no speculation on speculation
```

Much of the repo was written before that language was stable.

## What Is Still Worth Preserving

The misaligned material should not be treated as automatically worthless.

It can still be valuable if it records:

```text
an actual emergence that should be rechecked in the strict-stage graph
a useful analogy kept clearly outside runtime semantics
a failed framing that clarifies what MoO is not
a candidate relation pattern worth inspecting by edges
```

But it should not be read as settled MoO evidence unless it survives the
resolved framing.

## How To Read The Repo Right Now

Use this hierarchy:

```text
primary:
  strict-stage graph corpus
  actual edge records
  confirmed count operands
  speculative output nodes

secondary:
  graph queries and summaries that point back to exact edges

historical:
  closure ledgers
  motif mass / residual / saturation studies
  target-probe reports from speculative-on-speculative runs

speculative lenses:
  geometry
  primes
  transcendentals
  Hardy-Littlewood / Ramanujan / Godel analogies
```

Historical and speculative material can inform questions, but the answer has to
come back to the graph.

## Cleanup Principle

Do not purge by topic.

Purge or rewrite by alignment:

```text
keep:
  material that preserves or clarifies edge structure
  material that states its speculative or historical status clearly
  material that helps ask better MoO questions

rewrite:
  material that has a useful idea but wrong language
  material that says "MoO-native" when it means historical closure-native
  material that treats values as interesting without their edges

archive or remove:
  material that only ranks values
  material that imports external targets as if they were MoO objects
  material that depends on operating on speculative nodes without saying so
```

## Current Diagnosis

The project is not out of alignment because it contains speculative probes.

The project is out of alignment because the speculative probes, historical
closure artifacts, and aligned graph-first MoO implementation are interleaved
without enough separation.

The core idea is still coherent:

```text
1 -> count -> speculative points -> edge structure
```

The repo needs to make that hierarchy obvious everywhere.
