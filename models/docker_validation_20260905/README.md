# Docker Validation: 2026-09-05

Container: `dobot-magician`, image: `dobot-magician:jazzy`.
Runtime: ROS 2 Jazzy, Gazebo Sim 8.11.0.
Both ROS packages were rebuilt from the mounted workspace source inside Docker.

## Results

- Independent suction contact/lift/release/re-enable test: PASS.
  Box center rose from 0.0200 m to 0.1450 m, then fell after disabling suction.
- Independent physical side-contact rejection test: PASS.
- Docker URDF-to-SDF cup, fixed joint, and contact collision references: PASS.
- Complete corrected robot pick/place workflow: PASS (`fixed/summary.json`).
  Both controllers were active. State sequence: detached, attached, detached.
  Observed motion: 33.195 simulation seconds, 62.38 wall seconds including startup.
  Physical box lift: 0.063962 m.
  Final box center: (0.0799644, 0.1599235, 0.01199998) m.
  Final table XY error: 0.00008436 m; final height stable over 20 samples.

The original complete-flow failure is retained in this directory's root logs
and `summary.json`. Corrected-run logs and raw pose/state/controller samples
are under `fixed/`.

## Corrections

The base is fixed to the world. The ground surface is z=0, and the box and
table heights now agree with the commanded suction-cup frame heights.
Vertical-tool IK constrains joint_4 = joint_3 - joint_2. The player executes
controller actions and confirms attachment/release using simulation time.
Joint-error tolerances prevent false success when an axis is stalled.

DART SERVO joints 2 and 3 were stuck at their initial lower limits. This was
reproduced even with the ROS controller removed. Initial and return values of
0.05 rad avoid the boundary while preserving the original joint limits.
The engine itself was not patched or upgraded.

## Reproduce

From the repository root with the container running:

```bash
docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH="/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python:$PYTHONPATH"
python3 ros2_ws/src/dobot_suction/test/verify_pick_place.py'
```

The validator uses an isolated Gazebo partition and ROS domain and cleans up
its simulation processes. Full instructions are in `ros2_ws/src/dobot_suction/README.md`.
