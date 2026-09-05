# Suction Algorithm Tuning - 2026-09-05

## Method

- Unchanged input: eight CSVs under `data/demos_suction_turn`, sorted by filename.
- Selection: three folds on `demo_01.csv` through `demo_06.csv` (four train, two validate).
- Held-out evaluation: train on the first six, evaluate once on `demo_07.csv` and `demo_08.csv`.
- Delivery models: retrain selected parameters on all eight demonstrations, at 180 time steps.
- Search: 10 classic GMM/DMP, 10 incremental GMM/DMP, 18 segmented DMP, and 16 BGMM/ProMP candidates.
- Reject non-converged mixtures or any fold with gripper RMSE above 0.12.
- Minimize `XYZ RMSE + 0.5 * low-height XYZ RMSE + 0.25 * maximum endpoint error`, all in mm.
- Low-height samples are validation demonstration points with Z <= 50 mm.
- XYZ RMSE pools all three position coordinates, samples and demonstrations. Gripper RMSE is dimensionless and is evaluated separately.

These demonstrations are noisy variants of one synthetic task, not different real-world tasks. Results do not establish generalization to different pick/place locations.

## Selected Parameters

The complete active parameters are in `configs/suction_arm.yaml`.

| Algorithm | Parameters |
|---|---|
| GMM+GMR+DMP | 40 components; 140 DMP bases; alpha_z=50, beta_z=12.5, alpha_s=1 |
| Inc-GMM+GMR+DMP | lambda=0.05; 140 DMP bases; alpha_z=50, beta_z=12.5, alpha_s=1 |
| GMM+GMR+Segmented DMP | 40 components; 4 segments; up to 50 bases per segment; alpha_z=50, beta_z=12.5, alpha_s=1 |
| BGMM+GMR+ProMP | 32 components; mean precision=0.001; covariance prior=data covariance * 0.01; 50 bases; width=0.02; constrained endpoints |

Batch mixtures use two initializations, at most 1000 iterations, and random seed 7. Ridge and covariance regularization remain 1e-6. Segment basis counts are capped at segment length minus one.

## Validation

| Algorithm | CV XYZ RMSE (mm) | Held-out XYZ RMSE (mm) | Held-out Z RMSE (mm) | Held-out low-height XYZ RMSE (mm) | Held-out max endpoint error (mm) | Held-out gripper RMSE |
|---|---:|---:|---:|---:|---:|---:|
| GMM+GMR+DMP | 4.047 | 4.147 | 4.663 | 5.864 | 1.432 | 0.01573 |
| Inc-GMM+GMR+DMP | 3.917 | 4.071 | 4.313 | 5.673 | 2.314 | 0.01573 |
| GMM+GMR+Segmented DMP | 3.092 | 3.212 | 1.891 | 3.570 | 2.699 | 0.00201 |
| BGMM+GMR+ProMP | 3.950 | 3.875 | 3.818 | 4.914 | <0.001 | 0.02101 |

## Saved Model Comparison

The following compares the previous saved models and the delivered models against all eight demonstrations. It is a reconstruction comparison, not held-out validation. The old DMP implementation bypassed integration for closed dimensions, so this comparison includes implementation corrections as well as parameter changes.

| Algorithm | Previous XYZ RMSE (mm) | New XYZ RMSE (mm) | Previous Z RMSE (mm) | New Z RMSE (mm) | Previous gripper RMSE | New gripper RMSE |
|---|---:|---:|---:|---:|---:|---:|
| GMM+GMR+DMP | 11.987 | 3.781 | 16.802 | 4.623 | 0.04805 | 0.01570 |
| Inc-GMM+GMR+DMP | 4.250 | 3.696 | 4.737 | 4.394 | 0.00514 | 0.01575 |
| GMM+GMR+Segmented DMP | 16.831 | 2.784 | 18.332 | 1.799 | 0.05502 | 0.00202 |
| BGMM+GMR+ProMP | 19.242 | 4.149 | 29.613 | 4.674 | 0.11058 | 0.02251 |

Incremental DMP's gripper error increased when genuine integration replaced the old direct-reference bypass. Its position error improved; not every metric improved.

## Implementation Corrections

- GMR responsibilities now include the Gaussian covariance determinant and use log-space normalization.
- Closed DMPs integrate the learned forcing term using SciPy RK45. Initial derivatives and forcing targets use the same reference spline. No direct-reference bypass or forced tail replacement is used.
- Adjacent segmented DMPs share a reference boundary sample. Finite-horizon integration still leaves small endpoint errors; exact velocity continuity is not imposed.
- ProMP reconstruction enforces the demonstrated start and goal through equality constraints on basis weights.
- Suction metric files are grouped under `models/suction_arm/metrics/`.

## Runtime Limits

All delivered batch mixtures converged and all saved models reload successfully. The plots and metrics describe offline learning only. With the current `inverse_kinematics` and the player's default final-20-percent vertical-tool rule, accepted samples were 53/180 (classic), 52/180 (incremental), 51/180 (segmented), and 51/180 (ProMP). Original demonstration points at the home position (0.10, 0, 0.20) and a mid-arc point also fail this solver. This check does not prove geometric impossibility: solver initialization, coordinate frames, and demonstration/model compatibility require investigation. No simulation pick/place or hardware movement was run for this tuning task.

## Reproduce

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  -m dobot_algorithms.scripts.tune_models --config configs/suction_arm.yaml \
  --output /tmp/dobot-tuning.json
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  -m dobot_algorithms.scripts.train_models --config configs/suction_arm.yaml
```

The search reports candidates without applying them. Training uses the parameters already in the YAML. The model selection remains `gmm_gmr_dmp`; no runtime algorithm switch was performed.
