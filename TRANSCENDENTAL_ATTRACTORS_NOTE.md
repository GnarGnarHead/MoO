# External Constant Probes in MoO Closure

> Status: research note.
>
> This note documents an empirical and conceptual insight from the current
> set-closure probes. It is not yet a theorem and is not runtime semantics for
> `constructionist_math.py`.

## External-Probe Framing

MoO does not construct transcendental constants as primitive objects, and the
runtime should not treat a rational as "about" a named constant.

Starting only from `1`, the bounded closure process under `+`, `-`, `*`, and `/`
generates finite rational fields. External constant probes can then test whether
some speculative nodes happen to be close to named constants.

The novelty is not that rational numbers approximate real constants. That is
classical. The MoO-native object is the speculative node and its construction
history. Approximation is an external test layered on afterward:

- when a rational first appears,
- how complex its construction path is,
- how many derivations flow into its value class,
- whether it is grounded or speculative in the graph model,
- and whether an external probe selects it for further comparison.

In this reading, arithmetic is not only a set of values with operations. It is a
stratified construction process in which value, construction history, derivation
multiplicity, grounding, and approximation behavior are all first-class.

## Probe Observation

Using the stateless closure probe:

```sh
python3 constant_probe.py --rounds 5 --targets pi,e,sqrt2,phi,ln2 --top-k 5 --pretty
```

with the default bounds:

- `max_abs_p = 100`
- `max_abs_q = 100`
- `max_abs_value = 4.0`

the round-5 closure set has `4439` retained rational values. As an external
constant-probe result, the following speculative nodes are the best matches in
that bounded window:

| target | round-5 best | absolute error | note |
| --- | ---: | ---: | --- |
| `pi` | `22/7` | `0.0012644892673496777` | classical convergent |
| `e` | `87/32` | `0.0004681715409549092` | strong bounded-window external match |
| `ln2` | `52/75` | `0.0001861527733880708` | strong bounded-window external match |
| `sqrt2` | `99/70` | `0.00007215191261922271` | algebraic control |
| `phi` | `34/21` | `0.0010136302977241662` | Fibonacci-ratio control |

The algebraic controls matter. `sqrt2` and `phi` are not transcendental, but they
help separate a general "good rational approximation emerges" phenomenon from a
specifically transcendental story.

## Interpretation

The current evidence supports a cautious hypothesis:

> Finite MoO closure produces speculative nodes whose construction histories can
> be studied natively, and external constant probes can select some of those
> nodes for comparison.

This is stronger than saying "rationals are dense." Density is an existence
statement over a completed set. MoO asks a different question:

> Which speculative nodes appear early under a specific constructive arithmetic
> process from `1`, before any external target interpretation is applied?

That turns convergence into an observable structural phenomenon.

## What This Does Not Claim

This note does not claim:

- that MoO has proven new values for `pi`, `e`, or any transcendental;
- that the runtime graph directly contains transcendental numbers;
- that a node close to an external constant is meaningful without a null model;
- that the current bounded search is unbiased;
- that this is already a new foundation for analysis.

The current result is a research signal, not a theorem.

## Research Program

The next step is to turn "external probes selected these speculative nodes" into
measurable claims.

Keep two layers separate:

- **MoO-native observables**: first-seen order, witnesses, derivation
  multiplicity, operation signatures, grounding behavior, and emergence chains.
- **Confirmation tools**: continued fractions, rational-tree placement, integer
  complexity, decoy targets, and sequence/relation-recognition methods.

The first layer is the project. The second layer checks whether MoO's internal
structure aligns with, diverges from, or sharpens known mathematical structure.
See `RESEARCH_TOOLS_NOTE.md` for the working boundary.

### 1. Define an Emergence Score

For a rational `p/q` first seen at closure round `r`, track:

- first-seen round,
- numerator and denominator size,
- expression/construction witness,
- number of derivation witnesses,
- graph depth if embedded into `Graph`,
- approximation error against target constants.

A simple first score could be:

```text
emergence_score(target, p/q) =
    (first_seen_round, denominator, abs(numerator), error)
```

More serious scores should include derivation multiplicity and witness length.

### 2. Compare Against Null Models

The critical question is whether external probes select MoO nodes earlier than a
baseline would expect.

Useful baselines:

- best rational in the same `|p|`, `|q|`, and value bounds,
- random rational samples from the same bounds,
- continued-fraction convergents for the target,
- Stern-Brocot / Calkin-Wilf enumeration depth,
- expression-tree enumeration by operator count.

### 3. Track External-Probe Persistence

An external probe has stronger evidence if its selected nodes:

- keep improving across rounds,
- remain near known continued-fraction convergents,
- reappear through multiple independent derivations,
- are stable under changed bounds,
- are stable under changed operation ordering.

### 4. Separate Constant Families

Use target groups:

- transcendental: `pi`, `e`, `tau`, `ln2`, `ln10`;
- algebraic irrational controls: `sqrt2`, `sqrt3`, `phi`;
- rational controls: values like `3/2`, `7/5`, `22/7`;
- decoys: random real numbers generated from a fixed seed.

If all external targets behave the same, the phenomenon is mostly
rational-density plus bounded enumeration. If named constants behave
differently, that is the signal.

### 5. Promote From Probe to Corpus

Use `moo_observatory.py` for persistent runs so the project can compare runs,
resume work, and inspect first witnesses:

```sh
python3 moo_observatory.py --db out/transcendental_attractors.sqlite --to-round 5 --targets all
```

Round 6 and beyond can become expensive quickly under the default bounds, so the
observatory path is the right place for longer research.

## Working Hypothesis

MoO may be exposing a constructive topology on arithmetic: not a topology of
preexisting real numbers, but a topology of rational visibility from `1`.

Under that topology, transcendentals are not constructed as objects. They remain
external probes that may reveal stable directions in the expanding rational
closure.
