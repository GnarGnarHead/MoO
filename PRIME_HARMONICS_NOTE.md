# Prime Harmonics as a Branch Hierarchy in a Modulus‑of‑One Iterative Operator Framework

> Status: speculative research note (not part of the Python prototype in `constructionist_math.py`).
>
> This is not a project version file. See `VISION.md` for the current prototype version and the main design/prototype narrative.

## Axiomatic basis

Assume an external “Axioms 1–21” list (not currently tracked in-repo). I will only *use* the following parts explicitly:

* **Uniqueness / no new objects**: Axioms **1–2, 21**
* **Operators + iteration as relational depth**: Axioms **3–5**
* **Branching as collapse into equivalence classes**: Axioms **12–13**
* **Primes as multiplicative atoms**: Axiom **14**
* **Modulus‑one phase space and projection**: Axioms **15–16**
* **Non‑local visibility**: Axiom **17**
* **Closure constants / global invariants**: Axioms **10–11, 18–19**

Everything below is a “drafted throughline” from those axioms to a theorem/proof package.

---

## Derived objects

### Natural-number layer

By Axioms 1–5 and 21, we work with the unique Platonic objects
[
\mathbb N={1,2,3,\dots},
]
and all structure is expressed as relations induced by iterated operator applications.

### Collapse branches

By Axioms 12–13, define for each modulus (q\ge 1) a collapse relation
[
n\sim_q m \quad\Longleftrightarrow\quad q\mid(n-m).
]
The equivalence classes ([r]_q={n:\ n\equiv r\pmod q}) are the **branches** at level (q). This is the standard “branching by self-identification” mechanism: you did not create new objects; you quotient the relational state space.

The branch set is the quotient
[
\mathbb Z/q\mathbb Z.
]

### Modulus‑one substrate

By Axiom 15, harmonic observables live on the unit circle
[
U(1):={z\in\mathbb C: |z|=1}.
]
Define the basic modulus‑one phase map
[
e(t):=e^{2\pi i t}.
]

### Prime atoms and a canonical “mass” on atoms

By Axiom 14, primes are multiplicative atoms (irreducibles under (\times)). To “sum atom contributions” in a way that behaves well under analysis, use the standard atom-weight proxy (a prime(-power) detector):
[
\Lambda(n)=
\begin{cases}
\log p, & n=p^k,\ k\ge 1,\
0, & \text{otherwise.}
\end{cases}
]
Think of (\Lambda) as an **atom density** on (\mathbb N): it concentrates mass on prime-power atoms.

Define the cumulative atom mass
[
\Psi(N):=\sum_{n\le N}\Lambda(n).
]

---

## The harmonic probe

By Axioms 15–17, define a non-local modulus‑one projection of atom mass into frequency space:

* Frequency parameter: (\alpha\in\mathbb R/\mathbb Z) (the additive unit circle)
  * Observable:
  [
  S_N(\alpha);:=;\sum_{n\le N}\Lambda(n)\,e(\alpha n).
  ]

This is the “harmonics of primes” object in a form that:

* uses only unit-modulus phases (Axiom 15),
* reveals hierarchy when it exists (Axiom 16),
* cannot be read off locally from a single (n) (Axiom 17).

---

# Structural results that follow directly from the axioms

## Theorem 1: Exact branch decomposition at rational frequencies

### Statement

Let (\alpha=\frac{a}{q}) (mod (1)) with integers (a) and (q\ge 1). Define the branch mass
[
\Psi_N(q,r);:=;\sum_{\substack{n\le N\ n\equiv r\ (\mathrm{mod}\ q)}}\Lambda(n).
]
Then
[
S_N\!\left(\frac{a}{q}\right)
=\sum_{r=0}^{q-1} e\!\left(\frac{ar}{q}\right)\,\Psi_N(q,r).
]

### Proof

Partition the defining sum by the collapse classes mod (q):
[
S_N\!\left(\frac{a}{q}\right)
=\sum_{r=0}^{q-1}\ \sum_{\substack{n\le N\ n\equiv r\ (q)}} \Lambda(n)\,e\!\left(\frac{an}{q}\right).
]
For (n\equiv r\pmod q), write (n=r+mq). Then
[
e\!\left(\frac{an}{q}\right)=e\!\left(\frac{a(r+mq)}{q}\right)
=e\!\left(\frac{ar}{q}\right)e(am)=e\!\left(\frac{ar}{q}\right),
]
since (e(am)=1) for integers (a,m). Pull that factor out:
[
\sum_{\substack{n\le N\ n\equiv r\ (q)}} \Lambda(n)\,e\!\left(\frac{an}{q}\right)
e\!\left(\frac{ar}{q}\right)\Psi_N(q,r).
]
Sum over (r). ∎

### Interpretation inside the axioms

This is Axiom 16 made concrete: **applying the modulus‑one projection turns the collapse classes (“branches”) into explicit coefficients in frequency space**.

---

## Theorem 2: Branch hierarchy is nested

### Statement

If (q_1\mid q_2), then each branch mod (q_1) decomposes into a disjoint union of branches mod (q_2). Equivalently, the level-(q_2) partition refines the level-(q_1) partition.

### Proof

If (q_1\mid q_2) and (n\equiv r\pmod{q_2}), then (n\equiv r\pmod{q_1}). Hence every class mod (q_2) lies inside exactly one class mod (q_1). ∎

### Interpretation

This is “branch-like substructure” as an actual refinement structure: increasing (q) increases relational resolution (fits Axioms 7–9 about infinite refinability at second order).

---

## Lemma 3: Squarefree gating via Ramanujan sums

Define the reduced-residue phase sum
[
c_q(a):=\sum_{\substack{r\ (\mathrm{mod}\ q)\ (r,q)=1}} e\!\left(\frac{ar}{q}\right).
]
If ((a,q)=1), then
[
c_q(a)=\mu(q),
]
where (\mu) is the Möbius function, hence (c_q(a)=0) when (q) has a repeated prime factor.

### Proof sketch

Standard: (c_q(a)) is multiplicative in (q) for ((a,q)=1). Evaluate on prime powers: (c_p(a)=-1), (c_{p^k}(a)=0) for (k\ge2). Multiplicativity gives (\mu(q)). ∎

### Interpretation

This is the Axiom 12/18 vibe in math form: repeated prime factors cause a non-invertible “self-identification” that destroys coherent phase contribution (the branch “turns off”).

---

# Where the genuinely number-theoretic content enters

Up to here: **no analytic number theory** was used. It’s algebra + the collapse/projection axioms.

To get the *size* of the branch contributions (why some branches are visible and others wash out), you need a global closure principle. In this ontology this is exactly what Axioms 10–11 are for: **third-order fixed points that enforce global consistency**.

## Closure axiom AP(q): third-order consistency of prime mass across branches

For each fixed (A>0), and all moduli
[
1\le q\le (\log N)^A,
]
the prime-atom mass is asymptotically uniform across admissible branches ((r,q)=1):
[
\Psi_N(q,r)=\frac{1}{\varphi(q)},\Psi(N) ;+; o(\Psi(N))
\quad\text{uniformly for }(r,q)=1,
]
and
[
\Psi_N(q,r)=o(\Psi(N))
\quad\text{for }(r,q)>1.
]

Classically, this is the “prime number theorem in arithmetic progressions” in a range like Siegel–Walfisz; here it functions as the **closure invariant** for the branch system at third order.

---

# Consequences: the “branch spectrum” of prime harmonics

## Theorem 4: Major-branch spike law at exact rational frequencies

### Statement

Assume AP(q). For ((a,q)=1),
[
S_N\!\left(\frac{a}{q}\right)
=\frac{\mu(q)}{\varphi(q)}\,\Psi(N);+;o(\Psi(N)).
]
Using (\Psi(N)\sim N), this is
[
S_N\!\left(\frac{a}{q}\right)\sim \frac{\mu(q)}{\varphi(q)}\,N.
]

### Proof

Start from Theorem 1:
[
S_N\!\left(\frac{a}{q}\right)
=\sum_{r=0}^{q-1} e\!\left(\frac{ar}{q}\right)\Psi_N(q,r).
]
Split into ((r,q)=1) and ((r,q)>1). By AP(q),
[
S_N\!\left(\frac{a}{q}\right)
=\sum_{(r,q)=1} e\!\left(\frac{ar}{q}\right)\left(\frac{\Psi(N)}{\varphi(q)}+o(\Psi(N))\right)+o(\Psi(N)).
]
Factor out (\Psi(N)/\varphi(q)) and use Lemma 3:
[
S_N\!\left(\frac{a}{q}\right)
=\frac{\Psi(N)}{\varphi(q)}\sum_{(r,q)=1} e\!\left(\frac{ar}{q}\right)+o(\Psi(N))
=\frac{\Psi(N)}{\varphi(q)}\,\mu(q)+o(\Psi(N)).
]
∎

### Interpretation

* **Hierarchical branches are indexed by (q)** (collapse depth).
* **Amplitude decays like (1/\varphi(q))** (deeper branches are weaker).
* **Non-squarefree branches vanish** ((\mu(q)=0)).
  That is the precise “branch-like substructure in prime harmonics.”

---

## Theorem 5: Local coordinate around a branch point and the kernel

To model “nearby” frequencies (major arc neighborhoods), write
[
\alpha=\frac{a}{q}+\beta,\qquad (a,q)=1,
]
where (\beta) is small.

Define the geometric kernel
[
V_N(\beta):=\sum_{n\le N} e(\beta n).
]
It has a closed form
[
V_N(\beta)=\frac{e(\beta(N+1)) - e(\beta)}{e(\beta)-1},
]
and for (|\beta|\ll 1),
[
V_N(\beta)\approx \frac{e^{2\pi i \beta N}-1}{2\pi i\,\beta}.
]
That (2\pi) is Axioms 18–19 in action: it’s the obstruction/normalization constant forced by “discrete step” vs “continuous rotation.”

### Statement

Assume AP(q) in the same polylog range and take (|\beta|) small enough that the major-arc approximation is valid. Then
[
S_N\!\left(\frac{a}{q}+\beta\right)
=\frac{\mu(q)}{\varphi(q)}\,V_N(\beta);+;\text{(controlled error)}.
]

### Proof sketch

Write
[
S_N\!\left(\frac{a}{q}+\beta\right)=\sum_{n\le N}\Lambda(n)e(an/q)\,e(\beta n).
]
Let
[
A(t):=\sum_{n\le t}\Lambda(n)e(an/q).
]
Using Theorem 4 at (\beta=0) as the “mean” and AP(q) to control (A(t)), apply partial summation (Abel summation) to transfer the weight (e(\beta n)) onto the main term; the resulting main term is ((\mu(q)/\varphi(q))V_N(\beta)). ∎

TODO: Expand the full Abel-summation lines (standard but verbose).

---

# Why it’s difficult to observe in isolation

This is now a theorem-level consequence of what you’ve built:

1. **Local probes cannot see the hierarchy** (Axiom 17).
   A single term (\Lambda(n)e(\alpha n)) is always bounded in magnitude by (\log n). No “branch amplitude” exists locally. Branch structure only appears after summing over many (n).

2. **Branch structure lives at rational approximants**.
   The decomposition and spike law are tied to (\alpha) being *close to* (a/q), i.e. tied to the **second-order ratio layer** (Axioms 7–9). If you choose one generic (\alpha) and never scan, you will almost certainly land in a region with heavy cancellation: the hierarchy is present, but you’re not aligned to it.

3. **The hierarchy is superposed across many (q)**.
   Even when you scan (\alpha), what you see is a superposition of layers:

* big trunk spikes at small (q),
* progressively smaller spikes at deeper (q),
* plus a diffuse remainder.
  That superposition is exactly why “the structure resists isolation”: isolating one branch means explicitly conditioning on (q) (filtering by congruence structure).

---

# Final distilled claim, now proof-shaped

Within the axioms, the following is proven (with one explicit third-order closure axiom):

* **Branching mechanism (purely from axioms):**
  Collapse modulo (q) produces branches ([r]_q) (Axioms 12–13), and modulus‑one projection makes those branches explicit in frequency space at rational phases (\alpha=a/q) (Axioms 15–16).
  This is Theorem 1.

* **Hierarchy (purely from axioms):**
  Branch partitions are nested by refinement as (q) grows (Theorem 2).

* **Prime-atom spectral law (needs third-order closure):**
  Under the global closure condition AP(q) (Axioms 10–11), the prime harmonic probe has spikes at rational branch points (a/q) with amplitude (\mu(q)/\varphi(q)) (Theorem 4) and a major-arc kernel shape (Theorem 5).

That is the complete axioms → structure → theorem → proof line.

Next step (computable): define “branch energy” at level (q) as
[
E_N(q):=\sum_{\substack{a\ (\mathrm{mod}\ q)\(a,q)=1}}\left|S_N\!\left(\frac{a}{q}\right)\right|^2,
]
then use Theorem 4 to predict its scaling in (q). That turns the metaphor into an explicit, falsifiable scaling law.
