# Prime-Euclid Shell Alignment Protocol

> Status: active geometry / number-theory bridge protocol.
>
> This note extends circle-square alignment by adding rational normalization,
> primitive integer triples, Euclid parameters, and prime-factor scrutiny. It
> does not claim that primes explain MoO structure until graph timing survives
> explicit controls.

## Purpose

The circle-square probe starts from exact rational shells:

```text
x*x + y*y = r*r
```

Prime-factor logic is integer logic. Therefore a rational shell must be
cleared before prime claims are attached.

For each candidate, the protocol records:

```text
rational shell
-> common-denominator integerized triple
-> primitive integer triple
-> Euclid parameters m,n when recoverable
-> prime factor profiles for the triple and parameters
-> strict graph timing and witness fields for those objects
```

## Rational Normalization

Given rational shell components:

```text
x = a / dx
y = b / dy
r = c / dr
```

compute:

```text
common_denominator = lcm(dx, dy, dr)
integerized_x = x * common_denominator
integerized_y = y * common_denominator
integerized_r = r * common_denominator
```

Then reduce by:

```text
gcd_integerized_xyz = gcd(integerized_x, integerized_y, integerized_r)
```

The primitive integer triple is:

```text
primitive_x = integerized_x / gcd_integerized_xyz
primitive_y = integerized_y / gcd_integerized_xyz
primitive_r = integerized_r / gcd_integerized_xyz
```

This prevents denominator artifacts from masquerading as prime structure.

## Euclid Parameter Recovery

For a nondegenerate primitive Pythagorean triple, recover:

```text
primitive_x, primitive_y, primitive_r

m*m - n*n
2*m*n
m*m + n*n
```

with:

```text
gcd(m, n) = 1
m and n of opposite parity
```

The graph report should ask whether MoO sees the generative grammar, not merely
the completed identity:

```text
m node present
n node present
m*m node present
n*n node present
m*m - n*n witness present
2*m*n witness present
m*m + n*n witness present
```

## Prime Fields

For each primitive shell, record factor payloads for:

```text
integerized_x, integerized_y, integerized_r
primitive_x, primitive_y, primitive_r
m, n
m*m, n*n
m*m - n*n
2*m*n
m*m + n*n
```

Fields include:

```text
prime factors
exponents
prime mod 4 classes
squarefree kernel
odd 3 mod 4 prime exponents
Fermat two-square obstruction flag
```

Guardrail:

```text
Do not use r*r as the primary obstruction test.
```

At the completed norm level, `r*r` has even prime exponents by construction.
The useful inspection target is `r`, the primitive triple, and the recovered
Euclid parameters.

## Controls

Prime and Euclid features are not evidence by themselves. They must be compared
against size and construction controls:

```text
same max component height
same common denominator
same primitive radius size
same first_stage bucket
same denominator baseline
same Euclid m,n size
same graph-invariant vocabulary
```

The first-pass report may expose the fields without fully satisfying every
control. A stronger result must state which controls were used.

## Allowed Claim

Safe current claim:

```text
MoO can inspect whether prime and Euclid-parameter structure organizes rational
shell-square alignment timing in strict construction graphs.
```

Candidate claim after a saved strict report:

```text
This corpus contains rational shell-square candidates whose primitive integer
triples have recovered Euclid parameters and named graph timing / witness
fields for the associated generative components.
```

## Disallowed Claims

Do not claim:

```text
Primes are the missing piece.
Prime factors explain MoO geometry.
MoO proves Fermat's two-square theorem.
MoO squares the circle.
MoO defines the Euclidean circle.
MoO constructs pi.
```

## First Experiment

Initial target:

```text
strict U80 smoke corpus
nondegenerate rational shells
complete shell-square families
primitive triple normalization
Euclid parameter recovery
prime-factor payloads
graph-node presence for m,n,m*m,n*n and generated legs/radius
strict generator-witness audit
```

The expected first signal is classical: small shell candidates reduce to the
`3,4,5` primitive family. The MoO question is whether the graph sees the
Euclid/prime grammar early and coherently enough to explain branch alignment
beyond ordinary size and denominator baselines.
