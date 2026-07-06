# Simple Gripper Palletizing Design Spec

**Date**: 2026-06-18
**Status**: Implemented

## Motivation

The project originally jumped directly from algorithm validation to a full
Dobot Magician CoppeliaSim scene. That made failures hard to separate: IK,
robot setup, target reading, and BGMM-ProMP learning were all coupled.

This scene isolates the algorithm validation step. It uses a free-moving
end-effector gripper, a small block, one pick point, and a 2x3 pallet area.
There is no full robot arm and no IK.

## CoppeliaSim Scene

`scenes/gripper_palletizing.ttt` contains:

- `/GripperBase`: dummy moved by Cartesian playback.
- Dobot Magician two-finger gripper end effector copied from the user's desktop
  Dobot scene and parented under `/GripperBase`.
- `/GripperBase/.../GripperJawLeftJoint` and `GripperJawRightJoint`: prismatic
  joints driven from the learned gripper signal.
- `/GripperBase/.../GripperTip`: attach frame used when carrying the block.
- `/PalletBlock`: 14 mm block.
- `/PickPoint`: pickup marker.
- `/Place_01` through `/Place_06`: six placement markers in a 2x3 grid.
- `/Table`: small visual reference surface.

The scene does not include the Dobot arm links, IK targets, or full robot
control logic.

## Data Format

Demonstration CSV files use `t,x,y,z,gripper`.

The first three dimensions are the free Cartesian position of `/GripperBase`.
The `gripper` column is continuous:

- `0.0`: open
- `1.0`: closed

`BGMMProMP` treats the gripper value as the fourth trajectory dimension.

## Demo Path Structure

Each trajectory follows:

| Phase | Gripper | Description |
| --- | --- | --- |
| home | 0.0 | Start above the scene |
| pre-pick | 0.0 | Above pick point |
| pick | 0.0 to 1.0 | Close on the block |
| post-pick | 1.0 | Lift block |
| pre-place | 1.0 | Move above selected slot |
| place | 1.0 to 0.0 | Release block |
| post-place | 0.0 | Lift away |
| home | 0.0 | Return home |

Geometry:

- Home: `(0.0, 0.0, 0.15)`
- Pick: `(0.20, -0.16, 0.006)`
- Grid: 2 rows x 3 columns, 40 mm spacing, constant Z
- Block: 14 mm wide, so it fits visually inside the 40 mm slots

## Synthetic Data Generation

`src/dobot_bgmm_promp/scripts/generate_palletizing_demos.py` generates:

- 6 placement positions
- 5 variants per position
- +/-2 mm XY noise for movement waypoints
- Smooth cubic interpolation over phase
- 30 CSV demonstrations in `data/demos`

## Scene Generation

`src/dobot_bgmm_promp/scripts/create_gripper_palletizing_scene.py` opens:

`C:\Users\Administrator\Desktop\dobotmagician.before_ik_backup.ttt`

It extracts the gripper end-effector subtree, removes the rest of the robot,
adds the block and markers, and saves:

`scenes/gripper_palletizing.ttt`

## Playback

`src/dobot_bgmm_promp/coppeliasim_client.py`:

- Moves `/GripperBase` through Cartesian trajectory points.
- Sends `sim.setFloatSignal("gripper", value)`.
- Drives the left/right prismatic gripper joints from the same gripper value.
- Attaches `/PalletBlock` to `GripperTip` after the close threshold.
- Releases `/PalletBlock` at the selected slot after the open threshold.

Pickup/release is deterministic instead of contact-physics based. This keeps
the algorithm validation stable while still making the object visibly move with
the gripper.

`dobot-play --place-index N` selects one of the six placement slots. The script
chooses the learned BGMM component whose placement section is nearest to that
slot.

## Validation Criteria

1. `dobot-create-gripper-scene` produces a scene with no full robot arm.
2. The scene contains the visible Dobot two-finger end effector.
3. `dobot-learn` trains successfully on the generated 4D demonstrations.
4. `dobot-play --place-index 1..6` animates the gripper, carries the block, and
   releases it at the selected slot.

## Non-Goals

- No full Dobot arm in this validation scene.
- No IK solving.
- No hardware interface.
- No unstable contact-physics gripping.
- The full-scene target-coordinate reading issue is not addressed here.
