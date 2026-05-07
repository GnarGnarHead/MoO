# Stage-Indexed Core: n=100 First Study

> Status: first compact study of the strict stage-indexed core.
>
> Source artifact:
> `out/experiments/stage_indexed_core_r100.json`
>
> Summary artifact:
> `out/experiments/stage_indexed_core_r100_summary.json`

## Framing

This run uses the aligned core rule:

```text
confirmed positive iterations can be operands
speculative constructions are recorded
speculative constructions are inspected, not operated on
promotion by the core loop permits later operation
```

So a value can be produced before it is confirmed, but it cannot drive further
core construction until the core loop reaches it.

## Run Summary

```text
max stage: 100
stage count: 100
stage-100 construction events: 40000
stage-100 unique constructed values: 9014
stage-100 unique/event ratio: 0.22535
```

The construction-event count follows the stage rule:

```text
events at stage n = 4 * n^2
```

because each confirmed positive operand pair is tested under:

```text
+  -  *  /
```

## First Construction Versus Confirmation

The important measurement is:

```text
promotion gap = confirmed stage - first constructed stage
```

Examples:

```text
6    first constructed at U3   confirmed at U6
12   first constructed at U4   confirmed at U12
24   first constructed at U6   confirmed at U24
60   first constructed at U10  confirmed at U60
100  first constructed at U10  confirmed at U100
```

This shows the intended behavior: construction can precede confirmation, but
confirmation still belongs to the core `1` loop.

## Multiplication Signal

Among promoted values from `3..100`:

```text
promotions counted:      98
multiplicative routes:   74
additive-only routes:    24
```

The additive-only values are:

```text
3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97
```

These are exactly the primes between `3` and `100` in this run. That is not a
new primality theorem, but it is a useful alignment check: under this core rule,
prime-like values do not receive an earlier multiplication witness.

## Largest Promotion Gaps

Top examples by promotion gap:

```text
100  first U10  confirmed U100  gap 90   witness 10 * 10
99   first U11  confirmed U99   gap 88   witness 9 * 11
96   first U12  confirmed U96   gap 84   witness 8 * 12
98   first U14  confirmed U98   gap 84   witness 7 * 14
90   first U10  confirmed U90   gap 80   witness 9 * 10
```

Top examples by confirmation/first-construction ratio:

```text
100  ratio 10  witness 10 * 10
81   ratio 9   witness 9 * 9
90   ratio 9   witness 9 * 10
99   ratio 9   witness 9 * 11
64   ratio 8   witness 8 * 8
72   ratio 8   witness 8 * 9
80   ratio 8   witness 8 * 10
88   ratio 8   witness 8 * 11
96   ratio 8   witness 8 * 12
```

This is the clearest current signal: factor structure creates early speculative
whole-number constructions long before the core loop confirms them.

## Fractions

The inspected value:

```text
87/32
```

first appears at:

```text
U87 via 87 / 32
```

It remains Order 3. This is correct under the aligned rule: fractions can be
constructed, but they are not confirmed positive whole-number iterations, and
they do not become core operands.

## Main Takeaway

The strict stage-indexed core keeps the philosophical alignment and still
produces useful structure.

The first useful native observable is not "which speculative values recursively
generate more values." It is:

```text
how early a value can be constructed
versus
when the core loop confirms it
```

That gap separates additive-only values from values with earlier multiplication
witnesses, and gives a clean low-compute structure to study at much higher `n`.
