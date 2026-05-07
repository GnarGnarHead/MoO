# Recurrence Frames Note

> Status: parked future-study note.
>
> This note names a related area without making it active project machinery.
> The current correction focuses on branches as repeated relation-lineages
> inside the present strict counting-spine field.

## Why This Is Parked

Not every repeated structure should be called a branch.

The project should separate:

```text
recurrence frame:
  how recurrence unfolds and carries memory

branch:
  repeated relation-line inside a recurrence field
```

This avoids flattening Fibonacci, doubling-as-iteration, and triangular
accumulation into the same category as evens, squares, products, primes, or
shells.

The eventual reason to return to recurrence frames is divergence:

```text
how 1 becomes 2
how 2 becomes 3
how 2 becomes 4
```

Those are not just different values. They are different ways recurrence may
preserve, count, relate, double, or branch from the first move beyond
certainty. Stacking recurrence frames may become a way to study how structure
diverges from `1`.

That work is parked. The current project focus stays inside the ordinary
counting-spine field:

```text
1, 2, 3, 4, ...
```

This keeps branch work disciplined before comparing alternate recurrence
frames.

## Candidate Recurrence Frames

```text
raw recurrence:
  1, 1, 1, ...

counting-spine frame:
  1, 2, 3, 4, ...
  next = current + 1

two-memory / Fibonacci frame:
  1, 1, 2, 3, 5, ...
  next = previous + current

doubling frame:
  1, 2, 4, 8, ...
  next = current + current

triangular accumulation frame:
  1, 3, 6, 10, ...
  next = current + next counting-spine increment
```

Some frames can also cast shadows as branches inside another frame. For
example:

```text
doubling as frame:
  next = 2*current

even branch inside the counting spine:
  n -> n+n
```

Those are related, but not identical.

## Phi Language

For now, avoid:

```text
Fibonacci branch
```

Prefer:

```text
Fibonacci recurrence frame
two-memory recurrence frame
```

Likewise:

```text
phi is a projected form of stable two-memory recurrence
```

not:

```text
phi is a projected form of the Fibonacci branch
```

## Future Questions

When this area becomes active, ask:

```text
What licenses a recurrence frame?
How does a frame preserve memory?
What counts as the same frame under projection?
Which branches persist across frames?
Which projected forms belong to frames rather than branches?
```

Until then, branch work should stay focused on repeated relation-lineages
inside the current strict counting-spine field.
