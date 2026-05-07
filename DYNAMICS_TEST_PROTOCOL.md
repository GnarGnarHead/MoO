# Dynamics Test Protocol

> Status: preregistration and report protocol for stage-dynamics research.
>
> This protocol keeps MoO dynamics work cumulative. Do not treat terminal output
> as a research result. Every experiment should have a frozen preregistration
> file, saved machine report, interpretation note, and follow-up decision.

## Research Loop

Use this loop:

```text
question
-> frozen preregistered test
-> saved machine report
-> human-readable interpretation note
-> follow-up decision
```

Saved reports live under:

```text
out/experiments/dynamics/
```

Each experiment should produce at least:

```text
out/experiments/dynamics/<experiment_id>.pre.md
out/experiments/dynamics/<experiment_id>.json
out/experiments/dynamics/<experiment_id>.analysis.md
```

The preregistration file freezes the question before running the test. The JSON
report is the measured artifact. The analysis note is the research artifact.

## Experiment IDs

Use stable IDs:

```text
dynamics_stage_persistence_u80_v1
dynamics_value_sweep_u80_v1
dynamics_symbolic_recurrence_u80_v1
dynamics_neighborhood_divergence_u80_v1
```

Avoid names based on desired conclusions.

## Required Preregistration Fields

Before running a test, record:

```text
experiment_id:
question:
evidence_layer:
claim_status:
corpus_paths:
corpus_configs:
exact_commands:
checkpoints:
primary_metric:
secondary_metrics:
metric_definitions:
candidate_thresholds:
control_definitions:
multiple_comparison_policy:
validation_corpus_paths:
known_limitations:
promotion_rule:
kill_or_downgrade_rule:
allowed_claim_language:
disallowed_claim_language:
```

If a field cannot be filled, the test is exploratory and must not promote
claims.

Planned commands are allowed only in interface-design notes. A preregistered
experiment must name the actual command to be run.

## Required JSON Metadata

Every machine report should include:

```text
report_type
experiment_id
generated_at_utc
corpus path
corpus checksum
corpus config
schema version
exact command
tool/source checksum
checkpoints or stage range
metric definitions
claim boundary
```

If a tool cannot yet write this metadata directly, include it in the paired
Markdown note.

## Interpretation Note Template

Use this shape for `<experiment_id>.analysis.md`:

```text
# <Experiment ID>

## Question

## Corpus

## Frozen Test

## Metrics

## Controls

## Thresholds

## Result Summary

## Candidate Findings

## Failed / Negative Findings

## Caveats

## Decision

## Next Question
```

The `Failed / Negative Findings` section is required. Silence about failures is
not acceptable research logging.

## Operational Defaults

Unless a preregistration file overrides these defaults, use:

```text
witness family:
  one unique commutative-normalized tuple (op, left_key, right_key)

operation diversity:
  count of operation labels from +, -, *, / with nonzero incoming edges

denominator-matched peer group:
  nodes with the same denominator q; require at least 10 peers

first-stage-matched peer group:
  nodes with first_stage within +/- 1 checkpoint interval; require at least 10
  peers

survives controls:
  candidate remains in the top decile of the primary metric within both peer
  groups and does not sit within 5% of numerator, denominator, or value caps

multiple comparisons:
  one primary metric may promote a candidate; all other metrics are exploratory
  unless separately preregistered

validation:
  promotion beyond "candidate" requires a held-out strict corpus with different
  bounds or a later U-stage extension
```

## Test 1: Stage Persistence

Purpose:

```text
Test whether construction-gathering nodes persist across U-checkpoints.
```

Default corpus:

```text
out/experiments/strict_stage_graph_smoke.sqlite
```

Default checkpoints:

```text
10,20,40,60,80
```

Metrics:

```text
incoming edge count
per-window new incoming edge count
distinct directed witness pairs
distinct commutative-normalized witness pairs
operation diversity
checkpoint top-k rank, cumulative
checkpoint top-k rank, per-window
node-age-normalized rank
```

Candidate threshold:

```text
appears in top 25 at >= 70% of checkpoints in both cumulative and per-window
rankings
and has >= 2 distinct witness families
and survives denominator-matched and first-stage-matched peer controls
```

Controls:

```text
denominator-matched peer comparison
first-stage-matched peer comparison
low-denominator positive control check
```

Decision:

```text
if no candidates survive controls:
  downgrade persistent-accumulation-site language
if candidates survive:
  promote only to "persistent accumulation candidate"
```

Planned command shape:

```sh
python3 moo_dynamics_probe.py \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --stage-persistence \
  --experiment-id dynamics_stage_persistence_u80_v1 \
  --checkpoints 10,20,40,60,80 \
  --k 25 \
  --write out/experiments/dynamics/dynamics_stage_persistence_u80_v1.json \
  --pretty
```

Until `moo_dynamics_probe.py` exists, this command is an interface target, not a
completed result.

## Test 2: Value-Bound Sweep

Purpose:

```text
Test robustness under a one-parameter retention-bound sweep.
```

Sweep:

```text
max_abs_value = 2, 3, 4, 5
```

Hold fixed:

```text
max_stage
max_abs_p
max_abs_q
retain_confirmed_edges
strict confirmed-only operand policy
```

Metrics:

```text
node count
edge count
operation distribution
denominator bands
confirmation transitions
persistent accumulation candidates
```

Candidate threshold-shift rule:

```text
metric changes by >= 3 median absolute deviations from neighboring sweep values
across a grid with at least seven ordered cells
and the change is visible in a repeated or held-out adjacent corpus
```

Controls:

```text
flag nodes near numerator/denominator/value caps
compare against total growth
compare persistence candidates across all sweep cells
```

Allowed claim:

```text
parameter-threshold shift candidate
```

With only the four-cell `2,3,4,5` sweep, this test is exploratory and cannot
promote a threshold claim by itself.

Disallowed claim:

```text
bifurcation
```

## Test 3: Edge-Local Symbol Recurrence

Purpose:

```text
Test whether strict-stage construction has recurrent edge-local symbolic motifs.
```

Do not encode full ancestry paths yet.

Edge symbol fields:

```text
op
left kind / right kind
result kind
result sign class
result denominator bucket
result value bucket
q-growth bucket
confirmation status
```

Metrics:

```text
symbol frequency by stage
symbol frequency by stage window
Shannon entropy of symbol distributions
novel symbol rate
recurring motif rate
Jensen-Shannon divergence between adjacent windows
```

Controls:

```text
operation-label shuffle
Markov null preserving operation frequencies and adjacent transitions
exclude impossible arithmetic cases
exclude bound-excluded outputs
```

Allowed claim:

```text
MoO has recurrent symbolic edge motifs under strict-stage construction.
```

Disallowed claim:

```text
MoO has chaotic symbolic trajectories.
```

## Test 4: Neighborhood Divergence

Purpose:

```text
Test whether numerical closeness and construction-neighborhood closeness differ.
```

Candidate pairs:

```text
probe-selected pairs such as 34/21 vs 87/32
denominator-matched controls
first-stage-matched controls
nearby-rational controls
```

Metrics by checkpoint:

```text
outgoing neighborhood size for A
outgoing neighborhood size for B
shared result count
shared operation count
Jaccard similarity
divergence score = 1 - Jaccard similarity
```

Required validation:

```text
divergence(A, B) == divergence(B, A)
missing nodes fail clearly
neighborhood depth is capped
```

Allowed claim:

```text
these nodes diverge in strict construction neighborhoods under the chosen metric
```

Disallowed claim:

```text
Lyapunov exponent
```

## Failure Criteria

Downgrade a dynamics claim if:

```text
total corpus growth explains the observation
denominator/value-matched peers behave similarly
the signal disappears under small bound changes
raw edge count is the only supporting metric
the candidate sits near corpus caps
the metric was chosen after seeing the result
graph or operation-label shuffles preserve the signal
no held-out strict corpus reproduces it
```

## Claim Language

Allowed:

```text
deterministic stage dynamics
persistent accumulation candidate
parameter-threshold shift candidate
operation-word recurrence
neighborhood divergence under a named metric
```

Disallowed until earned:

```text
MoO is chaotic
MoO has attractors
MoO has bifurcations
MoO has Lyapunov exponents
MoO has strange attractors
```
