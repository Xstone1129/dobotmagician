# Dobot Magician 吸盘轨迹学习与 ROS 2 仿真

本项目使用 Dobot Magician 模型研究吸取、抬升、转运和放置轨迹，通过 GMM/GMR 学习示教数据，再由 DMP 或 ProMP 生成轨迹，并提供 ROS 2 Jazzy + Gazebo 仿真。

## 1. 完整流程与当前状态

```text
已有示教 / 生成示教 CSV
          |
          v
选择配置与算法 -> 参数搜索（可选）-> 将选定参数写回 YAML
          |
          v
训练四个算法 -> 保存模型、阶段图、最终轨迹图和指标
          |
          v
检查拟合误差、起终点、低位停留与逆解可达性
          |
          v
启动 Gazebo -> 检查控制器 -> 分段回放学习轨迹并确认吸附、释放
          |
          v
独立物理验证 -> 检查物体抬升、落点和最终吸盘状态
```

**离线拟合、机械臂运动和物体成功抓放是三个不同的验证层级。**

使用已有数据复现结果时，按第 3 节准备环境、第 5.2 节训练、第 6 节查看结果即可；无需重新生成示教或重新搜索参数。仿真与回放按第 7、8 节进行。

- 示教已按当前场景重新生成，从 pick 中心接触位开始、在 place 中心接触位结束，两个接触位默认下压 0.5 mm；8 条示教共 1440 个点全部通过竖直吸盘逆解检查。
- 四个模型已在 Docker 回放环境中重新训练，沿用 [吸盘配置](configs/suction_arm.yaml) 中上一轮调优参数。本轮训练 XYZ RMSE 约为 0.686–0.912 mm，属于合成示教拟合误差，不是实际机械臂跟踪误差。
- 播放器检查全部选中轨迹点的逆解，任一点失败都会拒绝执行；默认全程保持吸盘竖直。逆解检查本身不发送运动指令，不包含碰撞及抓放验证。
- 学习轨迹播放器使用 `FollowJointTrajectory` 动作接口，按模型中的吸盘启停信号分段执行；吸附确认后才抬升，释放确认后才继续，等待控制器完成后自动退出。
- Docker 完整测试集 44 项通过，其中生成器 17 项、播放器 16 项。历史调参报告对应旧示教，其指标不能直接作为本轮结果。
- 四个算法的下压抓放均已通过 Gazebo 物理验证：确认吸附、抬升、释放，最终方块稳定停在台面上。当前场景、默认 0.5 mm 下压及 `speed:=0.5` 的实测结果如下；这不是实机测试。

| 算法 | 方块抬升 | 距 place 中心误差 | 物理验证 |
|---|---:|---:|---|
| GMM + GMR + DMP | 64.44 mm | 0.740 mm | PASS |
| Inc-GMM + GMR + DMP | 64.36 mm | 0.745 mm | PASS |
| GMM + GMR + 分段 DMP | 64.21 mm | 0.719 mm | PASS |
| BGMM + GMR + ProMP | 65.04 mm | 0.660 mm | PASS |

第 8.4 节分别提供预设路径和指定学习算法的验证命令；预设路径通过不能代替学习算法通过。

## 2. 算法与目录

| 配置中的算法名称 | 算法流程 |
|---|---|
| `gmm_gmr_dmp` | 经典 EM-GMM → GMR → DMP |
| `inc_gmm_gmr_dmp` | 增量 GMM → GMR → DMP |
| `gmm_gmr_segmented_dmp` | 经典 EM-GMM → GMR → 分段 DMP |
| `bgmm_gmr_promp` | 贝叶斯 GMM → GMR → ProMP |

```text
configs/suction_arm.yaml                 当前任务配置与四算法参数
data/demos_suction_turn/                  8 条示教 CSV
src/dobot_algorithms/                     学习、调参、绘图和回放代码
ros2_ws/src/dobot_magician_ros/            URDF、网格、场景、控制器与启动文件
ros2_ws/src/dobot_suction/                 C++ 吸盘插件和物理验证脚本
models/suction_arm/
  *.joblib                               四份训练模型
  plots/trajectories/                     最终轨迹及四算法对比图
  plots/gmm/                             GMM 拟合图及对比图
  plots/gmr/                             GMR 回归图及对比图
  metrics/                               训练指标、阶段指标及调参报告
tests/                                   算法回归测试
reports/                                 论文文档
reports/figures/                          论文插图
magician3D/                               原始 CAD 和模型参考资料
```

旧夹爪任务及 `configs/default.yaml` 已移除。训练和直接调用播放器时，默认配置都是 `configs/suction_arm.yaml`。

## 3. 准备环境

### 3.1 两个运行位置

| 位置 | 项目路径 | 用途 |
|---|---|---|
| 宿主机 | `/home/yuling/xstone/dobotmagician` | 编辑代码、生成示教、本地训练、查看结果 |
| Docker 容器 | `/workspace/dobotmagician` | ROS 2 Jazzy、Gazebo、容器内训练与回放 |

下面的命令均标明运行位置。新的宿主机终端先进入项目根目录：

```bash
cd /home/yuling/xstone/dobotmagician
```

### 3.2 宿主机 Python 环境

已有 `.venv` 可以继续使用。首次部署、环境缺失或依赖需要更新时再执行：

```bash
cd /home/yuling/xstone/dobotmagician
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
```

要求 Python >= 3.10；算法依赖由 `pyproject.toml` 管理。后面的本地命令显式使用 `.venv/bin/python`，无需先激活虚拟环境。单纯生成示教、训练和绘图不需要启动 ROS。

Ubuntu 提示缺少 venv/ensurepip 时，先执行 `sudo apt install python3-venv`，再创建环境。

### 3.3 Docker 仿真环境

需要 Docker Engine、Compose V2，以及可供容器使用的图形显示环境。当前 `docker-compose.yml` 针对这台主机的 NVIDIA 设备和 X11 显示配置，包含 `/dev/nvidia*` 映射；没有这些设备的电脑需要先调整 Compose，单独设置 `gui:=false` 不会取消设备映射。

在宿主机执行：

```bash
cd /home/yuling/xstone/dobotmagician
docker --version
docker compose version
nvidia-smi
xhost +local:docker
docker compose build
docker compose up -d
docker compose ps
```

容器服务名为 `dobot`，容器名为 `dobot-magician`。镜像构建时安装 ROS/Gazebo 依赖、Python 算法包，并编译 `ros2_ws`。

**修改文件后的更新方式：**

| 宿主机修改内容 | 容器如何看到更新 |
|---|---|
| `models/` | 实时挂载，训练模型和图片直接共享 |
| `data/` | 实时只读挂载；在宿主机生成示教，容器负责读取 |
| `ros2_ws/src/` | 实时挂载；C++、安装清单或新增文件修改后，在容器内重新编译 |
| `src/dobot_algorithms/`、`configs/`、`pyproject.toml`、`tests/`、Dockerfile | 未挂载，重新执行 `docker compose build` 和 `docker compose up -d` |

只执行 `docker compose restart` 不会把新算法代码和配置复制进旧镜像。

## 4. 准备示教数据

项目已提供示教，可直接进入训练步骤。需要重新生成时，在宿主机执行：

```bash
cd /home/yuling/xstone/dobotmagician
PYTHONPATH=src:ros2_ws/src/dobot_magician_ros \
  .venv/bin/python -m dobot_algorithms.scripts.generate_suction_demos \
  --output-dir data/demos_suction_turn \
  --count 8 \
  --seed 57 \
  --noise-std 0.0015 \
  --press-depth 0.0005
```

脚本读取 `ros2_ws/src/dobot_magician_ros/worlds/suction_turn.sdf` 中 `pick_box` 和 `place_table` 的碰撞盒中心与尺寸，以及 URDF 吸盘插件的接触面偏移。轨迹从 pick 中心接触位开始，经吸取、抬升、绕基座转运、下降、释放，在 place 中心接触位结束，不再包含往返 HOME 的段落。

当前场景在默认下压量下，起点为 `(0.18, -0.15, 0.0255)` m，终点为 `(0.08, 0.16, 0.0270)` m。XY 对齐两个区域的中心；Z 是 `suction_cup_link` 原点高度，在方块、台面高度和吸盘底面到原点的 6 mm 偏移基础上，减去 0.5 mm 下压量，不是方块内部的几何中心高度。

`--press-depth` 表示接触时给定的位置下压量，默认 `0.0005` m，允许范围为 `0` 到 `0.001` m（0 到 1 mm）。当前 Gazebo 吸盘仍是刚体，没有添加弹簧或真实伸缩结构；这个参数用于让接触指令略低于表面，不能当作已实现柔顺控制。修改下压量后，必须重新生成示教并按第 5 节重新训练四个模型，已有模型不会自动跟随生成器参数变化。

**脚本先生成全部示教，并逐点检查竖直吸盘逆解；全部通过后才替换输出目录中的 `demo_*.csv`。** 检查失败会报告示教编号与点索引，保留原有 CSV。这里仅加载纯 Python 运动学模块，不需要启动 ROS。保留现有数据时不要重复执行；实验数据可通过 `--output-dir` 指定其他目录，并同步修改配置中的 `data.demos_dir`。

每份 CSV 是一条示教：

```csv
t,x,y,z,gripper
0.00,0.18,-0.15,0.0255,0
```

- `t`：时间，单位秒。
- `x,y,z`：世界坐标系下的吸盘原点坐标，单位米；当前机器人基座固定在世界原点。
- `gripper`：吸盘命令示教值，0 表示关闭，1 表示开启；生成器插值后可以出现中间值，播放器按 `gripper >= 0.5` 判定开启。
- `--noise-std 0.0015`：空中转运段 XYZ 高斯噪声的最大标准差为 1.5 mm，段落两端平滑衰减为零；接触停留、竖直接近和起终点不加噪声。
- `--lift-z 0.09`：吸盘原点的转运高度，单位米。修改高度后仍须通过全部逆解检查。
- `--world`、`--urdf`：指定场景和吸盘描述文件；当前仅支持轴对齐的方块与放置台。运动学检查使用项目现有的 URDF 对应逆解，修改机械臂关节几何时需同步更新逆解。
- 当前生成器默认每条 180 个点、采样间隔 0.04 秒，坐标插值使用 PCHIP。

所有示教必须包含相同的坐标列。加载器按 `t` 排序，训练再按样本索引归一化时间；对于不等间隔采集的数据，需要先重采样，不能只填写真实时间戳后直接假定时间间隔会被保留。

## 5. 调参与训练

### 5.1 选择训练方式

`configs/suction_arm.yaml` 中：

```yaml
model:
  algorithm: compare
  active_algorithm: gmm_gmr_dmp
```

- `algorithm: compare`：一次训练四个算法并生成对比图。
- `algorithm` 改成单个算法名称：只训练该算法。
- `active_algorithm`：直接运行学习轨迹播放器且不传 `--algorithm` 时选择的算法；不会改变训练算法选择。

### 5.2 使用当前参数训练全部算法

在宿主机执行：

```bash
cd /home/yuling/xstone/dobotmagician
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m dobot_algorithms.scripts.train_models \
  --config configs/suction_arm.yaml --algorithm compare
```

只训练一个算法：

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m dobot_algorithms.scripts.train_models \
  --config configs/suction_arm.yaml --algorithm bgmm_gmr_promp
```

训练会覆盖对应的 `.joblib`、图片和训练指标文件。单算法训练也会覆盖公共指标表，但不会刷新四算法对比图；需要完整且一致的对比结果时，最后再运行一次 `--algorithm compare`。

### 5.3 重新搜索参数（可选）

当前配置已调优，普通使用不需要每次搜索。改变示教任务后，可在宿主机执行：

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m dobot_algorithms.scripts.tune_models \
  --config configs/suction_arm.yaml \
  --output /tmp/dobot-tuning.json
```

当前 8 条数据的搜索流程为：前 6 条做三折验证，每折 4 条训练、2 条验证；最后 2 条不参与选参，留作独立检查。换成更多示教时，脚本仍保留排序后的最后 2 条作为留出集。

搜索按毫米制的位置、低位区域和起终点误差评分，吸盘信号误差单独设门槛，避免混合不同单位。脚本只输出候选和结果，**不会自动修改 YAML，也不会替换现有模型**。

查看结果后，将各算法 `best.params` 写入 YAML 对应的 `params`，再运行全部算法训练。既有 [调参报告](models/suction_arm/metrics/hyperparameter_tuning.md) 记录的是上次实验，不会随参数搜索自动刷新。

### 5.4 准备在 Docker 中回放的模型

`joblib` 模型受 Python 包路径和 scikit-learn 等依赖版本影响。宿主机与容器的依赖版本可能不同；为了保持训练和回放环境一致，可以在已更新并启动的容器中训练：

```bash
docker compose exec -T \
  -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 \
  -w /workspace/dobotmagician dobot \
  python3 -m dobot_algorithms.scripts.train_models \
  --config configs/suction_arm.yaml --algorithm compare
```

输出仍写入宿主机挂载的 `models/`，会覆盖同名模型和图表。依赖版本变化后应重新检查指标，不应假定与之前的调参报告完全相同。

## 6. 查看图像和指标

| 内容 | 位置 |
|---|---|
| 四算法最终轨迹对比 | [trajectory_comparison.png](models/suction_arm/plots/trajectories/trajectory_comparison.png) |
| 各算法最终轨迹 | [plots/trajectories/](models/suction_arm/plots/trajectories/) |
| GMM 拟合及分量对比 | [plots/gmm/](models/suction_arm/plots/gmm/) |
| GMR 回归及对比 | [plots/gmr/](models/suction_arm/plots/gmr/) |
| 最终轨迹指标 | [algorithm_metrics.md](models/suction_arm/metrics/algorithm_metrics.md) |
| GMR 与运动基元阶段指标 | [stage_metrics.md](models/suction_arm/metrics/stage_metrics.md) |
| 调参参数与验证结果 | [hyperparameter_tuning.md](models/suction_arm/metrics/hyperparameter_tuning.md) |
| 论文插图 | [reports/figures/](reports/figures/) |

宿主机可直接打开对比图：

```bash
xdg-open models/suction_arm/plots/trajectories/trajectory_comparison.png
```

单算法图中的灰线是示教，红线是模型输出；对比图中的不同颜色对应不同算法。横轴是归一化时间，位置纵轴单位为米。

检查时依次关注：XYZ 误差、起终点、下降到吸取高度后的停留、抬升过程、吸盘启停时刻。XYZ RMSE 越小越好，Pearson 越接近 1 越好；相关性高不能替代绝对位置精度。CSV 中保留的旧 `RMSE Mean` 是混合单位统计，不应用于选参。

## 7. 编译并启动仿真

以下命令从宿主机执行，要求第 3 节的容器已启动。

### 7.1 更新 ROS 工作空间

修改 ROS 包后，在容器内编译：

```bash
docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
colcon --log-base ros2_ws/log build --symlink-install --base-paths ros2_ws/src \
  --build-base ros2_ws/build --install-base ros2_ws/install'
```

始终使用 `ros2_ws/install/setup.bash`。仓库根目录的 `build/`、`install/` 是旧构建目录，不是当前推荐的运行入口。

### 7.2 只查看模型

```bash
docker compose exec dobot ros2 launch dobot_magician_ros view_model.launch.py
```

该命令打开 RViz 和关节调节窗口，不运行 Gazebo 物理仿真。检查完后按 `Ctrl+C` 退出，再进入下一种运行方式。

### 7.3 启动 Gazebo 与控制器

终端 A：

```bash
docker compose exec dobot ros2 launch dobot_magician_ros simulation.launch.py
```

无图形界面时使用：

```bash
docker compose exec dobot ros2 launch dobot_magician_ros simulation.launch.py gui:=false
```

终端 B 检查状态：

```bash
docker compose exec dobot ros2 control list_controllers
docker compose exec dobot ros2 topic list
docker compose exec dobot ros2 topic echo /joint_states --once
```

预期 `arm_controller` 和 `joint_state_broadcaster` 都为 `active`。本项目使用 `suction_cup_link` 作为吸盘工具参考，竖直工具逆解满足 `joint_4 = joint_3 - joint_2`。

## 8. 回放与抓放验证

### 8.1 回放学习得到的轨迹

在未启动其他 Gazebo 实例时，使用合并启动文件：

```bash
docker compose exec -w /workspace/dobotmagician dobot \
  ros2 launch dobot_magician_ros algorithm_playback.launch.py \
  algorithm:=gmm_gmr_segmented_dmp \
  config:=configs/suction_arm.yaml \
  speed:=0.5
```

它会同时启动仿真和学习轨迹播放器，**不要再同时运行第 7.3 节的仿真启动命令**。切换算法时先结束当前启动进程，再替换 `algorithm:=` 的值启动。

| 启动参数 | 默认值 | 含义 |
|---|---|---|
| `algorithm` | `gmm_gmr_dmp` | 四个算法之一；合并启动文件有固定默认值 |
| `config` | `configs/suction_arm.yaml` | 读取哪个任务配置 |
| `speed` | `1.0` | 时间缩放，0.5 更慢；当前实现最低按 0.1 处理 |
| `sample_period` | `0.08` | 缩放前相邻样本的播放时间间隔，单位秒 |
| `lead_in` | `2.0` | 初始姿态的过渡/保持时间，单位秒 |
| `max_joint_speed` | `0.8` | 关节速度上限，单位 rad/s；`speed < 1` 时再同比降低，上限不得超过 URDF 的 3.15 rad/s |
| `max_waypoints` | `0` | 0 表示不限制，正数指定均匀下采样点数；额外保留吸盘信号切换点，实际点数可能超过此值 |
| `startup_delay` | `8.0` | 开始动作前等待时间，单位秒；还需等控制器和吸盘状态就绪 |
| `vertical_tail_fraction` | `1.0` | 默认全程保持吸盘竖直，避免自由姿态逆解在相邻点间跳变 |
| `gui` | `true` | 是否启动 Gazebo 图形界面 |

如果第 7.3 节的仿真已经在运行，则在另一个终端单独启动播放器：

```bash
docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
python3 -m dobot_algorithms.scripts.play_algorithm \
  --config configs/suction_arm.yaml \
  --algorithm bgmm_gmr_promp --speed 0.5'
```

直接调用时省略 `--algorithm` 才会读取配置中的 `active_algorithm`；合并启动文件省略 `algorithm:=` 时默认是 `gmm_gmr_dmp`。

播放器根据相邻点的最大关节位移自动延长时间，包括初始 HOME 到 pick 起点的过渡；`sample_period / speed` 是相邻原始样本的最短播放间隔。以 `speed:=0.5` 为例，关节速度上限为 0.4 rad/s，HOME 到 pick 约需 5.66 秒。`lead_in / speed` 是进入初始姿态的时间，与这段起点过渡时间分开计算。日志中的 `motion duration` 是分段运动时间之和，吸附、释放确认还会增加等待时间。

播放器从学习模型读取 XYZ 和 `gripper`，在 `gripper >= 0.5` 的状态切换点结束当前动作段。到达吸取位后发送开启命令，等到命令之后新收到的 `attached` 状态才执行抬升和转运；到达释放位后关闭吸盘，等新收到的 `detached` 状态才继续。每段均检查控制器动作结果。轨迹使用仿真时钟执行，同时用实际经过时间监测仿真或反馈停滞；状态等待超时或动作失败会停止并以非零退出码结束。

单独中断播放器时，程序先取消当前动作并确认控制器停止，再关闭吸盘；Ctrl+C 返回中断码 130。如果无法确认控制器已停止，会报错并保留吸附，避免机械臂继续运动时先松开物体。

`State tolerances failed` / `Holding position due to state tolerance violation` 表示实际关节未及时跟上参考轨迹，与 IK 无解不同。日志中的 `joint 0` 对应 `joint_1`；当前路径误差阈值为 0.35 rad。应检查轨迹时间、姿态连续性和实际反馈，不应通过放宽阈值掩盖过快的指令。

播放器出现 `Refusing incomplete ... unreachable points` 时，会拒绝发送不完整轨迹，应先处理示教坐标、逆解或竖直工具约束问题。出现 `Playing ...` 表示开始执行；`Learned trajectory complete; suction released.` 表示所有动作段及吸盘状态确认完成，播放器随即自动退出。Gazebo 启动进程仍需手动结束；物体实际抬升和最终落点由第 8.4 节的物理验证检查。

### 8.2 运行预设抓放程序

先按第 7.3 节启动仿真，再在第二个终端执行：

```bash
docker compose exec dobot ros2 run dobot_magician_ros trajectory_player
```

这个程序执行预设的抓放路径，等待控制器动作结果，并检查吸盘吸附、释放状态；它不读取四个学习模型。运行时不要同时启动学习轨迹播放器，避免向同一个机械臂发送多份目标。

### 8.3 检查吸盘状态

在已经运行的仿真中，从宿主机执行：

```bash
docker compose exec dobot gz topic -e -t /dobot_magician/suction_state
```

需要手动测试启停时：

```bash
docker compose exec dobot gz topic -t /dobot_magician/suction/enable \
  -m gz.msgs.Boolean -p 'data: true'
docker compose exec dobot gz topic -t /dobot_magician/suction/enable \
  -m gz.msgs.Boolean -p 'data: false'
```

插件通过吸盘底面与指定物体的接触建立物理连接；只发送开启命令并不代表已经吸住。状态为 `attached` 表示已连接，`detached` 也可能表示吸盘开启但尚未接触物体。

### 8.4 自动验证物理抓放

以下命令均在宿主机执行，脚本会启动独立、无图形界面的仿真。运行前结束其他 Gazebo 实例，并逐个验证算法，避免并行实例影响时钟和状态桥接。先验证预设抓放路径：

```bash
docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH="/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python:$PYTHONPATH"
python3 ros2_ws/src/dobot_suction/test/verify_pick_place.py'
```

验证当前训练得到的分段 DMP 抓放：

```bash
docker compose exec -w /workspace/dobotmagician dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
export PYTHONPATH="/opt/ros/jazzy/opt/gz_msgs_vendor/lib/python:$PYTHONPATH"
python3 ros2_ws/src/dobot_suction/test/verify_pick_place.py \
  --algorithm gmm_gmr_segmented_dmp --speed 0.5'
```

`--algorithm` 可替换为第 2 节的任一算法名称；省略时保持原来的预设路径验证。脚本等待控制器，检查物体是否吸附、抬升、释放并落到目标位置。查看输出中的 `PASS` / `FAIL`、失败原因和进程退出码。上面的 ROS 环境和 Gazebo protobuf 的 `PYTHONPATH` 设置适用于两种验证方式。

日志与 `summary.json` 默认写在容器内 `/tmp/dobot-pick-place-check/`，不会堆积到项目的 `models/`。`summary.json` 中的 `algorithm` 标识实际验证的算法或 `preset`；需要保留多次结果时用 `--output-dir` 指定不同目录。独立底面接触、侧面拒绝等更细的测试见 [吸盘插件说明](ros2_ws/src/dobot_suction/README.md)。

## 9. 测试与结束运行

宿主机算法测试：

```bash
cd /home/yuling/xstone/dobotmagician
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -m pytest -q -p no:cacheprovider
```

该测试检查算法、图像生成和示教的离线逆解，不连接真实机械臂，也不代表 Gazebo 抓取验证通过。禁用插件自动加载是为了避免系统 ROS `launch_testing` 插件与本地 pytest 版本冲突。

播放器测试需要 ROS 消息类型，在没有 ROS 的宿主机 `.venv` 中会跳过。在容器中运行完整测试集：

```bash
docker compose exec -T -w /workspace/dobotmagician \
  -e PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 -e PYTHONDONTWRITEBYTECODE=1 \
  -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 dobot bash -c '
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
python3 -m pytest -q -p no:cacheprovider tests'
```

结束运行时，先在启动仿真、播放器和状态监听的终端按 `Ctrl+C`。随后在宿主机执行：

```bash
docker compose down
xhost -local:docker
```

这会停止并移除 Compose 容器。宿主机挂载的模型和数据保留；容器内未挂载的临时日志不会随容器保留。

## 10. 本机直接运行 ROS 2（可选）

不使用 Docker 时，需要宿主机已经安装 Ubuntu 24.04 对应的 ROS 2 Jazzy、Gazebo 相关 ROS 包和 colcon。ROS/Gazebo 依赖名称可参考 [Dockerfile](Dockerfile) 中的安装清单。

使用独立终端，不要激活本地 `.venv` 来运行 ROS 节点。安装系统侧算法依赖并构建：

```bash
cd /home/yuling/xstone/dobotmagician
source /opt/ros/jazzy/setup.bash
sudo apt install python3-numpy python3-scipy python3-sklearn \
  python3-matplotlib python3-yaml python3-joblib
colcon --log-base ros2_ws/log build --symlink-install --base-paths ros2_ws/src \
  --build-base ros2_ws/build --install-base ros2_ws/install
source ros2_ws/install/setup.bash
export PYTHONPATH="$PWD/src:$PYTHONPATH"
ros2 launch dobot_magician_ros simulation.launch.py
```

第二个终端同样加载 ROS 和 `ros2_ws/install/setup.bash` 后，再运行预设播放器，或设置同样的 `PYTHONPATH` 后运行学习轨迹播放器。模型加载遇到依赖版本警告时，应在实际回放使用的 Python 环境中重新训练。

## 11. 常见问题

| 现象 | 检查方法 |
|---|---|
| 容器缺少 NVIDIA 设备或无法启动 | 核对 `nvidia-smi` 和 Compose 的设备映射；当前配置不能原样套到无 NVIDIA 的机器 |
| Gazebo / RViz 无法显示 | 核对宿主机显示会话、`DISPLAY`、X11 挂载和 `xhost`；只需无界面仿真时使用 `gui:=false` |
| ROS 找不到包、插件或新 launch | 加载 `ros2_ws/install/setup.bash`；在当前运行环境重新编译，检查控制台报错 |
| 修改了算法或 YAML，容器仍用旧版本 | 这两部分未挂载，重建镜像并更新容器；重启旧容器不够 |
| 找不到旧模型模块或出现 scikit-learn 版本警告 | 使用当前 `suction_arm.yaml`，在回放环境中重新训练，避免加载历史模型 |
| 对比图和当前单算法结果不一致 | 最近可能只训练了一个算法；重新运行四算法 `--algorithm compare` |
| 拟合图很好，但播放器拒绝执行 | 检查 `Refusing incomplete` 日志、坐标系、逆解与竖直工具约束，不能靠提高拟合精度解决 |
| 学习轨迹回放没有吸起物体 | 检查是否收到命令后的 `attached` 状态、接触位置和 `gripper` 切换点；修改 `--press-depth` 后重新生成、训练，并按第 8.4 节验证对应算法 |
| 下压后关节跟踪误差增大 | 检查刚体接触与下压量，允许范围为 0 到 1 mm；当前模型没有真实伸缩或弹簧机构 |
| DDS 通信异常 | 仿真启动文件会清除 `FASTRTPS_DEFAULT_PROFILES_FILE`；其他独立终端也需使用一致的 ROS 环境和域 |
