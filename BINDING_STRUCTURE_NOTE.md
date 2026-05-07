# Binding Structure Study

> Status: first binding-profile pass over the inspected speculative nodes.
>
> This note keeps the speculative thought alive without turning it into a
> runtime claim: external constants do not enter MoO as nodes, but external probes
> can select already-emergent speculative nodes whose native construction context
> can be studied.

## Definition

A binding structure is the MoO-native construction profile around a speculative
node selected by an external probe.

It includes:

- first-seen round;
- first witness;
- operation signature;
- report-level hub and motif neighborhood;
- construction aperture;
- bounded-cap behavior.

Some report fields still use older graph language (`parent`, `child`, `hub`).
In MoO framing, read these as earlier generated construction, recorded result,
and report-level hub.

The external label is not the identity of the node. It is only a test handle.

```text
external probe -> selected speculative node -> MoO-native binding profile
```

This is the disciplined version of the speculative idea:

```text
MoO may bind transcendentals through the rational structures by which they
become approachable, without containing transcendentals as completed values.
```

## Command

The report was generated from saved artifacts only:

```sh
python3 binding_structure_study.py \
  --write out/experiments/binding_structure_r6.json
```

The default inspected probes are:

| external probe | selected speculative node |
| --- | ---: |
| `pi` | `22/7` |
| `e` | `87/32` |
| `ln2` | `52/75` |
| `sqrt2` | `99/70` |
| `phi` | `34/21` |

Sources:

```text
native values:       out/experiments/native_r6_full.json
motif context:       out/experiments/motif_r5.json
aperture context:    out/experiments/construction_aperture_r6.json
threshold context:   out/experiments/witness_threshold_r5.json
```

## Result

Summary:

```text
probe count:                     5
present in native corpus:         5
first-seen round:                 5 / 5 at round 5
first-witness aperture:           5 / 5 at aperture 4
first-witness operations:         3 subtraction, 2 division
```

Cap-3 behavior:

```text
22/7    final value outside |v| <= 3
87/32   escape-and-return under first-witness ancestry
52/75   escape-and-return under first-witness ancestry
99/70   escape-and-return under first-witness ancestry
34/21   escape-and-return under first-witness ancestry
```

The witness-threshold audit adds an important caveat: `34/21` can still survive
under `|v| <= 3` by an alternate witness. So aperture here means saved
first-witness aperture, not globally minimal aperture.

## Motif Split

The five inspected speculative nodes split into three major operation motifs:

| motif | inspected nodes |
| --- | --- |
| `- : mid_q_rational - low_q_rational, both previous round` | `22/7`, `99/70`, `34/21` |
| `/ : mid_q_rational / low_q_rational, both previous round` | `87/32` |
| `/ : mid_q_rational / mid_q_rational, both previous round` | `52/75` |

This is the strongest current binding observation:

```text
The inspected nodes are not just close to external constants.
They enter through a narrow late mid-q motif layer.
```

## Shared Hubs and Ancestors

No single direct report-level hub binds all five inspected nodes.

The strongest direct shared construction remains:

```text
-4/3 -> 34/21, 87/32
```

Common ancestors from the motif report:

| ancestor | inspected descendants |
| ---: | --- |
| `-3` | all five |
| `4` | all five |
| `3` | `22/7`, `99/70`, `52/75` |
| `-4/3` | `34/21`, `87/32` |

This supports a cautious reading:

```text
Binding is not a single universal report-level hub in the current data.
It is a shared construction layer: late round, aperture 4, mid-q motifs,
and repeated ancestry through small grounded scaffolds.
```

## Interpretation

This result does not prove that MoO binds all transcendentals. It gives a
testable meaning for that thought.

Current conservative claim:

```text
MoO can assign a native binding profile to externally probed speculative nodes.
```

Stronger working conjecture:

```text
Constructively meaningful transcendentals may be bound by recurring MoO-native
motif layers, apertures, ancestry, and constraint transitions.
```

The important shift is that the object of study is no longer the approximation
alone. The object is the construction corridor around the approximant.

## Limits

- The sample is tiny and externally selected.
- The report uses saved first witnesses, not every possible derivation.
- Motif context comes from the `n=5` emergence report, while saturated
  derivation counts come from `n=6`.
- The result is a binding profile, not a proof of transcendental identity or
  universality.

## Next Step

Run the same binding-profile machinery on explicitly geometric probes after the
area/product study is defined:

```text
square/area probes -> binding profile
circle probes      -> binding profile
bridge probes      -> binding profile
```

Then compare whether those probe families reuse the same motif layer or split
into distinct construction neighborhoods.
