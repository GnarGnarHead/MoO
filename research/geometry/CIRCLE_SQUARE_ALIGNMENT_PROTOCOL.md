# Circle-Square Alignment Protocol

> Status: active geometry research protocol.
>
> This note defines a MoO-internal circle-square branch-intersection problem. It
> does not claim classical squaring of the circle, Euclidean circle definition,
> or construction of `pi`.

## Core Distinction

Classical squaring the circle asks:

```text
Given an arbitrary Euclidean circle, construct an exactly equal-area square by
classical compass-and-straightedge rules.
```

MoO's geometry-adjacent question is different:

```text
Inside one strict construction graph, where do rational shell structures and
square/self-product structures overlap in timing, witnesses, operation
signatures, neighborhoods, or predictive organization?
```

Safe short name:

```text
circle-square alignment
```

Avoid as a primary claim:

```text
squaring the circle
```

MoO-native correction:

```text
A value appearing is not enough.
The same value can appear by different witnesses, and the witness matters.
```

For this protocol, the central distinction is:

```text
square witnessed through spine:
  the square value appears by positive-integer confirmation

square witnessed through branch:
  the square value appears by the inspected self-product relation v * v
```

Only the second reading supports branch-square emergence.

## Branch Definitions

### Circle-Like Branch

Current first object:

```text
rational quadratic shell:
  x*x + y*y = r*r
```

This is not yet a Euclidean circle. It is an exact rational constraint family
inside a strict MoO graph corpus.

### Square-Like Branch

Current first objects:

```text
square components:
  x*x
  y*y
  r*r

self-product witness:
  a strict graph edge v * v -> v*v
```

Important strict-stage rule:

```text
rational square nodes may be present without self-product witnesses
```

In strict-stage MoO, speculative rational nodes are not operands. Therefore a
literal `v * v` witness is expected only when `v` is an allowed confirmed
positive integer operand at the edge stage.

## Alignment Candidate

A circle-square alignment candidate is:

```text
a nondegenerate rational shell x*x + y*y = r*r
whose shell components and square components are present in the same strict
graph corpus with named graph-invariant support
```

Candidate fields:

```text
x, y, r
x_square, y_square, r_square
component presence
square component presence
self-product witness status
common-denominator integerized triple
primitive integer triple
Euclid m,n parameter recovery when available
prime-factor profile after rational normalization
stage_spread
phase_delta
graph_invariant_summary
neighborhood overlap
baseline envelope
```

Prime and Euclid-parameter fields are governed by
`PRIME_EUCLID_SHELL_ALIGNMENT_PROTOCOL.md`. They are scrutiny fields, not proof
that primes explain MoO geometry.

## Phase Language

Use stage language instead of unqualified chaos language:

```text
stage_spread:
  max(first_stage over shell and square components)
  -
  min(first_stage over shell and square components)

shell_stage_spread:
  max(first_stage of x, y, r) - min(first_stage of x, y, r)

square_stage_spread:
  max(first_stage of x*x, y*y, r*r) - min(first_stage of x*x, y*y, r*r)

phase_delta:
  max(first_stage of square components)
  -
  max(first_stage of shell components)
```

Safe interpretation:

```text
low stage_spread:
  the shell and square components become graph-visible in a narrow strict-stage
  window

positive phase_delta:
  square components lag the shell components

negative phase_delta:
  square components are already visible before the full shell is visible
```

Do not call this a bifurcation, attractor, Lyapunov effect, or strange
attractor without a separate dynamics protocol.

## Metrics

Primary first-pass metrics:

```text
complete_family:
  x, y, r, x*x, y*y, and r*r are all present

self_product_witness_count:
  number of square components with literal strict `v * v` witnesses

stage_spread:
  bounded phase-alignment score

total_incoming_derivation_events:
  family-level witness mass from graph invariants

baseline_envelope:
  denominator/component-height envelope for the family
```

Secondary metrics:

```text
operation signature agreement
pairwise shared-input-neighborhood overlap
denominator/component-height matched ranking
held-out stage persistence
```

## Controls

Minimum controls:

```text
denominator height
component height
degenerate versus nondegenerate shells
self-product witness eligibility under strict operand rules
stage/bound settings of the source corpus
```

Future controls:

```text
matched nonshell triples
operation-label shuffles
held-out strict corpora
stage-window holdouts
common-denominator matched shells
primitive-radius matched shells
Euclid-parameter-size matched shells
```

## Allowed Claims

Allowed after a successful strict report:

```text
This corpus contains circle-square alignment candidates: rational quadratic
shell structures whose associated square components are present in the same
strict graph corpus with bounded stage spread and graph-native witness support.
```

Allowed for weak findings:

```text
This report identifies shell-square branch-overlap leads that need stronger
controls before geometric interpretation.
```

## Disallowed Claims

Do not claim:

```text
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
Every circle can be squared in MoO.
Classical impossibility results are refuted.
```

## First Experiment

Initial target:

```text
nondegenerate strict rational shells
small denominator/component-height envelope
explicit x*x, y*y, r*r presence
self-product witness audit
low stage-spread ranking
```

The expected low-hanging examples include classical Pythagorean structure such
as `3, 4, 5`. The MoO question is not whether those identities exist, but how
their shell and square branches phase into the strict graph corpus.
