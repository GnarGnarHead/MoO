# Geometric Probes as Analysis-Layer Subsets

> Status: speculative research note.
>
> This note records a boundary for future MoO geometry work: geometric probes are
> analysis-layer subsets of the emergent arithmetic pattern. They are not runtime
> semantics, not primitive shape objects, and not claims that MoO currently
> contains geometry as a built-in domain.

## Core Framing

MoO should treat geometry as an interpretive probe over already-emergent
construction structure.

The runtime produces rational values, derivation events, first witnesses,
operation motifs, grounding status, and construction centers. A geometric probe
selects a speculative subset of that emergent pattern and asks whether it
behaves like a known geometric constraint family.

In short:

```text
runtime emergence
-> analysis-layer constraint filter
-> MoO subset or repeated structure
-> shape-like shadow
-> possible concept label
```

This is deliberately weaker than saying that the graph directly contains
circles, squares, dimensions, or geometric space.

## Why This Matters

The current MoO evidence is strongest when it stays target-blind first:

- construct the bounded rational field from `1`,
- record first-seen order and first witnesses,
- identify motifs and construction centers,
- then apply outside interpretations.

Geometry probes should follow the same discipline. A square, circle, area
relation, diagonal relation, or polygon-limit relation should be treated as a
shadow cast by a subset or repeated structure of the arithmetic construction
field.

That keeps the research question measurable:

```text
Do certain emergent branches, centers, or transition profiles repeatedly align
with independently defined geometric constraint signatures?
```

It also avoids a common failure mode:

```text
interesting geometric language
-> unrestricted projection
-> everything appears related to everything else
```

The value of the probe depends on explicit constraints.

## Constraint Signatures

A geometric probe should define a constraint signature before inspecting the
target subset.

Possible square signatures:

- self-product structure, `n * n`;
- additive square growth by odd increments, `1, 3, 5, 7, ...`;
- area/grid interpretation;
- fourfold or `C4` constraint;
- diagonal shadow through `sqrt2`;
- tiling or axis-product behavior.

Possible circle signatures:

- unit/radius invariant;
- circumference and area shadows through `pi` or `tau`;
- polygon-refinement behavior;
- rotation/curvature interpretation;
- one-to-infinity boundary behavior;
- inscribed/circumscribed polygon constraints.

Possible bridge signatures:

- equal-area circle-to-square shadow, `sqrt(pi)`;
- equal-perimeter circle-to-square shadow, `pi/2`;
- unit-square circumcircle shadow, `sqrt2/2`;
- unit-square incircle shadow, `1/2`;
- square-to-circle equal-area radius, `1/sqrt(pi)`;
- polygon refinement as a finite-to-limit bridge.

These are not new MoO objects. They are proposed analysis filters.

## Constrained Projection Overlap

A useful working term is:

```text
constrained projection overlap
```

Definition:

```text
A constrained projection overlap occurs when two distinct concept families,
after explicit constraint filters are applied, share construction ancestry,
motif centers, first-witness structures, or stable asymptotic shadows.
```

This is the map-making version of the circle/square question.

It does not say:

```text
circle = square
```

It asks:

```text
Do circle-like and square-like constraint signatures overlap in MoO's
construction space?
```

That framing is compatible with the classical impossibility of squaring the
circle by compass and straightedge. MoO is not claiming a direct construction of
one object from the other. It is asking whether their constrained projections
share a construction address in a richer arithmetic map.

## Branch And Shadow

A branch is the repeated witnessed relation. A projected shape is the shadow
cast by that branch or by a branch interaction.

For squares:

```text
self-relation / square branch:
  n -> n*n

square-like projected form:
  the geometric shadow of self-relation
```

For circles:

```text
shell-relation interaction:
  x and y enter square relation
  x*x and y*y enter addition
  that result agrees with r*r

circle-like shadow:
  only if that interaction repeats, stabilizes, and organizes further emergence
```

## Concept Branches

A concept branch is a candidate region of the MoO construction field that can
earn a mathematical label only after multiple independent witnesses agree.

Candidate branch labels:

- perfect-square branch;
- diagonal branch;
- area-preservation branch;
- circle-shadow branch;
- polygon-limit branch;
- recurrence/convergence branch.

A branch label should not be assigned merely because a value appears. For
example, a square branch should not be identified only because the value `4`
exists. It should require several witnesses, such as:

- repeated self-product construction;
- odd-increment growth;
- stable motif family across bounds;
- relevant parent ancestry;
- bridge shadows to diagonals or area relations;
- controls showing the same label does not attach everywhere.

The label is earned by structure, not by association.

## Low-Hanging Study

The first geometric study should probably start with squares rather than
circles.

Reason:

- square signatures are strongly arithmetic;
- multiplication already belongs to the runtime closure;
- self-product and odd-increment witnesses are easy to define;
- the diagonal shadow gives a clean bridge to `sqrt2`;
- area-preserving projections give later bridges to circle probes.

Important caveat: the current default bounded corpus has
`max_abs_value = 4`, so raw integer square values beyond `4` are outside the
retained value field. A square study under the current corpus should therefore
focus on local signatures, normalized projections, or small square witnesses
first. Studying larger square numbers as values will require changed bounds.

## Guardrails

Geometry probes should remain analysis-layer unless the runtime is deliberately
extended later.

For now, do not:

- add circle or square primitives to `constructionist_math.py`;
- treat geometric objects as graph node types;
- interpret a numerical approximation as a geometric discovery by itself;
- treat visual or metaphorical overlap as evidence without a constraint filter;
- claim that MoO solves classical squaring of the circle.

Do:

- define the constraint signature first;
- run the probe over a saved corpus when possible;
- compare against decoy concept families;
- record first witnesses and motif ancestry;
- test stability under changed bounds;
- keep the interpretation separate from runtime semantics.

## Working Hypothesis

Geometric concepts may become visible in MoO as speculative subsets of the
emergent arithmetic pattern.

If the structure is real, circle-like and square-like probes should not merely
find isolated approximants. They should identify stable branches, centers,
transition profiles, or projection overlaps that persist under constraint.
