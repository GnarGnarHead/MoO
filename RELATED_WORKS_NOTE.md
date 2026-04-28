# Related Works for MoO Closure Research

> Status: exploratory literature map.
>
> This note records works and research areas that look relevant to MoO's
> "rational visibility from `1`" program. It is intentionally practical: each
> section says what the work gives MoO and what to test next.

## 1. Rational Trees and Enumerations

MoO's closure rounds are not the only way to enumerate rationals. The closest
classical comparators are the Stern-Brocot and Calkin-Wilf trees.

Relevant works:

- Neil Calkin and Herbert Wilf, "Recounting the Rationals", American
  Mathematical Monthly, 2000.
  - DOI: <https://doi.org/10.1080/00029890.2000.12005205>
  - Author PDF: <https://www.math.clemson.edu/~calkin/Papers/calkin_wilf_recounting_rationals.pdf>
- Roland Backhouse and Joao F. Ferreira, "Recounting the Rationals: Twice!",
  Mathematics of Program Construction, 2008.
  - DOI: <https://doi.org/10.1007/978-3-540-70594-9_6>
- Katherine E. Stange, "An arborist's guide to the rationals", 2014.
  - arXiv-sourced listing: <https://www.researchgate.net/publication/260755674_An_arborist%27s_guide_to_the_rationals>
- "Exact arithmetic on the Stern-Brocot tree", Journal of Discrete Algorithms,
  2007.
  - DOI: <https://doi.org/10.1016/j.jda.2005.03.007>

Why this matters:

- These trees give canonical baseline orderings of rationals.
- They give depth/rank notions independent of MoO's operation closure.
- MoO can ask whether target approximants appear early in MoO closure compared
  with Stern-Brocot, Calkin-Wilf, and Farey orderings.

Immediate test:

- For each best-so-far MoO approximant `p/q`, compute:
  - MoO first-seen round,
  - Stern-Brocot depth,
  - Calkin-Wilf breadth-first rank/depth,
  - denominator height `q`,
  - Farey order.

If MoO consistently finds important approximants at unusually low operation
depth, that is a stronger claim than ordinary rational density.

## 2. Continued Fractions, Best Approximation, and Ford Circles

Continued fractions are the standard theory of rational approximants. They are
the first null model MoO must beat or at least align with.

Relevant works:

- A. Ya. Khinchin, *Continued Fractions*.
  - MAA review: <https://old.maa.org/press/maa-reviews/continued-fractions-0>
- Ian Short, "Ford Circles, Continued Fractions, and Rational Approximation",
  American Mathematical Monthly, 2011.
  - DOI: <https://doi.org/10.4169/amer.math.monthly.118.02.130>
- Andrea Frosini and Lama Tarsissi, "The Characterization of Rational Numbers
  Belonging to a Minimal Path in the Stern-Brocot Tree According to a Second
  Order Balancedness", 2020.
  - PMC: <https://pmc.ncbi.nlm.nih.gov/articles/PMC7247880/>

Why this matters:

- Continued fractions identify the best classical approximants.
- Ford circles give a geometric picture of rational visibility: rationals with
  small denominators occupy large neighborhoods.
- The Frosini/Tarsissi paper is especially relevant to `phi`: it connects
  Fibonacci behavior, Stern-Brocot paths, continued fractions, and a minimality
  notion.

Immediate test:

- Classify each MoO best-so-far approximant as:
  - continued-fraction convergent,
  - semiconvergent/intermediate fraction,
  - non-CF near miss.

If MoO repeatedly rediscovers convergents, it is detecting classical best
approximation through a new construction order. If it finds strong non-CF near
misses, those are worth inspecting as MoO-specific artifacts.

## 3. Integer Complexity, Addition Chains, and Straight-Line Programs

MoO's "from `1`" stance overlaps strongly with integer complexity: how expensive
is it to construct a number from ones using allowed operations?

Relevant works:

- Integer complexity: representing `n` using the fewest ones with addition and
  multiplication.
  - MathWorld overview: <https://mathworld.wolfram.com/IntegerComplexity.html>
- Harry Altman, "Integer complexity: Representing numbers of bounded defect",
  Theoretical Computer Science, 2016.
  - DOI: <https://doi.org/10.1016/j.tcs.2016.09.005>
- Neill M. Clift, "Calculating optimal addition chains", Computing, 2011.
  - DOI: <https://doi.org/10.1007/s00607-010-0118-8>
- Allender, Balaji, Datta, and Pratap, "On the complexity of algebraic numbers,
  and the bit-complexity of straight-line programs", Computability, 2023.
  - DOI: <https://doi.org/10.3233/COM-220407>

Why this matters:

- It gives MoO a rigorous vocabulary for construction cost.
- Addition chains are a clean baseline for `+`-only emergence from `1`.
- Integer complexity is a clean baseline for `+`/`*` emergence from `1`.
- Straight-line programs are a natural formal model for expression DAGs.

Immediate test:

- Define a rational complexity proxy:

```text
moo_cost(p/q) =
    first_seen_round + operation_count + witness_size + denominator_penalty
```

- Compare it to:
  - integer complexity of `p` and `q`,
  - addition-chain lengths for `p` and `q`,
  - Stern-Brocot depth.

This would turn "emergence" into a measurable construction-cost theory.

## 4. Experimental Mathematics and Constant Recognition

MoO's closure-attractor work belongs partly to experimental mathematics: compute,
notice structure, then harden the observation with controls.

Relevant works/tools:

- Jonathan Borwein and David Bailey, *Mathematics by Experiment: Plausible
  Reasoning in the 21st Century*.
  - Publisher page: <https://www.routledge.com/Mathematics-by-Experiment-Plausible-Reasoning-in-the-21st-Century/Borwein-Bailey/p/book/9781568814421>
- David Bailey et al., *Experimental Mathematics in Action*.
  - Publisher page: <https://www.routledge.com/Experimental-Mathematics-in-Action/Bailey-Borwein-Calkin-Luke-Girgensohn-Moll/p/book/9781568812717>
- Ferguson, Bailey, and Arno, "Analysis of PSLQ, an Integer Relation Finding
  Algorithm", Mathematics of Computation, 1999.
  - NASA record: <https://ntrs.nasa.gov/citations/19970009839>
- RIES, "Find Algebraic Equations, Given Their Solution".
  - Project page: <https://www.mrob.com/pub/ries/index.html>
- Inverse Symbolic Calculator / Plouffe's Inverter.
  - OEIS wiki: <https://oeis.org/wiki/Inverse_Symbolic_Calculator>
- OEIS as sequence-recognition infrastructure.
  - OEIS: <https://oeis.org/>
  - Sloane, "A Handbook of Integer Sequences Fifty Years Later", 2023:
    <https://doi.org/10.1007/s00283-023-10266-6>

Why this matters:

- PSLQ and RIES are cautionary: good-looking near misses are easy to produce.
- Experimental mathematics gives a methodology for turning computation into
  conjecture responsibly.
- OEIS-style sequence comparison is useful for MoO best-so-far chains.

Immediate test:

- Export best-so-far numerator and denominator chains for each target:

```text
pi numerators: 2, 3, 25, 22, ...
pi denominators: 1, 1, 8, 7, ...
```

- Search them against OEIS and compare to known continued-fraction sequences.

## 5. BBP, Apéry, and Structured Rational Approximants

There is a large literature where constants are approached or recognized through
structured rational/integer sequences rather than arbitrary decimal expansion.

Relevant works:

- Bailey, Borwein, and Plouffe / BBP-type formulas for constants.
  - MathWorld overview: <https://mathworld.wolfram.com/BBPFormula.html>
  - "The BBP Algorithm for Pi", Bailey, 2006:
    <https://doi.org/10.2172/983322>
- Kristensen and Mathiasen, "BBP-type formulas - An elementary approach",
  Journal of Number Theory, 2023.
  - DOI: <https://doi.org/10.1016/j.jnt.2022.09.001>
- Apéry-style rational approximants to zeta values.
  - Arvesu and Soria-Lorente, "On Infinitely Many Rational Approximants to
    zeta(3)", 2019: <https://doi.org/10.3390/math7121176>

Why this matters:

- Many important constants are "seen" through special rational sequences.
- MoO can search for whether its best-so-far chains satisfy recurrences,
  holonomic relations, or low-complexity generating rules.

Immediate test:

- For each target, collect first-seen best approximants over rounds.
- Attempt to infer:
  - recurrence relations,
  - continued-fraction relation,
  - known OEIS sequences,
  - simple expression grammar.

## 6. Constructive and Computable Analysis

This is the philosophical/mathematical background for treating construction as
part of meaning.

Relevant works:

- Errett Bishop and Douglas Bridges, *Constructive Analysis*.
  - Springer page: <https://link.springer.com/book/10.1007/978-3-642-61667-9>
- Douglas Bridges and Luminiţa Simona Vîţă, *Techniques of Constructive
  Analysis*.
  - Springer page: <https://link.springer.com/book/10.1007/978-0-387-38147-3>
- Stanford Encyclopedia of Philosophy, "Constructive Mathematics".
  - <https://plato.stanford.edu/entries/mathematics-constructive/>

Why this matters:

- It gives disciplined language for avoiding overclaiming.
- It separates "there exists a good rational approximant" from "this process
  constructs that approximant at this stage with this witness."

Immediate test:

- Phrase MoO claims constructively:

```text
At closure round r, under bounds B and operation policy P, target t has witnessed
approximant p/q with error epsilon and witness w.
```

This is much stronger and cleaner than "the rationals are dense."

## 7. Cambridge-Style Arcs, Cusps, and Rational Influence

The Hardy-Littlewood-Ramanujan circle-method tradition is not a direct model of
MoO, but it is a useful analogy for the motif results. In that tradition,
important arithmetic signal can concentrate near rational boundary points,
roots of unity, Farey arcs, and cusp-like sites.

See `CAMBRIDGE_ARC_MOTIFS_NOTE.md` for the focused note.

Relevant works and threads:

- Hardy, Littlewood, and Ramanujan's circle method.
- Rademacher refinements and Farey/Ford-circle geometry.
- Littlewood-style simultaneous approximation questions.
- Minkowski question-mark/Farey dynamics and singular rational measures.
- Ramanujan continued fractions and modular transformations.
- Nahm sums at roots of unity as a more speculative asymptotic tangent.

Why this matters:

- The round-5 motif graph found that `-4/3` behaves as a high-output
  nontrivial hinge, directly feeding both `34/21` and `87/32`.
- That is closer to "rational influence neighborhood" than to "one good
  approximation."
- It suggests treating motif families as finite constructive analogues of
  major/minor arc decompositions.

Immediate test:

- Rank motif families by downstream child count, diversity, and persistence
  across changed bounds.
- Ask whether attractor approximants concentrate inside the strongest motif
  families more often than seeded random targets do.
- Track whether the same rational hinges survive from round to round, or
  whether they are round-5 artifacts.

## Most Useful Next Reading Order

1. Calkin-Wilf, "Recounting the Rationals".
2. Stern-Brocot/Ford circles/continued fractions via Khinchin and Short.
3. Hardy-Littlewood/Ramanujan circle-method background as an analogy for motif
   arcs.
4. Integer complexity and addition chains.
5. Bailey/Borwein experimental mathematics and PSLQ.
6. Apéry/BBP-style constant sequence discovery.
7. Bishop/Bridges constructive analysis for philosophical discipline.

## Research Questions To Carry Forward

1. Do MoO closure rounds discover continued-fraction convergents earlier than
   standard rational enumerations?
2. Are MoO best-so-far chains mostly convergents, semiconvergents, or new
   operation-policy artifacts?
3. Which operations dominate the construction witnesses for good approximants?
4. Do derivation multiplicity and approximation quality correlate?
5. Are `pi`, `e`, `ln2`, `sqrt2`, and `phi` distinguishable from seeded random
   real targets under MoO emergence scores?
6. Does changing operation ordering or bounds preserve the same attractor chains?
7. Can best-so-far chains be recognized as known OEIS sequences or recurrences?
8. Do high-output motif hinges behave like persistent rational influence
   neighborhoods across rounds and bounds?
9. Can MoO define a finite major/minor motif decomposition that predicts where
   attractor approximants will appear?
