# Dobot Magician GMM-GMR Movement Primitives

This project learns palletizing demonstrations and replays generated trajectories
in CoppeliaSim. The main experiments are organized around the required
three-stage pipeline:

```text
GMM variant -> GMR trajectory regression -> movement primitive execution model
```

## Algorithms

- `gmm_gmr_dmp`: classic EM-GMM + GMR + DMP.
- `inc_gmm_gmr_dmp`: incremental GMM + GMR + DMP.
- `gmm_gmr_segmented_dmp`: classic EM-GMM + GMR + segmented DMP.
- `bgmm_gmr_promp`: Bayesian GMM + GMR + ProMP reconstruction.

## Project Layout

```text
configs/                 Runtime configuration
data/demos_single_place/ CSV demonstrations for the single place point
models/                  Saved models and plots
src/dobot_bgmm_promp/    Python package
tests/                   Regression tests
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Demonstration CSV Format

Put demonstrations in `data/demos_single_place/`. Each CSV should contain one trajectory with
columns like:

```csv
t,x,y,z,gripper
0.00,0.20,0.00,0.08,0
0.02,0.21,0.01,0.08,1
```

All demo files for one training run must use the same coordinate columns.

## Learn Models

The default config trains all four algorithms and prints Pearson/RMSE metrics:

```powershell
python -m dobot_bgmm_promp.scripts.learn --config configs/default.yaml
```

Use `model.algorithm` in `configs/default.yaml` to train only one algorithm.

## Replay in CoppeliaSim

Set `model.active_algorithm` in `configs/default.yaml` to one of:

```text
gmm_gmr_dmp
inc_gmm_gmr_dmp
gmm_gmr_segmented_dmp
bgmm_gmr_promp
```

Then replay a learned trajectory to the configured place point:

```powershell
python -m dobot_bgmm_promp.scripts.play_coppeliasim --config configs/default.yaml
```

The default config contains one place point. `--place-index 1` is still accepted
for compatibility, but no other place index is configured.
