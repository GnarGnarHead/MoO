# Graph Invariants Protocol

> Status: active protocol.
>
> This note defines the shared graph-native invariant vocabulary used by MoO
> research probes. It exists to keep circle, Order-4, dynamics, and archived-lead
> tests from inventing incompatible scoring language.

## Purpose

MoO claims are graph-first. A value is only an address. The evidence is how that
value appears inside a strict construction corpus.

This protocol standardizes the first invariant set every strict report should
try to expose:

```text
first_stage
confirmed_stage
confirmation_lag
incoming_derivation_events
distinct_witness_families
operation_signature
neighborhood_overlap
baseline_adjusted_rank
denominator / component-height baseline
```

These are not theorem claims. They are report fields that make different probes
comparable.

## Required Fields

### Arrival

```text
first_stage:
  first strict stage where the node is recorded in the corpus

confirmed_stage:
  core-loop stage where a positive whole-number node is confirmed, or null

confirmation_lag:
  confirmed_stage - first_stage, when confirmed_stage exists
```

Interpretation:

```text
construction can precede confirmation
confirmation_lag is corpus/generator-conditioned
absence of confirmation is not rejection of a rational node
```

### Incoming Derivation Events

```text
incoming_derivation_events:
  count of recorded incoming edge occurrences landing on the node
```

This is witness mass, not intrinsic importance. It must be read with operation
mix, stage, and baseline controls.

### Distinct Witness Families

A report should distinguish:

```text
unique_directed_algebraic:
  op plus ordered input values

unique_commutative_normalized_algebraic:
  same as above, but + and * input order is normalized

distinct_directed_input_pairs:
  ordered input-pair diversity, regardless of repeated equivalent events

distinct_commutative_normalized_input_pairs:
  input-pair diversity with + and * order normalized
```

This prevents raw edge multiplicity from being mistaken for independent
construction diversity.

### Operation Signature

```text
operation_signature:
  histogram of incoming operation labels plus the dominant operation
```

For strict-stage MoO this is evidence about how confirmed operands first reach
or repeatedly construct the node. It is not a symbolic identity of the value.

### Neighborhood Overlap

The default local neighborhood is:

```text
shared_input_neighborhood:
  other result nodes produced by edges that share at least one confirmed input
  node with the target's incoming edges
```

For a family of nodes, report pairwise overlap as:

```text
pairwise_shared_input_neighborhood_jaccard
```

This is a first reusable neighborhood metric. It can be refined later, but a
report using another metric must name it explicitly.

### Classical Baselines

Every rational node should expose at least:

```text
denominator_height:
  q for normalized p/q

component_height:
  max(abs(p), q)
```

Reports may add continued-fraction, Stern-Brocot, Farey, construction-cost, or
operation-exposure controls, but denominator and component height are the
minimum baselines.

### Baseline-Adjusted Rank

The initial baseline-adjusted rank asks:

```text
within the peer group matched by denominator or component height,
where does this node sit for a named graph metric?
```

Allowed first metrics:

```text
incoming_derivation_events
distinct_witness_families
confirmation_lag
first_stage
```

Allowed first controls:

```text
denominator
component_height
```

Safe interpretation:

```text
This node is high/low under this metric relative to this named peer group in
this corpus.
```

Unsafe interpretation:

```text
This node is intrinsically important.
```

## Family Summaries

For probes involving a tuple or family, such as:

```text
t, x, y in a unit quadratic shell
x, y, r in x*x + y*y = r*r
successive ratios in a projected phi chain
```

the report should include:

```text
present_member_count
missing_member_count
max_first_stage
max_confirmation_lag
total_incoming_derivation_events
aggregate_operation_signature
baseline_envelope
neighborhood_overlap
```

This makes the claim about the family, not just the most attractive member.

## Current Implementation

The shared helper lives in:

```text
moo_graph_invariants.py
```

Current consumers:

```text
moo_research_report.py
moo_circle_probe.py
moo_circle_square_probe.py
```

Report payloads using this protocol should include:

```text
vocabulary_version: graph_invariants.v1
```

## Claim Upgrade Path

A graph-invariant report can upgrade a lead only when it supports a stricter
claim than value presence alone.

Example:

```text
weak:
  7/25 and 24/25 are present in the strict corpus.

stronger:
  The unit-shell family t=3/4 -> (7/25, 24/25) is complete in this corpus and
  has named graph-invariant fields: arrival, witness diversity, operation
  signature, baseline envelope, and neighborhood overlap.

not yet allowed:
  MoO defines the circle.
```

## Guardrails

Do not:

```text
compare reports that use different corpus bounds without naming the bounds
turn high derivation mass into an importance claim without controls
call first_stage an intrinsic construction cost
call neighborhood overlap an attractor
claim projected constants from approximation alone
```

Do:

```text
name the corpus and bounds
include the claim boundary
state the invariant metric
state the baseline/control
save the report if it will support future interpretation
pair saved machine reports with analysis notes
```
