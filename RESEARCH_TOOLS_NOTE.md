# Research Tools for MoO Closure

> Status: working research note.
>
> This note separates MoO-native observables from external confirmation tools.
> The tools below are not the theory. They are ways to inspect, compare, and
> pressure-test the structure MoO already produces.

## Core Separation

MoO's primary object is the constructive arithmetic field grown from `1`.
Research should therefore start inside the closure process, not with outside
targets.

The useful split is:

- **MoO-native observables**: structure produced by the closure itself.
- **Confirmation tools**: outside comparators used afterward to check whether
  the internal structure aligns with known mathematics.

This keeps the project from becoming "approximate known constants with
rationals." The intended direction is:

```text
closure -> internal structure -> candidate chains -> external recognition
```

not:

```text
named constant -> rational search -> best hit
```

## MoO-Native Observables

These are the main research layer.

### First-Seen Order

For each rational value `p/q`, record the earliest closure round in which it
appears. This is the simplest internal emergence measure.

Useful question:

```text
Which values become visible early from one?
```

### Witness and Construction Cost

Record the first arithmetic event that creates a value, then later expand this
into full ancestry when needed.

Useful question:

```text
What did the value require, structurally, before it could appear?
```

### Derivation Multiplicity

Count how many distinct construction events land on the same reduced rational
value. A value reached many ways may be more central than a value reached once.

Useful question:

```text
Which values act like convergence points for many construction paths?
```

### Operation Signature

Track whether a value is mainly created by `+`, `-`, `*`, `/`, or mixed paths.

Useful question:

```text
Do different number families have different operation fingerprints?
```

### Emergence Chains

Follow best-so-far or structurally prominent values across rounds, but treat the
chain as a MoO object before assigning it a classical name.

Useful question:

```text
Which rational chains look stable before we ask what they approximate?
```

### Lens Agreement

Compare whether the same values appear important under multiple MoO lenses:
value identity, construction identity, grounding behavior, flow/density, and
first-seen order.

Useful question:

```text
Which values remain important after changing the lens?
```

## Confirmation Tools

These tools are useful only after MoO has produced candidate values or chains.
They should confirm, contextualize, or challenge MoO observations, not define
them.

### Continued Fractions

Classify a MoO approximant as a convergent, semiconvergent, or non-continued
fraction near miss.

What it contributes:

```text
Checks whether MoO's emergence order rediscovers classical best approximation.
```

### Stern-Brocot, Calkin-Wilf, and Farey Order

Place a MoO value inside standard rational-tree or denominator-order baselines.

What it contributes:

```text
Shows whether MoO finds a value early relative to other rational enumerations.
```

### Integer Complexity and Addition Chains

Compare MoO emergence to classical "from ones" construction costs for integers
and numerator/denominator pairs.

What it contributes:

```text
Connects MoO's constructive cost to established construction-cost language.
```

### Decoy Targets

Use random real values or rational controls as a sanity check.

What it contributes:

```text
Tests whether apparent attractors are special or merely density under bounds.
```

### OEIS, PSLQ, and RIES

Use sequence and relation-recognition tools only after MoO has produced stable
chains.

What they contribute:

```text
Suggests names or formulas for internally discovered chains.
```

## Local Workflow

A hardware-light workflow should compute each bounded closure once, then reuse
the saved ledger for repeated analysis.

First, generate the MoO-native ledger:

```sh
python3 native_emergence_scan.py --rounds 5 --include-ledger --write out/experiments/native_r5_full.json
```

Then rerank or inspect that saved ledger without recomputing closure:

```sh
python3 native_emergence_scan.py --from-report out/experiments/native_r5_full.json --top-k 25 --pretty
```

Run a residual study to subtract the obvious skeleton:

```sh
python3 residual_emergence_study.py --report out/experiments/native_r5_full.json --top-k 25 --write out/experiments/residual_r5.json
```

Run a motif graph study to inspect reusable construction scaffolds:

```sh
python3 motif_graph_study.py --report out/experiments/native_r5_full.json --top-k 20 --write out/experiments/motif_r5.json
```

Run the target-oriented confirmation layer separately:

```sh
python3 emergence_baselines.py --rounds 5 --targets pi,e,sqrt2,phi,ln2 --compact --pretty
```

Interpret the outputs in four passes:

1. Read `native_emergence_scan.py` output as MoO-native data:
   `first_seen_round`, `first_witness`, `derivation_events`,
   `operation_signature`, local neighbors, and rankings.
2. Read `residual_emergence_study.py` output as a filtered MoO-native
   calibration layer: it asks which values remain prominent after skeleton hubs
   and denominator effects are discounted.
3. Read `motif_graph_study.py` output as a structural layer: it asks whether
   values sit downstream of reusable parent hubs and operation motifs.
4. Read `emergence_baselines.py` output as confirmation/context:
   `emergence_tuple`, `cf_class`, `stern_brocot_depth`, `calkin_wilf_rank`,
   `farey_order`, and `integer_complexity`.

The first three passes are the project. The fourth pass is the comparison layer.

## What to Avoid

Avoid treating a named constant as the whole explanation. A result like `22/7`
for `pi` is interesting only because MoO created `22/7` at a specific closure
stage, through a specific witness, inside a specific field of neighboring
rationals.

The recognition step may say "this is close to `pi`." The MoO question is:

```text
Why did this rational become visible here?
```
