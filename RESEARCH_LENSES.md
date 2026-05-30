# Research Lenses

> Status: operational scrutiny layer for graph-first MoO research.
>
> A research lens is admissible only if it compiles down to a graph query, a
> measurable score, a null/control comparison, or an explicit speculative-only
> lead. Names from outside mathematics are labels for scrutiny, not authority.
> External researchers and traditions are peripheral framing lenses; they do
> not enter MoO's core grammar. See `research/FRAMING_LENSES_NOTE.md`.

## Claim Discipline

MoO claims must carry two independent labels:

```text
evidence_layer: strict | exploratory | external_probe
claim_status:  observation | lead | candidate | strict_result | rejected
```

Use `evidence_layer` to name where the evidence came from.

Use `claim_status` to name how strong the current claim is.

This prevents a useful exploratory observation from being discarded while also
preventing it from being promoted into strict-stage MoO by wording alone.

## Required Lens Fields

Every new lens should fill these fields before it becomes part of the active
research workflow:

```text
name:
evidence_layer:
claim_status:
provocative_hypothesis:
false_positive_guarded_against:
graph_native_observable:
query_or_report:
metric:
null_model_or_control:
promotion_criteria:
kill_criteria:
allowed_claim_language:
disallowed_claim_language:
```

If any field cannot be filled, the lens stays a note, not an active research
tool.

Order-4 projected-object proposals must also fill the certificate in
`ORDER4_PROJECTION_PROTOCOL.md` before they gain credibility.

Graph-native metric language should use `GRAPH_INVARIANTS_PROTOCOL.md` unless a
probe explicitly defines a stricter metric.

## Active Strict Lenses

### Rational Baseline Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  Some MoO nodes may appear early or receive many construction witnesses
  relative to classical rational-complexity baselines.
false_positive_guarded_against:
  Mistaking ordinary low-denominator or standard rational-tree visibility for
  MoO-native structure.
graph_native_observable:
  node first_stage, confirmation status, incoming edge occurrences, witness
  diversity, operation histogram, and shared-input neighborhood.
query_or_report:
  python3 moo_research_report.py --db <corpus.sqlite> --node 34/21 --pretty
  python3 moo_research_report.py --db <corpus.sqlite> --corpus-baselines --pretty
metric:
  denominator height, component height, continued-fraction length,
  Stern-Brocot depth, Farey neighbors, derivation events, normalized witnesses,
  peer-group percentile, residual from peer median.
null_model_or_control:
  denominator, component height, or Stern-Brocot-depth peer groups.
promotion_criteria:
  A node-level observation can become a candidate only after it survives a
  corpus-wide ranking with explicit corpus parameters and peer controls.
kill_criteria:
  The same scoring declares many denominator-matched ordinary rationals equally
  strong, or the lead disappears under nearby corpus bounds.
allowed_claim_language:
  "34/21 has these construction witnesses and these rational baseline features
  in this strict-stage corpus."
disallowed_claim_language:
  "34/21 is unusual" from a single-node dossier.
```

### Temporal Confirmation Lens

```text
evidence_layer: strict
claim_status: lead
provocative_hypothesis:
  Some speculative-first integers may reveal useful paths before the core loop
  later confirms them.
false_positive_guarded_against:
  Treating later confirmation as proof that the earlier speculative path was
  important.
graph_native_observable:
  nodes with first_stage < confirmed_stage, plus incoming construction edges.
query_or_report:
  python3 moo_graph_query.py --db <corpus.sqlite> --confirmations --pretty
  python3 moo_research_report.py --db <corpus.sqlite> --corpus-baselines \
    --kind confirmed --rank-by confirmation_lag --control component_height --pretty
metric:
  confirmation_lag, incoming witness diversity, operation histogram.
null_model_or_control:
  component-height or denominator-matched confirmed nodes.
promotion_criteria:
  Confirmation lag is accompanied by repeated or diverse strict construction
  witnesses and persists under nearby corpus bounds.
kill_criteria:
  The lag is only a predictable consequence of the core integer index or bounds.
allowed_claim_language:
  "This node was first recorded speculatively and later confirmed by the core
  loop."
disallowed_claim_language:
  "The speculative construction predicted the integer" without a control.
```

### Operation Ecology Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  The balance of +, -, *, and / around a node may reveal construction roles
  that value-only reports hide.
false_positive_guarded_against:
  Calling a node central solely because it has many raw edge occurrences.
graph_native_observable:
  incoming and outgoing operation histograms, normalized witness counts, and
  shared-input neighborhoods.
query_or_report:
  python3 moo_research_report.py --db <corpus.sqlite> --node <p/q> --pretty
metric:
  operation histogram, normalized witness count, outgoing participation.
null_model_or_control:
  denominator or component-height peer groups, with commutative duplicates
  reported separately from directed witnesses.
promotion_criteria:
  Operation imbalance persists in corpus-wide rankings and is visible in exact
  construction edges.
kill_criteria:
  The imbalance is explained by operation ordering, commutative duplication, or
  bounds.
allowed_claim_language:
  "This node's incoming construction events are division-heavy in this corpus."
disallowed_claim_language:
  "This operation signature has mathematical meaning" before controls.
```

### Quadratic Shell Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  MoO may expose rational point families satisfying exact quadratic invariants
  before any Euclidean circle language is earned.
false_positive_guarded_against:
  Smuggling in geometry, angle, circumference, area, or pi by calling
  x*x + y*y = r*r a circle too early.
graph_native_observable:
  rational component nodes x, y, r; exact Q(x, y) = r*r check; first stages;
  confirmation status; construction witnesses; operation histograms; sign
  symmetry coverage.
query_or_report:
  python3 moo_circle_probe.py --db <corpus.sqlite> --unit-circle --node 3/4 --pretty
  python3 moo_circle_probe.py --db <corpus.sqlite> --unit-circle --pretty
  python3 moo_circle_probe.py --db <corpus.sqlite> --pythagorean --pretty
metric:
  complete component-node count, max component first stage, component witness
  count, denominator distribution, sign-symmetry coverage.
null_model_or_control:
  denominator-matched rational controls, construction-cost matched controls,
  placebo quadratic forms, graph shuffles, and bound-sensitivity checks.
promotion_criteria:
  Quadratic-shell candidates show stable graph-visible structure across strict
  corpora and beat matched controls. Later orbit language requires exact
  Q-preserving transformations.
kill_criteria:
  Matched placebo curves score similarly, the effect disappears under small
  corpus-bound changes, or only hand-picked nodes support the observation.
allowed_claim_language:
  "MoO has rational quadratic-shell candidates with graph-visible construction
  evidence."
disallowed_claim_language:
  "MoO defines the circle" or "MoO constructs pi."
```

### Euler Reciprocal Mass Lens

```text
evidence_layer: external_probe
claim_status: lead
provocative_hypothesis:
  Euler-style reciprocal-square and finite-product structures may give MoO a
  graph-native route to pi shadows without decimal target-hunting.
false_positive_guarded_against:
  Treating zeta(2), sine products, or Euler products as internal MoO objects
  before MoO has exact finite rational structures and controls.
graph_native_observable:
  nodes for 1/n^2, partial sums S_N, finite prime products, denominator growth,
  construction witnesses, return-to-zero corridors, and prime/composite
  neighborhood differences.
query_or_report:
  Delayed. Governance starts in
  research/euler/EULER_RECIPROCAL_MASS_AND_CIRCLE_LENS_NOTE.md.
metric:
  partial-sum construction cost, denominator growth, witness diversity,
  prime-product versus sum agreement, prime/composite residuals.
null_model_or_control:
  matched composite controls, denominator/height controls, constant placebos,
  and held-out strict corpora.
promotion_criteria:
  Exact finite reciprocal-mass/product structures show stable graph behavior
  beyond controls before any pi-shadow language is used.
kill_criteria:
  Raw approximation explains the observation, many unrelated constants score
  similarly, or graph shuffles preserve the signal.
allowed_claim_language:
  "MoO can inspect exact finite reciprocal-square term and partial-sum nodes
  when they are present in this strict corpus."
disallowed_claim_language:
  "MoO constructs pi from zeta(2)."
```

### Order-4 Projection Lens

```text
evidence_layer: external_probe
claim_status: lead
provocative_hypothesis:
  Stable strict graph families may support non-operational projected anchors
  such as non-rational constants, circle-like invariants, or asymptotic
  organizing points.
false_positive_guarded_against:
  Defining the projected object after seeing an exciting pattern, mistaking
  approximation accuracy for structure, or treating an analysis anchor as a
  runtime object.
graph_native_observable:
  exact source-family nodes and edges, source stages and corpus bounds,
  construction witnesses, neighborhoods, operation signatures, confirmation
  status, and held-out graph structure.
query_or_report:
  ORDER4_PROJECTION_PROTOCOL.md defines the projection certificate. Concrete
  reports must name a source family, projection rule, primary metric, controls,
  holdout, prediction, and kill rule.
metric:
  prediction lift over matched controls, projection stability, held-out error
  reduction, recurrence/compression improvement, control-adjusted witness
  diversity, or organization of held-out neighborhoods.
null_model_or_control:
  denominator-matched, first-stage-matched, construction-cost-matched,
  continued-fraction controls, placebo constants, placebo invariants, graph
  shuffles, and operation-label shuffles as appropriate.
promotion_criteria:
  Avoid the word promotion here. An Order-4 anchor gains credibility only when
  it predicts or organizes held-out strict graph structure better than controls.
kill_criteria:
  The anchor drifts under stage growth, many unrelated anchors fit equally
  well, the source family was target-selected after the fact, baselines explain
  the signal, shuffles preserve the effect, or the projection has no held-out
  predictive value.
allowed_claim_language:
  "This is an Order-4 projected inspection anchor inferred from this exact
  graph family by this projection rule."
disallowed_claim_language:
  "This Order-4 anchor is a certainty, runtime node, operand, theorem, or
  completed object inside strict MoO."
```

### Stage Dynamics Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  Strict-stage MoO may show reproducible deterministic stage dynamics:
  persistence, accumulation, threshold shifts, recurrence, and divergence.
false_positive_guarded_against:
  Calling ordinary graph growth, low-denominator bias, or raw edge popularity
  "chaos", "attractors", or "bifurcations".
graph_native_observable:
  stage snapshots G_U; node/edge growth; operation distribution; denominator
  bands; confirmation transitions; top-k construction-gathering nodes;
  edge-local symbolic motif distributions.
query_or_report:
  research/dynamics/DYNAMICS_TEST_PROTOCOL.md defines planned report shapes.
  Future tool target:
  python3 moo_dynamics_probe.py --stage-persistence --checkpoints 10,20,40,60,80
metric:
  top-k checkpoint appearances, witness diversity, operation diversity,
  confirmation lag, stage-window symbol frequency, neighborhood Jaccard
  divergence.
null_model_or_control:
  denominator-matched peers, first-stage-matched peers, stage-size null,
  exposure controls, operation-label shuffle, graph shuffle, held-out strict
  corpora.
promotion_criteria:
  A candidate survives preregistered thresholds, saved report review, matched
  controls, and at least one robustness check.
kill_criteria:
  Total corpus growth explains the observation, matched peers behave similarly,
  small bound changes erase it, or raw edge count is the only support.
allowed_claim_language:
  "persistent accumulation candidate" and "parameter-threshold shift candidate".
disallowed_claim_language:
  "MoO is chaotic", "MoO has attractors", "MoO has bifurcations", "MoO has
  Lyapunov exponents", or "MoO has strange attractors".
```

## Quarantined Exploratory Lenses

These lenses are allowed to record leads, but they cannot make strict-stage
claims until they reproduce through strict graph queries.

### Motif / Hinge Lens

```text
evidence_layer: exploratory
claim_status: lead
provocative_hypothesis:
  Some rational values act as construction hinges in bounded exploratory
  closure reports.
false_positive_guarded_against:
  Promoting exploratory closure artifacts into aligned MoO claims.
graph_native_observable:
  repeated operation motifs, high-output neighborhoods, alternate witnesses.
query_or_report:
  historical motif reports first; strict reproduction must use
  moo_research_report.py or moo_graph_query.py over a strict graph corpus.
metric:
  motif membership, report-level hub count, strict witness count if reproduced.
null_model_or_control:
  denominator-matched controls and nearby corpus-bound sensitivity checks.
promotion_criteria:
  The same value or motif has a strict-stage graph observable with explicit
  controls.
kill_criteria:
  The hinge disappears when speculative operands are disallowed.
allowed_claim_language:
  "-4/3 is an exploratory hinge under the named closure mode and bounds."
disallowed_claim_language:
  "MoO discovers -4/3 as a strict organizing center" without strict evidence.
```

### Aperture Lens

```text
evidence_layer: exploratory
claim_status: lead
provocative_hypothesis:
  Some constructions leave and return to a bounded value region in ways that
  expose lower-aperture witnesses.
false_positive_guarded_against:
  Mistaking final value admissibility for path admissibility.
graph_native_observable:
  first witness path, maximum intermediate aperture, alternate witnesses.
query_or_report:
  historical aperture reports until strict ancestry extraction exists.
metric:
  first witness aperture, alternate lower-aperture witness count.
null_model_or_control:
  denominator-matched and value-range controls.
promotion_criteria:
  Strict graph ancestry can reproduce the witness behavior without speculative
  operands.
kill_criteria:
  The effect depends on exploratory reuse of speculative nodes.
allowed_claim_language:
  "This is an aperture lead from exploratory closure."
disallowed_claim_language:
  "This is a strict MoO cost" before strict ancestry support.
```

## Delayed Lenses

Fourier, Hodge, spectral, circle-method, constant-recognition, PSLQ, RIES, and
OEIS lenses stay delayed until a strict graph report produces candidate chains
or edge-flow data large enough to justify them.

Their allowed role is:

```text
strict graph -> candidate structure -> external scrutiny
```

not:

```text
external name -> rational search -> MoO claim
```
