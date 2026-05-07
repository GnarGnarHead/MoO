# Motif Mass Study

> Status: first low-compute measure pass over saved `n=6` artifacts.
>
> This note records a way to treat MoO as an induced construction measure,
> without claiming that the final saturated value set is the point of the
> project.

## Framing

The useful question is not just:

```text
Which rationals exist after closure?
```

The better question is:

```text
Where does construction mass gather, and which speculative nodes sit inside
those construction corridors?
```

Here "mass" means several separate observables, not one magic score:

- local derivation mass: `derivation_events` for a value;
- operation motif mass: how many values share the same first-witness motif;
- direct report-level hub mass: how many recorded first-witness results
  flow through a value's two recorded input constructions;
- aperture: how far the saved first-witness ancestry must step away from the
  final value region before returning.

Some report fields still use graph-language names such as `parent`, `child`,
and `hub`. In MoO framing, read them as:

```text
parent -> earlier generated construction
child  -> recorded result
hub    -> report-level hub
```

All such constructions and results are generated from `1`; they are not
independent primitive operands.

The script also emits a `triage_mass_score`, but that is only a ranking helper.
It is not a MoO-native theorem.

## Research Hooks

The second literature pass suggests four useful outside analogies:

1. **Cluster algebras and snake graphs.**
   Canakci and Schiffler show continued fractions as quotients of perfect
   matching counts in snake graphs:
   <https://www.cambridge.org/core/journals/compositio-mathematica/article/cluster-algebras-and-continued-fractions/7C3C12E450B8C6110735A0E338396FDD>.
   Their sequel connects snake graphs to convergents, Euclidean division,
   palindromic continued fractions, Markov numbers, and sums of squares:
   <https://www.sciencedirect.com/science/article/pii/S0195669820300020>.
   MoO is not doing snake-graph calculus, but the analogy is useful: finite
   graph/combinatorial structure can carry rational approximation data.

2. **Minkowski question-mark and Stern-Brocot measures.**
   The question-mark function and measure show that rational-tree orderings can
   induce very nonuniform, singular structures:
   <https://www.sciencedirect.com/science/article/pii/S0021904517300746>.
   Fractal work on the question-mark function ties the structure to
   Stern-Brocot intervals and the Farey map:
   <https://doi.org/10.1016/j.jnt.2007.12.010>.
   MoO's motif mass may be a different induced measure on rational construction
   space.

3. **Integer complexity and straight-line programs.**
   Integer complexity studies cost from ones under `+` and `*`, with "defect"
   as a refined cost measure:
   <https://doi.org/10.1016/j.tcs.2016.09.005>.
   Straight-line-program and arithmetic-circuit work gives a formal background
   for construction cost and the role of division:
   <https://doi.org/10.3233/COM-220407> and
   <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CCC.2021.25>.
   MoO witnesses are small arithmetic circuits over `1`, with `/` admitted as a
   native constructor.

4. **Roots of unity and asymptotic boundary behavior.**
   Garoufalidis and Zagier's work on Nahm sums at roots of unity is a distant
   but interesting analogy for rational boundary sites binding asymptotic
   structure:
   <https://link.springer.com/article/10.1007/s11139-020-00266-x>.
   This should stay speculative, but it is relevant to the "rational hinge as
   asymptotic address" idea.

## Command

The report was generated without recomputing closure:

```sh
python3 motif_mass_study.py \
  --pretty \
  --write out/experiments/motif_mass_r6.json
```

Sources:

```text
native report:       out/experiments/native_r6_full.json
aperture report:     out/experiments/construction_aperture_r6.json
motif controls:      out/experiments/motif_persistence_r6.json
binding report:      out/experiments/binding_structure_r6.json
square report:       out/experiments/concept_square_r6.json
triangle report:     out/experiments/concept_triangle_r6.json
```

## Corpus Result

Summary:

```text
values:                    10655
first-witness edges:       10654
operation motifs:             83
direct report-level hubs:     1571
generated pairs:              7226
```

Largest operation motif:

```text
/: mid_q_rational / mid_q_rational, both previous round
recorded results: 2586
derivation mass:  1339957
```

Next largest motifs:

```text
/: mid_q_rational / low_q_rational, both previous round
recorded results: 1071
derivation mass:  1518129

/: low_q_rational / mid_q_rational, both previous round
recorded results: 1041
derivation mass:   974868
```

This is a strong local lesson: under the saturated `n=6` corpus, division-heavy
mid-denominator motifs carry much of the visible construction mass.

Top direct report-level hubs by nontrivial recorded-result count:

```text
-9/5     recorded results 897
-11/5    recorded results 687
-13/5    recorded results 424
-4/3     recorded results 409
-5/3     recorded results 341
```

This preserves the earlier caution about centers. `-4/3` remains an important
older hinge, but `n=6` exposes newer layer-dependent report-level hubs such as
`-9/5`, `-11/5`, and `-13/5`.

## Binding Probes Versus Controls

Binding probes:

```text
22/7, 87/32, 52/75, 99/70, 34/21
```

Comparison against the saved matched-control cohort:

```text
binding median derivation events:        1797
control median derivation events:        1310

binding median motif dependent count:     421
control median motif dependent count:     226

binding major motif rate:                1.00
control major motif rate:                0.60

binding median first-witness aperture:   4
control median first-witness aperture:   4
```

The aperture result is not distinctive: both cohorts live at aperture `4`.
The more interesting signal is that all five binding probes sit inside major
operation motifs, while the matched controls do so only 60% of the time.

This is not proof that MoO binds transcendentals. It is evidence that the
selected speculative nodes are concentrated in high-mass construction corridors.

## Concept Families

Squares family:

```text
values:                         49
median derivation events:     1144
median motif dependent count:  173
major motif rate:             0.43
median aperture:              4
```

Triangle family:

```text
values:                         43
median derivation events:     1329
median motif dependent count:  226
major motif rate:             0.60
median aperture:              4
```

This does not overturn the earlier concept-family note. Squarehood remains the
cleaner native timing family because self-product timing is so direct. The
motif-mass lens says something different: triangle-family values, as a diffuse
cohort, pass through major motifs more often than square-family values in this
bounded corpus.

## Interpretation

The useful result is a measure-like view:

```text
value -> local derivation mass
value -> first-witness operation motif mass
value -> direct report-level hub mass
value -> aperture / escape-return status
value -> cohort membership
```

That gives MoO a low-compute way to ask:

```text
Is this speculative node merely present, or does it sit inside a high-mass
construction corridor?
```

For the current binding probes, the answer is cautiously positive. They are all
round-5, aperture-4 nodes inside major motifs, and the cohort has a higher
median motif-dependent count than the saved matched controls.

## Limits

- Motif mass is based on saved first witnesses, not every possible derivation.
- Construction aperture is saved first-witness aperture, not globally minimal
  aperture.
- The binding-probe cohort is tiny and externally selected.
- The full `n=6` value set is saturated under current bounds, so future work
  should refine measures and controls before increasing `n`.

## Next Questions

1. Do binding probes remain more motif-concentrated under alternate operation
   orderings or bounded replay cells?
2. Can we build a MoO-induced rational measure from motif mass and compare it to
   Stern-Brocot/Minkowski-style measures?
3. Are there native high-mass corridors with no current external interpretation?
4. Do geometric probe subsets, kept as pure analysis-layer cohorts, reuse the
   same high-mass corridors or split into different construction neighborhoods?
