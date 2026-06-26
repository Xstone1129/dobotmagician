# GMM-DMP Model Switching Design Spec

**Date**: 2026-06-26
**Status**: Approved design

## Motivation

The project currently trains and plays only one algorithm: BGMM-ProMP. For a
clearer experimental story, the code should support a traditional baseline and
let the user switch algorithms from configuration.

The new baseline is GMM+DMP:

- GMM separates demonstrations into placement modes.
- DMP learns a smooth trajectory generator for each mode.

The system should also generate side-by-side comparison plots between
BGMM-ProMP and GMM+DMP.

## Algorithms

### BGMM-ProMP

Existing behavior remains available as `bgmm_promp`.

It learns a Bayesian Gaussian mixture over ProMP weights from all demonstrations.
For `--place-index N`, playback chooses the component trajectory whose placement
section is nearest to the requested pallet slot.

### GMM+DMP

New algorithm name: `gmm_dmp`.

Training flow:

1. Normalize each demo to `n_time_steps`.
2. Extract a placement feature from each demo, using the XY point around the
   gripper opening / place phase.
3. Fit a standard `GaussianMixture` with `n_components`, normally 6 for the 2x3
   pallet grid.
4. Assign demos to clusters.
5. Train one discrete DMP trajectory model per cluster.

DMP scope:

- Learns all trajectory dimensions present in the demo, including `x,y,z,gripper`.
- Uses canonical phase and Gaussian basis functions.
- Reconstructs trajectories through learned forcing terms.
- For the first implementation, target generalization is optional; the primary
  need is a traditional smooth baseline for the current 2x3 experiment.

Playback flow:

1. `--place-index N` maps to a target pallet slot.
2. The model chooses the cluster/DMP whose learned placement point is nearest to
   that slot.
3. The selected DMP generates a trajectory.
4. The existing CoppeliaSim client plays the generated 4D trajectory.

## Unified Model Interface

Both models should expose the same high-level methods:

- `fit(demos)`
- `mean_trajectory()`
- `sample_trajectories(n_samples)`
- `component_trajectories()`
- `trajectory_for_place(place_index, place_positions)`

This lets `learn.py`, `play_coppeliasim.py`, and plotting code avoid algorithm
specific branching.

`BGMMProMP` can keep its internals, but should gain `trajectory_for_place`.

`GMMDMP` should be added as a new class in a separate module.

## Config

`configs/default.yaml` should support algorithm selection:

```yaml
model:
  algorithm: compare  # bgmm_promp | gmm_dmp | compare
  active_algorithm: gmm_dmp
  output_dir: models

bgmm_promp:
  output_path: models/bgmm_promp.joblib
  n_time_steps: 150
  n_basis: 25
  max_components: 8

gmm_dmp:
  output_path: models/gmm_dmp.joblib
  n_time_steps: 150
  n_components: 6
  n_basis: 35
  alpha_z: 25.0
  beta_z: 6.25
  alpha_s: 4.0
```

Rules:

- `algorithm: bgmm_promp` trains only BGMM-ProMP.
- `algorithm: gmm_dmp` trains only GMM+DMP.
- `algorithm: compare` trains both models and writes all comparison plots.
- `active_algorithm` controls which saved model `dobot-play` loads.

## Plot Outputs

When training one algorithm:

- `models/learned_trajectory_bgmm_promp.png`
- or `models/learned_trajectory_gmm_dmp.png`

When `algorithm: compare`:

- `models/learned_trajectory_bgmm_promp.png`
- `models/learned_trajectory_gmm_dmp.png`
- `models/trajectory_comparison.png`

Plot meaning:

- Grey lines: demos.
- Single-model plot: model mean/components/samples.
- Comparison plot: BGMM-ProMP and GMM+DMP selected trajectories drawn on the
  same four dimensions: `x`, `y`, `z`, `gripper`.

## Learn Script

`dobot-learn` should:

1. Load demonstrations once.
2. Build model(s) according to `model.algorithm`.
3. Save each trained model with `joblib`.
4. Write single-model and comparison plots.
5. Print which model files were saved.

If a required gripper column is missing, loading should fail before training.
This already protects against mixing old `t,x,y,z` demos with new
`t,x,y,z,gripper` demos.

## Play Script

`dobot-play` should:

1. Read `model.active_algorithm`.
2. Load that algorithm's saved `.joblib` model.
3. Use `trajectory_for_place(place_index, place_positions)` when
   `--place-index` is provided.
4. Fall back to `mean_trajectory()` or sampling when no place index is provided.
5. Send the trajectory to the existing CoppeliaSim client.

The CoppeliaSim scene and gripper attach/release logic do not need to change for
this feature.

## Validation

Required checks:

1. Unit tests for DMP fit/reconstruction shape.
2. Unit tests that `GMMDMP.trajectory_for_place` returns a 4D trajectory.
3. Existing BGMM-ProMP test still passes.
4. `dobot-learn --config configs/default.yaml` works with `algorithm: compare`.
5. `dobot-play --config configs/default.yaml --place-index 3` works after
   switching `active_algorithm` between `bgmm_promp` and `gmm_dmp`.

## Non-Goals

- No full robot IK integration.
- No hardware execution.
- No advanced DMP goal conditioning in the first pass.
- No browser UI for model switching; config switching is enough.
