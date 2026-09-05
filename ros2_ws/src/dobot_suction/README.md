# Bottom-Contact Suction

The C++ Gazebo Sim 8 plugin starts with suction disabled. Enabling suction
allows a bottom-face contact with the configured target to create a physical
fixed joint using Gazebo's `DetachableJoint` component. Disabling removes the
joint, allowing the object to fall under gravity. There is no teleporting,
distance-based attraction, pressure calculation, or cup deformation.

The robot keeps `base_link` and `link_1` through `link_4`. Only `link_7` is
renamed to `suction_cup_link`; joint names remain unchanged.

## Configuration

The plugin is attached to the robot model. `link_name` selects the cup,
`collision_name` selects its thin bottom collision, and `target_model` selects
the exact allowed object model name (currently `pick_box`). `surface_z` is the
bottom plane in the cup frame, currently -0.006 m. Contacts must be within
1 mm of that plane and have a normal aligned within about 26 degrees of the
cup axis. Side-wall contact does not count as suction contact.

`joint_7` uses `preserveFixedJoint` so Gazebo retains the cup link.
libsdformat renames the two URDF collision elements during conversion; the
Xacro property `cup_contact_gz_name` supplies the resulting bottom collision
name to both the sensor and plugin. Recheck `gz sdf -p` when changing geometry.

## Build and Run

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install --packages-up-to dobot_magician_ros
source install/setup.bash
ros2 launch dobot_magician_ros simulation.launch.py
```

In another sourced terminal, enable, disable, or monitor attachment:

```bash
gz topic -t /dobot_magician/suction/enable -m gz.msgs.Boolean -p 'data: true'
gz topic -t /dobot_magician/suction/enable -m gz.msgs.Boolean -p 'data: false'
gz topic -e -t /dobot_magician/suction_state
```

The state topic publishes `attached` or `detached` as `gz.msgs.StringMsg`
at 10 Hz of simulation time. `detached` includes both disabled suction and
enabled suction waiting for contact. The old `/dobot_magician/attach` and
`/dobot_magician/detach` commands remain supported with `gz.msgs.Empty`.
The trajectory player enables suction above the box, waits for attachment
after descending, and waits for release at the placement waypoint. Controller
actions and the suction confirmation timeout use simulation time. The base is
fixed to the world; the ground top is z=0 and the table top is z=0.002 m.
The initial and return posture is `(0, 0.05, 0.05, 0)` radians. Keeping joints
2 and 3 inside their unchanged position limits avoids the DART servo-at-limit
lockup reproduced in the Docker image. Each motion takes at least four seconds
of simulation time and must satisfy the controller's position tolerance.
See https://github.com/dartsim/dart/issues/1683 for the upstream limitation.

## Physical Test

After sourcing the workspace, from the repository root:

```bash
export GZ_PARTITION=dobot_contact_test
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PWD/ros2_ws/install/dobot_suction/lib:$GZ_SIM_SYSTEM_PLUGIN_PATH"
gz sim -s -r ros2_ws/src/dobot_suction/test/contact.sdf
```

In another terminal with the same partition and a sourced ROS environment:

```bash
export GZ_PARTITION=dobot_contact_test
export PYTHONPATH="/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python:$PYTHONPATH"
python3 ros2_ws/src/dobot_suction/test/verify_contact.py
```

This checks initial-off behavior, no attachment at a distance, bottom-contact
attachment, physical lifting, gravity release, inhibition while disabled,
and re-enabling. It exercises the mechanism independently of the robot path.

With the plugin path set, run the independent side-contact check:

```bash
python3 ros2_ws/src/dobot_suction/test/verify_side_contact.py
```

This starts and stops its own isolated Gazebo server, verifies actual contact
sensor messages from the cup side, and checks that suction does not attach.

## Docker Full-Model Check

Build the current mounted source inside the container, then run the full-model
check. The image includes `ros2controlcli`; an older image needs rebuilding or
`apt-get install ros-jazzy-ros2controlcli` inside the container first.

```bash
docker compose exec -w /workspace/dobotmagician/ros2_ws dobot bash -c '
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-up-to dobot_magician_ros'

docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH="/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python:$PYTHONPATH"
python3 ros2_ws/src/dobot_suction/test/verify_pick_place.py'
```

The check starts its own headless simulation (`gui:=false`) using a separate
Gazebo partition and ROS domain. It waits for both controllers, observes at
least 12 seconds of simulation time after starting the player, and checks
attachment, physical lifting, release, and the final box position. A failed
physical check returns a nonzero exit code even if the player exits normally.
Logs and `summary.json` are written to `/tmp/dobot-pick-place-check` inside
the container, configurable with `--output-dir`.

Reference: https://gazebosim.org/api/sim/8/detachablejoints.html
Gazebo documents contact-related limitations for detachable joints under DART;
physical regression tests are necessary when changing physics versions.
