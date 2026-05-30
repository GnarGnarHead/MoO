# Branch Formalization Note

> Status: core support note.
>
> This note makes branch probes precise enough to run without replacing the
> MoO-native meaning of branch. It does not demote branches into ordinary
> arithmetic labels. It says how a branch must be named, witnessed, and reported
> before a probe can make a branch claim.

## Governing Definition

```text
branch = same relation repeated along the unfolding of MoO
```

A branch is not a formula family and not a value list.

A branch is the repeated relation. Values are its shadows. Witnesses show where
a value enters the branch.

## Why Formalize

Branch language is useful only if it preserves this distinction:

```text
value appears
```

is weaker than:

```text
value appears through this repeated relation
```

The formalization exists to prevent three common mistakes:

```text
classical truth -> MoO-witnessed truth
value presence -> branch presence
positive-spine evidence -> full operator-fan evidence
```

## Branch Card

Every branch probe should have a branch card before the probe is interpreted.

```text
branch_name:
moo_relation:
operator_fan_root:
active_field:
eligible_sources:
witness_event:
shadow_values:
membership_reading:
non_membership_reading:
linearity_reading:
relation_distance:
stage_distance:
witness_depth:
interaction_reading:
machine_fields:
known_classical_shadow:
allowed_claim_language:
disallowed_claim_language:
weakening_or_kill_rule:
```

### Field Meanings

```text
branch_name:
  the MoO branch name, optionally followed by an ordinary shadow label

moo_relation:
  the repeated relation being studied

operator_fan_root:
  expansion, cancellation, preservation, ratio, product, or mixed

active_field:
  the field of observation, such as positive-spine strict corpus U80;
  current reports must not pretend this is the full signed operator-fan field

eligible_sources:
  which values, witnesses, or nodes may enter the branch relation

witness_event:
  the exact emergence event that places a value into the branch reading

shadow_values:
  the values cast by the branch relation

membership_reading:
  what makes an event or value count as participating in the branch

non_membership_reading:
  what would show that a value is absent from, not witnessed by, or only
  externally labeled as the branch

linearity_reading:
  what makes this a repeated lineage rather than a scattered set of values

relation_distance:
  the shared relation-distance from `1`, not merely stage number

stage_distance:
  where the witness appears in the selected field of observation

witness_depth:
  how much witnessed structure is required before the reading is earned

interaction_reading:
  what would count as interaction with another branch

machine_fields:
  retained edge rows, inferred permitted events, node presence, blockers, and
  any other bookkeeping needed by the tool

known_classical_shadow:
  the ordinary arithmetic name, if there is one

weakening_or_kill_rule:
  what would weaken the branch reading or show that the probe is only reporting
  a classical label or corpus artifact
```

## Naming Rule

Name the MoO relation first and the ordinary shadow second.

Good:

```text
twofold self-addition branch / even shadow
self-multiplicative branch / square shadow
product-landing branch / composite shadow
prime branch / irreducibility shadow
```

Short forms such as `even branch`, `square branch`, and `prime branch` are
allowed after the relation has been defined. They are not license to skip the
witness.

This does not mean primes are not a branch. It means the prime branch must be
read as a repeated relation in the counting/product field, not merely as a
factorization label imported from ordinary arithmetic.

## Branch Linearity

`Linear` does not mean evenly spaced by value, stage, or visual graph layout.

In branch language, linearity means:

```text
the same relation keeps reappearing along the selected unfolding of MoO
```

Examples:

```text
twofold self-addition:
  n+n repeats as the field unfolds

self-multiplication:
  n*n repeats as the field unfolds

prime relation:
  the prime relation repeats along the counting/product field
```

Members can appear at different stages and still share branch-linearity because
their relation-distance is the same even when their stage-distance differs.

## Required Machine Reading

Branch reports should separate the MoO reading from bookkeeping fields.

Minimum machine fields:

```text
value_visible:
spine_witness:
branch_relation_permitted:
retained_branch_witness:
implied_unretained_relation:
field_blockers:
all_relevant_witnesses:
classification_basis:
```

Recommended `classification_basis` values:

```text
graph_witnessed:
  the relevant witness is present in the saved field

inferred_from_field_absence:
  the reading depends on absence in a named finite field

inferred_from_generator_rule:
  the relation is permitted by the generator but not retained in the saved field

arithmetic_shortcut:
  ordinary arithmetic was used as a helper; this must not be treated as a
  MoO witness
```

## Canonical Branch Cards

### Expansion Branch

```text
branch_name:
  expansion branch / successor shadow
moo_relation:
  n -> n + 1
operator_fan_root:
  + expands
active_field:
  positive-spine strict corpus, unless a signed operator-fan corpus is named
witness_event:
  n + 1 -> n+1
known_classical_shadow:
  successor / counting-spine growth
```

### Cancellation Branch

```text
branch_name:
  cancellation branch / zero shadow
moo_relation:
  n -> n - n -> 0
operator_fan_root:
  - cancels
active_field:
  current positive-spine corpora can inspect retained cancellation outputs,
  but full cancellation/removal requires the future signed operator-fan field
witness_event:
  n - n -> 0
known_classical_shadow:
  zero / additive inverse structure
```

### Preservation Branch

```text
branch_name:
  preservation branch / identity shadow
moo_relation:
  n * 1 -> n
  n / 1 -> n
operator_fan_root:
  * preserves
  / preserves
witness_event:
  multiplication or division by `1` returning the source value
known_classical_shadow:
  multiplicative identity
```

### Return-To-One Branch

```text
branch_name:
  return-to-one branch / ratio identity shadow
moo_relation:
  n / n -> 1
operator_fan_root:
  / preserves through relation
witness_event:
  n / n -> 1
known_classical_shadow:
  self-ratio identity
```

### Twofold Self-Addition Branch

```text
branch_name:
  twofold self-addition branch / even shadow
moo_relation:
  n -> n + n
operator_fan_root:
  + expands
witness_event:
  n + n -> 2n
known_classical_shadow:
  even numbers
weakening_or_kill_rule:
  the report only lists even values without self-addition witnesses or inferred
  branch status
```

### Self-Multiplicative Branch

```text
branch_name:
  self-multiplicative branch / square shadow
moo_relation:
  n -> n * n
operator_fan_root:
  * preserves by self-relation, then expands as a value shadow
witness_event:
  n * n -> n^2
known_classical_shadow:
  squares
weakening_or_kill_rule:
  the report treats `n^2` appearing through the counting spine as equivalent to
  being witnessed through `n*n`
```

### Product-Landing Branch

```text
branch_name:
  product-landing branch / composite shadow
moo_relation:
  a * b -> n, with a,b > 1
operator_fan_root:
  * product relation
witness_event:
  retained or inferred nontrivial product landing on a value
known_classical_shadow:
  composites
weakening_or_kill_rule:
  the report uses ordinary factorization without naming graph witnesses or the
  field of observation
```

### Prime Branch

```text
branch_name:
  prime branch / irreducibility shadow
moo_relation:
  the repeated prime relation in the counting/product field
membership_reading:
  n is witnessed through the counting spine, and no nontrivial product-landing
  branch witnesses n in the named field of observation
non_membership_reading:
  a nontrivial product-landing witness enters n in the named field
known_classical_shadow:
  primes
machine_fields:
  classification_basis
weakening_or_kill_rule:
  the report silently treats ordinary primality as a MoO witness, or makes an
  absolute absence claim from a finite field without saying so
```

The prime branch is a branch. The formal card exists so it is not reduced to
either a textbook label or a mere failure flag.

### Reciprocal Branch

```text
branch_name:
  reciprocal branch / unit-fraction shadow
moo_relation:
  n -> 1 / n
operator_fan_root:
  / ratio relation
witness_event:
  1 / n -> 1/n
known_classical_shadow:
  unit fractions
```

### Shell-Relation Branch

```text
branch_name:
  shell-relation branch / circle-adjacent shadow
moo_relation:
  x enters self-multiplicative branch: x*x
  y enters self-multiplicative branch: y*y
  r enters self-multiplicative branch: r*r
  x*x and y*y enter addition
  the additive result agrees with r*r
operator_fan_root:
  mixed: self-relation plus addition
witness_event:
  all required square and additive agreement witnesses, with field status
known_classical_shadow:
  rational quadratic shells / Pythagorean structure
weakening_or_kill_rule:
  the report calls the formula a circle before repeated witnessed branch
  interaction is shown
```

## Branch Interaction

Branch interaction is not automatic overlap of value sets. It must name the
interaction predicate.

Examples:

```text
shared value:
  the same value has witnesses from two branches

shared witness:
  one retained event satisfies two branch rules

synchronized emergence:
  two branch witnesses appear within a named stage or field window

structural dependency:
  one branch reading requires witnesses from another branch
```

For geometry work, the shell-relation branch has structural dependency on the
self-multiplicative branch. That does not yet define a Euclidean circle.

## Probe Order

The safest branch probe order is:

```text
1. twofold self-addition / even shadow
2. self-multiplicative / square shadow
3. product landing / composite shadow
4. prime branch / irreducibility shadow
5. reciprocal branch / unit-fraction shadow
6. shell-relation branch / circle-adjacent shadow
```

Cancellation, preservation, return-to-one, opposition, and signed removal are
closer to the operator fan, but the current saved strict corpora are
positive-spine scoped. They should be formalized conceptually now and measured
fully after the signed operator-fan field exists.

## Claim Rule

Allowed branch claim:

```text
In field F, relation R is witnessed by these events and casts these values as
branch shadows.
```

Stronger branch claim:

```text
In field F, branch R interacts with branch S under this explicit interaction
predicate and survives the stated weakening checks.
```

Disallowed shortcut:

```text
These values have a familiar arithmetic name, therefore MoO has witnessed the
branch.
```
