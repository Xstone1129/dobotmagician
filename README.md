# Dobot Magician GMM-GMR Movement Primitives

This project learns palletizing demonstrations and replays generated trajectories
in ROS 2/Gazebo. The main experiments are organized around the required
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
src/dobot_algorithms/    Python algorithm package (GMM/GMR/primitives)
ros2_ws/src/             ROS 2/Gazebo package (URDF, meshes, RViz)
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
python -m dobot_algorithms.scripts.learn --config configs/default.yaml
```

Use `model.algorithm` in `configs/default.yaml` to train only one algorithm.

## Algorithms

Set `model.algorithm` in the configuration to train one algorithm or `compare`
to evaluate all four GMM/GMR movement-primitive variants. Results are written to
the configured `models/` paths.

Every training run now saves the fitted mixture and the GMR conditional mean
before the final DMP/ProMP output in `models/.../intermediate/`.

## ROS 2 + Gazebo

On Ubuntu 24.04 with ROS 2 Jazzy, build the new simulation package:

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch dobot_magician_ros simulation.launch.py
```

In a second terminal, send a slow reachable circular-turn demo:

```bash
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 run dobot_magician_ros trajectory_player
```

如果你在仓库根目录看到 `install/setup.bash`，它只是旧构建目录的快捷入口；请使用上面命令加载 `ros2_ws/install/setup.bash`。

The tool frame is explicitly `suction_tip_link`; `joint_4` is commanded as
`-(joint_2 + joint_3)` so the suction tool stays approximately vertical.
