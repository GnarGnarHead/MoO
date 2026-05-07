# Stage Dynamics Lens

> Status: research protocol note.
>
> Chaos systems are useful to MoO as motivation for studying deterministic
> iteration, persistence, threshold shifts, recurrence, and divergence. This note
> does not claim that MoO is chaotic.

## Working Language

Use stage-dynamics language in active reports. Keep chaos vocabulary as outside
motivation until strict graph evidence earns stronger terms.

```text
chaos                       -> deterministic stage dynamics
chaotic emergence           -> path-sensitive combinatorial emergence
attractor                   -> persistent accumulation site
bifurcation                 -> parameter-threshold shift
sensitivity                 -> robustness under bound/policy sweeps
phase space                 -> feature projection space
Lyapunov divergence         -> neighborhood divergence rate
strange attractor           -> unclassified persistent structure
symbolic dynamics           -> operation-word recurrence
```

Formal reports should prefer `deterministic construction bloom` or
`path-sensitive combinatorial emergence` until MoO has a state space, evolution
map, metric, trajectory definition, and sensitivity criteria.

## Core Question

The first question is not:

```text
Is MoO chaotic?
```

The first question is:

```text
Does strict-stage MoO show reproducible deterministic stage dynamics:
growth, persistence, accumulation, threshold shifts, recurrence, or divergence?
```

## Stage State

For a strict graph corpus, define `G_U` as the graph snapshot through stage `U`.

A stage state can be summarized by:

```text
stage U
total nodes
new nodes
total edges
new edges
operation distribution
denominator bands
confirmed/speculative counts
confirmation transitions
top construction-gathering nodes
edge-local symbolic motif distribution
```

This is a feature projection over the graph, not a replacement for graph
inspection.

## Persistent Accumulation Sites

A persistent accumulation site is a node, motif, corridor, class, or return
pattern that repeatedly gathers construction evidence across stage growth.

For v1, use a narrow node definition:

```text
persistent accumulation candidate:
  appears in top-k construction-gathering rankings at >= 70% of sampled
  checkpoints in both cumulative and per-window rankings
  is normalized for node age / exposure where the metric permits it
  has more than one witness family
  is reported as a candidate, not a result
```

Raw edge count is not sufficient. A candidate must eventually survive controls:

```text
denominator-matched peers
first-stage-matched peers
operation-mix controls
bound-sensitivity checks
held-out strict corpora
```

## Parameter-Threshold Shifts

A parameter-threshold shift is a reproducible change in graph behavior under a
one-parameter sweep.

Candidate parameters:

```text
max_stage
max_abs_value
max_abs_p
max_abs_q
operation set
strict confirmed-only operand policy
```

Changing into speculative-operand closure is a mode change, not a strict-stage
parameter sweep. It must be labeled exploratory.

Allowed early language:

```text
parameter-threshold shift candidate
```

Disallowed early language:

```text
bifurcation
```

A shift candidate needs a before/after metric, such as:

```text
new accumulation site appears
old accumulation site drops below threshold
confirmation rate changes sharply
denominator distribution changes sharply
operation ecology changes sharply
return corridors emerge or disappear
```

Boundary effects must be treated as a first explanation, not an afterthought.

## Operation-Word Recurrence

MoO does not yet have full ancestry paths in the strict graph corpus. Do not
pretend node histories are linear trajectories.

Start with edge-local symbols:

```text
op
left kind / right kind
result kind
sign class
denominator bucket
value bucket
q-growth bucket
confirmation status
```

Example:

```text
/: positive_integer,positive_integer -> rational | q:low->mid | speculative
```

Stage is the time axis. Inside a stage, use canonical sorting or multisets, not
SQLite insertion order.

Allowed early claim:

```text
MoO has recurrent symbolic edge motifs under strict-stage construction.
```

Disallowed early claim:

```text
MoO has chaotic symbolic trajectories.
```

## Neighborhood Divergence

Numerical closeness is not construction closeness.

A future divergence test should compare graph neighborhoods at checkpoints:

```text
outgoing neighborhood size for A and B
shared result count
shared operation count
Jaccard similarity
divergence score
```

Do not call this a Lyapunov exponent unless a metric, nearby-state definition,
and growth law are explicitly defined.

## Research Workflow

Every stage-dynamics experiment should follow:

```text
question -> preregistered test -> saved report -> interpretation note -> follow-up decision
```

The protocol lives in:

```text
DYNAMICS_TEST_PROTOCOL.md
```

Saved reports live under:

```text
out/experiments/dynamics/
```

The output of a probe is not the research result by itself. A report becomes
usable only when paired with an interpretation note that records controls,
failures, caveats, and next questions.

## First Test

The first frozen test should be:

```text
Stage persistence of construction-gathering nodes across U-checkpoints.
```

Suggested checkpoints for the smoke corpus:

```text
U10, U20, U40, U60, U80
```

Initial metrics:

```text
incoming edge count
distinct witness pairs
operation diversity
```

Candidate threshold:

```text
appears in top 25 at >= 70% of checkpoints
and has >= 2 distinct witness families
```

Decision rule:

```text
if no candidates survive controls, downgrade accumulation-site language
if candidates survive, promote only to persistent accumulation candidate
```
