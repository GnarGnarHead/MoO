# Epistemic Order in MoO

> Status: canonical framing note.
>
> This note records the current MoO meaning of certainty and order. It uses the
> project framing directly and should be preferred over generic graph language.

## Core Claim

```text
1 is the only certainty.
```

Everything else is constructed from iterations of `1`.

MoO began as an attempt to prove `2` from `1`. That attempt failed as certainty:
to get `2`, a previous instance of `1` has to be preserved and used again. That
previous instance is already once removed from the immediate certainty.

So `2` is not a second certainty. It is infinite distance from `1`.

## Stage-Indexed Universe

MoO should be read as a stage-indexed universe. Before the core `1` loop has
iterated twice, there is no confirmed `2` in the MoO universe.

The positive whole-number stages are:

```text
U1: 1
U2: 1, 2
U3: 1, 2, 3
...
Un: 1, 2, 3, ..., n
```

At stage `n`, the confirmed positive whole-number iterations are exactly
`1..n`. The system can still form speculative constructions from values that
already exist.

Example:

```text
At U3, both 2 and 3 exist.
So 2 * 3 can exist as a construction.
But 6 remains unconfirmed until U6.
```

This is the central rule:

```text
construction can precede confirmation;
confirmation comes from the core 1 loop reaching the value.
```

Speculative constructions are still nodes. Their uncertainty is epistemic, not
ontological: they are part of the MoO graph once constructed, but they are not
as certain as `1` or as confirmed core-loop iterations.

They are also not operands. A speculative node can be inspected, interpreted,
or selected by a probe, but MoO does not operate on it unless the core loop
later confirms it.

Once the core loop promotes a speculative node to a higher epistemological
certainty, MoO can speculate further from that promoted node. It does not
speculate on speculations.

## Orders

The current order language is:

```text
Order 1:
  the immediate certainty, 1

Order 2:
  confirmed positive whole-number iterations of 1

Order 3:
  unconfirmed constructions from iterations of 1
```

Previous instances of `1` are once removed from certainty. Confirmed positive
whole-number iterations are second order. Fractions, relational removals such
as `0` or negative values, and unconfirmed positive whole-number constructions
are third order unless a later analysis lens explicitly says otherwise.

## Confirmation By n

Order can change when the core iteration `n` confirms a positive whole number.

Example:

```text
3 * 2 produces 6
```

Once `2` and `3` exist, this construction can exist. If the current core
iteration is still less than `6`, then `6` is an unconfirmed construction:

```text
6 = third order
```

Once `n` reaches and confirms `6` as a whole-number iteration of `1`, `6`
becomes:

```text
6 = second order
```

This is the important status transition:

```text
unconfirmed positive whole-number construction
-> confirmed positive whole-number iteration of 1
```

## Fractions

Fractions such as:

```text
3/2
```

are third order. They are constructions from iterations of `1`, but they are not
confirmed positive whole-number iterations of `1`.

This does not make them invalid. It means they have a different epistemic
status.

Likewise, an unconfirmed positive whole-number construction is not discarded or
treated as non-MoO. It remains a speculative node until the core loop confirms
it.

## No Independent Operands

MoO should not be explained as if it starts with arbitrary numbers `a` and `b`.

If a report or script says:

```text
a / b
a * b
a + b
a - b
```

the MoO reading is:

```text
construction from iterations of 1
related to another construction from iterations of 1
```

Everything is constructed from `1`.

## Report Language

Some scripts and JSON fields still use conventional graph words:

```text
parent
child
hub
grounded
speculative
```

Those are implementation/report terms. They should not override the MoO
framing above.

The closest reading is:

```text
grounded Ref(1)        -> Order 1 certainty
grounded Ref(N > 1)    -> Order 2 confirmed positive whole-number iteration
other values           -> Order 3 unconfirmed or relational construction
```

The code can keep these field names for stability, but interpretation should
follow the order model in this note.

## Order 4 Is Not Certainty

Some research notes may use `Order 4` for projected objects such as
non-rational constants, circle-like invariants, or asymptotic anchors.

This does not add another certainty tier inside the graph.

Order 4 means:

```text
projected limit/invariant anchor inferred from stable Order-3 graph families
```

An Order-4 object is:

```text
analysis-layer
non-operational
not a runtime node
not an operand
not a confirmed fact
not a theorem
not more certain than Order 3
```

Order 4 is more abstract than Order 3, not more certain. It can guide
inspection, but it cannot participate in strict-stage computation.

Use:

```text
Order-4 projected object
asymptotic inspection anchor
projected invariant
non-rational projected constant
```

Do not use:

```text
Order-4 certainty
MoO constructs pi
MoO defines the Euclidean circle
```

See `ORDER4_PROJECTION_PROTOCOL.md` for the required projection certificate and
testing rules.

## Stage Versus Closure Round

The core iteration stage `n` is not the same as a closure round in the analysis
scripts.

The stage says which positive whole-number iterations are confirmed by the core
`1` loop. A closure round says how many passes of arithmetic construction have
been applied inside a chosen stage or saved corpus.

This prevents a construction like `2 * 3 = 6` from being mistaken for immediate
confirmation of `6`.
