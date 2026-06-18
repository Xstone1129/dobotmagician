# Simple Gripper Palletizing — Design Spec

**Date**: 2026-06-18
**Status**: Approved design, awaiting implementation

## Motivation

The current project (dobot-magician-bgmm-promp) jumped directly from algorithm
development to full-robot-arm CoppeliaSim simulation, making it impossible to
validate the BGMM-ProMP algorithm independently. The existing demo_01.csv is
invalid — only the timestamp changes, xyz coordinates are constant.

This spec describes a simplified simulation environment: a free-floating gripper
in 3D space, performing palletizing (pick-and-place) trajectories. No robot arm,
no inverse kinematics. This isolation lets us validate the algorithm end-to-end
before re-integrating with the full robot model.

## CoppeliaSim Scene (`scenes/gripper_palletizing.ttt`)

A minimal scene with only these objects:

- `/GripperBase` — dummy, position-controlled via `sim.setObjectPosition`
- `/GripperSignal` — marker, open/close via `sim.setFloatSignal("gripper", 0.0/1.0)`
- `/PickPoint` — fixed pickup location marker (small opaque sphere)
- `/Place_01` through `/Place_06` — six placement markers in a 2x3 grid

No joints, no scripts, no IK elements. The scene is purely a visualization
surface for the Python client to drive.

## Data Format

CSV changes from `t, x, y, z` to `t, x, y, z, gripper`. The `gripper` column
is a continuous signal: 0.0 = open, 1.0 = closed. The algorithm treats it as the
4th dimension — no code changes needed in `BGMMProMP`.

## Demo Path Structure

Each complete palletizing trajectory follows this waypoint sequence:

| Phase      | Gripper | Description                        |
|------------|---------|-----------------------------------|
| home       | 0.0     | Start position, gripper open      |
| pre-pick   | 0.0     | 5cm above pick point              |
| pick       | 0->1    | At pick point, close gripper      |
| post-pick  | 1.0     | Lift 5cm above pick point         |
| pre-place  | 1.0     | Travel 5cm above target place     |
| place      | 1->0    | At place point, open gripper      |
| post-place | 0.0     | Lift 5cm above place point        |
| home       | 0.0     | Return to start                   |

Home position: (0, 0, 0.15)
Pick point: centered relative to grid
Grid: 2 rows x 3 columns, 40 mm spacing in X and Y, constant Z

## Synthetic Data Generation (New Script)

`src/dobot_bgmm_promp/scripts/generate_palletizing_demos.py`

- Defines the grid geometry and waypoint positions
- For each of the 6 place positions, generates 5 variants
- Per-variant: adds +/-2 mm uniform random noise to (x, y) waypoints
- Interpolates via `scipy.interpolate.CubicSpline` over phase [0, 1]
- Outputs to `data/demos/demo_01.csv` through `demo_30.csv`
- Total: 30 demonstration CSV files

## CoppeliaSim Client Changes

`src/dobot_bgmm_promp/coppeliasim_client.py`:

- `play_cartesian_trajectory` detects trajectory dimensionality:
  - 3 columns: existing behaviour (position only)
  - 4 columns: position + gripper signal per step
- On 4D input, calls `sim.setFloatSignal("gripper", g)` alongside
  `sim.setObjectPosition`
- Backward compatible — existing 3D use cases unaffected

## Config Changes

`configs/default.yaml`:

- Add `data.gripper_column: gripper` (optional, default null)
- Update `coppeliasim.target_path` to `/GripperBase`
- Simplify coordinate scale/offset for the new scene

## I/O Changes

`src/dobot_bgmm_promp/io.py`:

- `load_demonstrations` reads the `gripper` column when
  `config["data"].get("gripper_column")` is set
- Demos become 4D arrays [time, 4] when gripper is present

## Validation Criteria

1. `generate_palletizing_demos.py` produces 30 valid CSV files with varying xyz
2. `dobot-learn` trains successfully, plot shows multi-modal trajectories
3. With CoppeliaSim open and scene loaded, `dobot-play` moves the GripperBase
   smoothly and sets gripper signal at correct waypoints

## Non-Goals

- No IK solving
- No full robot arm model
- No joint-level control
- No real hardware interface
- No gripper finger animation (joint drivers deferred to full-robot phase)
- The existing target-reading issue with the full-robot .ttt is not addressed here

## File Changes Summary

| Action | File |
|--------|------|
| New    | `scenes/gripper_palletizing.ttt` |
| New    | `src/dobot_bgmm_promp/scripts/generate_palletizing_demos.py` |
| Edit   | `configs/default.yaml` |
| Edit   | `src/dobot_bgmm_promp/coppeliasim_client.py` |
| Edit   | `src/dobot_bgmm_promp/io.py` |
| Delete | `data/demos/demo_01.csv` (optional, stale data) |
