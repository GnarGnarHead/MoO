# Core Claims

> Status: canonical claim boundary.
>
> This document consolidates what MoO can currently claim without replacing the
> detailed notes. If another document appears to make a stronger claim, read it
> through this boundary and through `PROJECT_ALIGNMENT_NOTE.md`.

## Reading Rule

Every MoO claim should state:

```text
evidence_layer: strict | exploratory | external_probe
claim_status: observation | lead | candidate | strict_result | rejected
```

The graph is the primary evidence. A value, approximation, constant label,
shape label, or high score is not a MoO result unless it is read through:

```text
node
construction edges
repeated witnesses
input neighborhood
operation signature
stage / confirmation status
corpus bounds
```

A shorter MoO-native rule:

```text
A value appearing is not enough.
The same value can appear by different witnesses, and the witness matters.
The value is not the object; the witnessed emergence is the object.
```

Projected-object claims also need:

```text
source_family
projection_rule
primary_metric
controls
holdout
kill_rule
```

## Core Theory Claims

### Primitive Certainty

MoO begins with one primitive certainty event:

```text
1
```

The philosophical seed is:

```text
I think, therefore 1.
```

The implementation claim is narrower and operational:

```text
Ref(1) is the only primitive runtime anchor.
Everything else is generated from iterations and relations of 1.
```

### Failed Proof Of 2

MoO began as an attempt to prove `2` from `1`. That attempt fails as certainty:
to reach `2`, the system must preserve a prior instance of `1`, and that prior
instance is already once removed from immediate certainty.

Therefore:

```text
2 is not a second certainty.
2 is the first confirmed move beyond immediate certainty.
```

The phrase "infinite distance from 1" is a philosophical reading of that
certainty gap, not a metric implemented by the runtime.

### Stage-Indexed Universe

MoO is stage-indexed. At strict stage `U_n`, the confirmed positive
whole-number iterations are:

```text
1..n
```

A construction can produce a future positive integer before the core loop
confirms it. Example:

```text
At U3, 2 and 3 are confirmed.
2 * 3 can construct 6.
6 remains speculative until U6.
```

This is the central stage rule:

```text
construction can precede confirmation;
confirmation comes from the core 1 loop reaching the value.
```

### Epistemic Orders

Current graph-internal order language:

```text
Order 1:
  1, the only immediate certainty

Order 2:
  confirmed positive whole-number iterations of 1

Order 3:
  unconfirmed or relational constructions from iterations of 1
```

Fractions, zero, negative values, and unconfirmed future whole numbers are real
MoO nodes once constructed, but they are not Order 1 or Order 2.

### Order-4 Projected Objects

Order 4 is not a new certainty tier.

It is an analysis-layer abstraction over graph evidence:

```text
Order 4:
  projected forms: subsets or repeated structures of MoO whose shadows can be
  read as higher forms
```

An Order-4 projected form is:

```text
a non-operational analysis-layer shadow inferred from a named family of exact
MoO graph evidence by an explicit projection rule
```

It is not:

```text
a runtime node
an operand
a confirmed fact
a theorem
a completed object inside strict MoO
more certain than Order 3
```

Order 4 is more abstract than Order 3, not more certain.

Governing rule:

```text
Order-4 forms are projected shadows, not certainties or operands; they gain
credibility only when they predict or organize held-out strict graph structure
better than controls.
```

The strongest evidence is not approximation accuracy. It is predictive
organization.

See `ORDER4_PROJECTION_PROTOCOL.md` before making Order-4 claims.

### Strict Operand Rule

Strict-stage MoO operates only on confirmed core-loop positive integers:

```text
operands = confirmed core-loop iterations only
outputs = recorded graph nodes
speculative outputs = inspected, not operated on
promotion = later core-loop confirmation
```

Short form:

```text
MoO speculates from promoted certainty.
MoO does not speculate on speculations.
```

### Graph-First Identity

MoO separates value identity from construction identity.

```text
value identity:
  one node per reduced rational value p/q

construction identity:
  many edge occurrences may land on the same value node

graph evidence:
  the node plus its incoming/outgoing construction context
```

The same rational value can be ordinary under one projection and structurally
interesting under another. MoO does not decide that from the value alone.

In MoO language:

```text
value presence:
  the value appears

witnessed emergence:
  the value appears by a named construction path

branch emergence:
  the witness belongs to the relation or branch being studied
```

Value presence is the weakest reading. Witnessed emergence is the object of
study.

### Branch Lineage

A branch is not a formula family, value list, single edge, or ordinary graph
path.

```text
A MoO branch is a repeated witnessed relation that emerges along the recurrence
of 1.
```

Examples:

```text
even branch:
  n -> n+n

square branch:
  n -> n*n

product branch:
  nontrivial multiplicative landings a*b -> n

prime branch:
  counting-spine values sharing the repeated irreducibility relation:
  no nontrivial product-branch landing exists

shell-relation branch:
  repeated witnessed cases where x, y, and r enter self-relation,
  x*x and y*y enter addition, and that result agrees with r*r
```

The same value may participate in multiple branch readings. A square value can
be witnessed through the counting spine while the square-branch witness is
permitted but not retained in the current field of observation.

## Current Strong Claims

MoO can currently claim:

```text
MoO is a graph-first construction framework from the primitive certainty 1.

Strict-stage MoO records rational and integer-valued constructions without
letting speculative nodes become operands.

Speculative nodes are real MoO nodes with weaker epistemic status, not errors
or discarded values.

Positive whole-number confirmation is stage-indexed by the core loop.

Graph provenance, witness multiplicity, neighborhoods, and confirmation status
are primary evidence.

External concepts are scrutiny lenses, not runtime foundations.

MoO may propose projected forms from stable graph families, but those shadows
are not certainties or operands.
```

## Corpus-Conditioned Observations

Strict graph corpora may support observations such as:

```text
this node is present in this corpus
this node first appears at this stage
this node was first speculative and later confirmed
this node has these incoming construction witnesses
this node has this operation histogram
this node shares input neighborhoods with these other nodes
this corpus passes strict alignment checks
```

These are corpus-conditioned. They depend on:

```text
max_stage
max_abs_p
max_abs_q
max_abs_value
retention policy
operand policy
tool version
```

They should not be quoted as intrinsic mathematical facts without naming the
corpus and controls.

## Candidate Claims

The following are live research candidates, not established theory:

```text
persistent accumulation candidates:
  possible construction-gathering nodes or regions that persist across stages
  and controls

unit-quadratic-shell candidates:
  exact rational square/addition agreements present in strict graph corpora

Euler reciprocal-mass candidates:
  exact finite reciprocal-square term and partial-sum structures when their
  nodes and construction edges are present

Order-4 projected forms:
  non-operational projected constants, shape-like shadows, or asymptotic
  shadows inferred from exact graph evidence by explicit projection rules

non-rational projected constants:
  pi and e as transcendental anchors; sqrt(2) and phi as algebraic irrational
  anchors; all remain projected forms rather than completed runtime objects

operation-word recurrence:
  repeated symbolic edge patterns under strict-stage construction

neighborhood divergence:
  differences between numerical closeness and construction-neighborhood
  closeness under a named metric
```

These candidates require preregistered metrics, controls, held-out data, saved
reports, and interpretation notes before gaining credibility.

## Not Yet Earned

MoO cannot currently claim:

```text
MoO defines the Euclidean circle.
MoO constructs pi, e, sqrt(2), phi, or any completed non-rational constant.
MoO is chaotic.
MoO has attractors, bifurcations, Lyapunov exponents, or strange attractors.
MoO proves new number theory.
MoO replaces standard foundations.
MoO invalidates ordinary arithmetic.
```

These phrases may appear in older or speculative notes as research language.
They are not current strict-stage claims unless a newer note explicitly
promotes them through the claim discipline above.

## Layer Boundaries

### Strict-Stage MoO

Aligned computation:

```text
confirmed operands only
speculative outputs recorded
graph-first SQLite corpus preferred
```

This is the layer used for current core evidence.

### Exploratory Closure

Historical hypothesis-generation:

```text
generated speculative values could be reused as operands
```

These notes are preserved because they contain leads, motifs, and intuition.
They are not strict-stage MoO computation.

### External Probes

Analysis lenses:

```text
constants
geometry labels
prime labels
Fourier / spectral / chaos language
classical rational baselines
```

External probes may select regions for inspection. They do not define MoO
objects by themselves.

### Order-4 Projection

Analysis-layer projection:

```text
exact graph family -> explicit projection rule -> inferred shadow/form
```

Projected forms may guide further inspection. They do not become strict-stage
operands, certainties, or theorems.

## Verification Trail

Read these in order when checking a claim:

```text
README.md
MOO_REALIGNMENT_NOTE.md
CORE_CLAIMS.md
PROJECT_ALIGNMENT_NOTE.md
EPISTEMIC_ORDER_NOTE.md
VISION.md
GRAPH_CORPUS_NOTE.md
GRAPH_INVARIANTS_PROTOCOL.md
ORDER4_PROJECTION_PROTOCOL.md
RESEARCH_LENSES.md
ANALYSIS_TOOL_PROTOCOL.md
```

For stage-dynamics research, also read:

```text
research/dynamics/STAGE_DYNAMICS_LENS_NOTE.md
research/dynamics/DYNAMICS_TEST_PROTOCOL.md
out/experiments/dynamics/README.md
```

For speculative or historical leads, also read:

```text
archive/exploratory_closure/EXPLORATORY_LEADS.md
DOCS_INDEX.md
```
