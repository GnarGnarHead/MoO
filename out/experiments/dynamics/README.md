# Dynamics Experiments

This directory is for durable stage-dynamics research artifacts.

Do not treat terminal output as a research result. Save each machine report and
pair it with an interpretation note.

## Required Pairing

Each experiment should produce:

```text
<experiment_id>.pre.md
<experiment_id>.json
<experiment_id>.analysis.md
```

The preregistration file freezes the test before measurement.

The JSON file is the measured report. Written reports should include the exact
command, corpus checksum, tool checksum, timestamp, schema version, and claim
boundary.

The analysis file records:

```text
question
corpus
frozen test
metrics
controls
thresholds
result summary
candidate findings
failed or negative findings
caveats
decision
next question
```

The repository ignore rules keep this directory narrow but track the dynamics
README, preregistration notes, analysis notes, and JSON reports so selected
research artifacts are not only terminal output.

## Naming

Use stable IDs:

```text
dynamics_stage_persistence_u80_v1
dynamics_value_sweep_u80_v1
dynamics_symbolic_recurrence_u80_v1
dynamics_neighborhood_divergence_u80_v1
```

Avoid conclusion-shaped names.

Order-4 projection experiments should also follow
`../../../ORDER4_PROJECTION_PROTOCOL.md` and use names such as:

```text
order4_phi_projection_u80_v1
order4_sqrt2_projection_u80_v1
order4_unit_shell_projection_u80_v1
```

## Claim Discipline

Allowed:

```text
persistent accumulation candidate
parameter-threshold shift candidate
operation-word recurrence
neighborhood divergence under a named metric
```

Disallowed until earned:

```text
MoO is chaotic
MoO has attractors
MoO has bifurcations
MoO has Lyapunov exponents
MoO has strange attractors
```

See `../../../DYNAMICS_TEST_PROTOCOL.md` and
`../../../STAGE_DYNAMICS_LENS_NOTE.md` for the active protocol.
