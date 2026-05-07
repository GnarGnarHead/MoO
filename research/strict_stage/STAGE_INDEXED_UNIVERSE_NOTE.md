# Stage-Indexed MoO Universe

> Status: framing note for core-loop emergence.
>
> This note records the rule that whole numbers are not assumed in advance.
> They enter the MoO universe when the core iteration of `1` reaches them.

## Core Rule

MoO functions in a universe where numbers emerge from iteration.

Before the core loop has iterated through `1` twice, there is no confirmed `2`
in the MoO universe.

```text
U1: 1
U2: 1, 2
U3: 1, 2, 3
U4: 1, 2, 3, 4
...
Un: 1, 2, 3, ..., n
```

`1` is still the only certainty. Values `2..n` are confirmed positive
whole-number iterations of `1`; they are not second certainties.

## Speculative Construction

Once values have appeared through the core loop, they can participate in
constructions.

Example:

```text
At U3:
  2 exists
  3 exists
  2 * 3 can be recorded as a construction
  6 remains speculative
```

`6` is not confirmed merely because `2 * 3` produced it. It becomes confirmed
only when the core loop reaches:

```text
U6
```

So the important distinction is:

```text
speculative construction: value produced by allowed relations
confirmed iteration: value reached by the core 1 loop
```

## Orders

The current order reading is:

```text
Order 1:
  1, the only certainty

Order 2:
  positive whole-number iterations confirmed by the current stage

Order 3:
  constructions not confirmed by the current stage
```

Fractions are Order 3. Positive whole-number constructions above the current
stage are Order 3 until the stage reaches them. Values like `0` and negative
integers are relational/removal constructions; they are not positive
whole-number iterations of the core loop.

## Why This Matters

This keeps MoO from smuggling ordinary arithmetic into the foundation.

Ordinary arithmetic says:

```text
2 and 3 already exist, so 6 exists.
```

MoO says:

```text
2 and 3 exist once the core loop reaches them.
2 * 3 may then produce 6 as a speculative construction.
6 is not confirmed until the core loop reaches 6.
```

That is the alignment rule for future studies.

## Local Inspection Command

Use this low-compute check to inspect the rule without rerunning the larger
closure studies:

```sh
python3 order_transition_study.py --max-stage 6 --pretty
```

The report separates:

```text
confirmed positive iterations
speculative future whole-number constructions
unconfirmed rational constructions
relational/removal integer constructions
promotions when the core loop reaches a previously speculative whole number
```

For example, the report should show that `6` can be produced by constructions
before stage `6`, but is not confirmed until `U6`.

## Compute Consequence

The stage-indexed rule also limits computation.

Speculative constructions are recorded as real MoO nodes, but they do not
become operands merely because they have been produced. They are speculated on,
not operated on. Only the confirmed positive whole-number iterations in the
current stage are allowed as core operands. Once the core loop promotes a
speculative node by confirming it, further speculation can proceed from that
promoted certainty.

So this is allowed:

```text
U3 confirms: 1, 2, 3
2 * 3 produces speculative 6
```

But this is not allowed in aligned MoO:

```text
speculative 6 immediately becomes an operand
```

That older behavior belongs to the exploratory closure scripts. It is useful as
a broad analysis lens, but it computes on speculative nodes and should not be
confused with the stage-indexed MoO core.

Practical distinction:

```text
stage-indexed core:
  operands = confirmed positive iterations only
  speculative outputs = real nodes with weaker epistemic status, inspected but not operated on
  promoted outputs = available for further speculation

exploratory closure:
  operands = all retained generated values, including speculative nodes
```

The exploratory closure behavior is historical and useful only as a hypothesis
artifact. It is not aligned MoO computation. This is why aligned stage-indexed
runs scale much more gently than the older bounded closure scans.
