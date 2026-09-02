from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont

from dobot_bgmm_promp.io import load_config, load_demonstrations, project_path
from dobot_bgmm_promp.scripts.learn import ALGORITHM_BUILDERS


@dataclass(frozen=True)
class AlgorithmFigureFact:
    algorithm_id: str
    label: str
    pipeline: tuple[str, ...]
    parameters: tuple[str, ...]
    segment_sizes: tuple[int, ...] = ()
    caveat: str | None = None


@dataclass(frozen=True)
class PlaybackFigureFact:
    active_algorithm: str
    target_path: str
    tip_path: str | None
    left_joint_path: str | None
    right_joint_path: str | None
    block_path: str | None
    pickup_threshold: float
    release_threshold: float
    release_after_phase: float
    release_mode: str
    endpoint_label: str


@dataclass(frozen=True)
class ReportFigureFacts:
    demo_count: int
    normalized_steps: int
    data_columns: tuple[str, ...]
    algorithms: tuple[AlgorithmFigureFact, ...]
    playback: PlaybackFigureFact


@dataclass(frozen=True)
class FileDigest:
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class AssetRecord:
    figure_id: str
    output: FileDigest
    width_px: int | None
    height_px: int | None
    dpi_x: float | None
    dpi_y: float | None
    source_files: tuple[FileDigest, ...]
    source_symbols: tuple[str, ...]


def collect_report_facts(config_path: str | Path = "configs/default.yaml") -> ReportFigureFacts:
    config = load_config(config_path)
    data = config["data"]
    demos = load_demonstrations(
        data["demos_dir"],
        time_column=data["time_column"],
        coordinate_columns=data["coordinate_columns"],
        gripper_column=data.get("gripper_column"),
    )
    steps = {
        int(config[algorithm_id]["params"]["n_time_steps"])
        for algorithm_id in ALGORITHM_BUILDERS
    }
    if len(steps) != 1:
        raise ValueError(f"Expected one shared n_time_steps value, got {sorted(steps)}.")
    normalized_steps = steps.pop()
    algorithms = tuple(
        _algorithm_fact(algorithm_id, label, config[algorithm_id]["params"], normalized_steps)
        for algorithm_id, (label, _) in ALGORITHM_BUILDERS.items()
    )
    sim = config["coppeliasim"]
    columns = [*data["coordinate_columns"]]
    if data.get("gripper_column"):
        columns.append(data["gripper_column"])
    return ReportFigureFacts(
        demo_count=len(demos),
        normalized_steps=normalized_steps,
        data_columns=tuple(columns),
        algorithms=algorithms,
        playback=PlaybackFigureFact(
            active_algorithm=config["model"]["active_algorithm"],
            target_path=sim["target_path"],
            tip_path=sim.get("tip_path"),
            left_joint_path=sim.get("left_gripper_joint_path"),
            right_joint_path=sim.get("right_gripper_joint_path"),
            block_path=sim.get("block_path"),
            pickup_threshold=float(sim["pickup_threshold"]),
            release_threshold=float(sim["release_threshold"]),
            release_after_phase=0.5,
            release_mode=str(sim["release_mode"]),
            endpoint_label="播放至模型轨迹末端",
        ),
    )


def _algorithm_fact(
    algorithm_id: str, label: str, params: dict, normalized_steps: int
) -> AlgorithmFigureFact:
    if algorithm_id == "gmm_gmr_dmp":
        return AlgorithmFigureFact(
            algorithm_id,
            label,
            ("经典 GMM", "GMR", "单 DMP"),
            (f"GMM 分量={params['n_components']}", f"DMP 基函数={params['dmp_basis']}"),
        )
    if algorithm_id == "inc_gmm_gmr_dmp":
        return AlgorithmFigureFact(
            algorithm_id,
            label,
            ("Inc-GMM", "GMR", "单 DMP"),
            (f"inc_lam={params['inc_lam']}", f"DMP 基函数={params['dmp_basis']}"),
        )
    if algorithm_id == "gmm_gmr_segmented_dmp":
        count = int(params["n_segments"])
        quotient, remainder = divmod(normalized_steps, count)
        sizes = tuple(quotient + (index < remainder) for index in range(count))
        return AlgorithmFigureFact(
            algorithm_id,
            label,
            ("经典 GMM", "GMR", "近等长分段 DMP"),
            (
                f"GMM 分量={params['n_components']}",
                f"片段数={count}",
                f"每段 DMP 基函数上限={params['dmp_basis']}",
            ),
            segment_sizes=tuple(int(value) for value in sizes),
        )
    if algorithm_id == "bgmm_gmr_promp":
        return AlgorithmFigureFact(
            algorithm_id,
            label,
            ("BGMM", "GMR", "确定性 ProMP 基函数重构"),
            (
                f"候选 BGMM 分量={params['n_components']}",
                f"ProMP 基函数={params['promp_basis']}",
                f"基函数宽度={params['promp_basis_width']}",
            ),
            caveat="未实现权重概率分布的独立随机采样",
        )
    raise ValueError(f"Unsupported algorithm for report figure: {algorithm_id}")


def render_project_data_flow(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    fig, axis, font = _new_diagram(font_path, height=8.0)
    labels = (
        f"{facts.demo_count} 条 CSV\nt,x,y,z,gripper",
        f"load_demonstrations\n归一化为 {facts.normalized_steps} 点",
        "GMM / Inc-GMM\n/ BGMM",
        "GMR 条件均值轨迹",
        "DMP / 近等长分段 DMP\n/ 确定性 ProMP",
        "joblib / 轨迹图 / 指标表",
        "play_coppeliasim.py\nZeroMQ\n-> CoppeliaSim",
    )
    colors = ("#356E9B", "#356E9B", "#D97920", "#D97920", "#35895A", "#35895A", "#845C9B")
    positions = ((0.45, 5.15), (3.65, 5.15), (6.85, 5.15), (10.05, 5.15),
                 (2.05, 2.75), (5.25, 2.75), (8.45, 2.75))
    width = 2.55
    for index, (label, color, (x, y)) in enumerate(zip(labels, colors, positions)):
        _box(axis, font, x, y, width, 1.35, label, color)
        if index in (1, 2, 3, 5, 6):
            previous_x, previous_y = positions[index - 1]
            _arrow(axis, previous_x + width, previous_y + 0.675, x, y + 0.675)
    _arrow(axis, 11.325, 5.15, 3.325, 4.1)
    _title(axis, font, "项目架构与数据流（节点均映射到当前源码或产物）")
    _note(axis, font, "当前范围：CoppeliaSim 简化自由夹爪单点码垛仿真；无完整机械臂、IK、碰撞检测或 RRT")
    return _save_figure(
        fig,
        "2-1",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_bgmm_promp/io.py",
            "src/dobot_bgmm_promp/scripts/learn.py",
            "src/dobot_bgmm_promp/scripts/play_coppeliasim.py",
        ),
        (
            "dobot_bgmm_promp.io.load_demonstrations",
            "dobot_bgmm_promp.scripts.learn.ALGORITHM_BUILDERS",
            "dobot_bgmm_promp.scripts.play_coppeliasim._model_path",
        ),
    )


def render_playback_state_machine(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    fig, axis, font = _new_diagram(font_path, height=8.0)
    playback = facts.playback
    labels = (
        f"active_algorithm\n{playback.active_algorithm}",
        f"加载 joblib\n{facts.normalized_steps}x4 轨迹",
        f"设置目标位置\n{playback.target_path}",
        "映射 gripper\n设置左右夹爪关节",
        f"gripper >= {playback.pickup_threshold:.2f}\nsetObjectParent 绑定",
        f"phase > {playback.release_after_phase:.1f} 且\ngripper <= {playback.release_threshold:.2f}\n解除绑定",
        playback.endpoint_label,
    )
    colors = ("#356E9B", "#356E9B", "#D97920", "#D97920", "#35895A", "#35895A", "#845C9B")
    positions = ((0.45, 5.05), (3.65, 5.05), (6.85, 5.05), (10.05, 5.05),
                 (2.05, 2.55), (5.25, 2.55), (8.45, 2.55))
    width = 2.55
    for index, (label, color, (x, y)) in enumerate(zip(labels, colors, positions)):
        _box(axis, font, x, y, width, 1.55, label, color)
        if index in (1, 2, 3, 5, 6):
            previous_x, previous_y = positions[index - 1]
            _arrow(axis, previous_x + width, previous_y + 0.775, x, y + 0.775)
    _arrow(axis, 11.325, 5.05, 3.325, 4.1)
    _title(axis, font, "回放控制链路与抓放状态机")
    _note(axis, font, "阈值触发 + setObjectParent；无接触力、距离或碰撞判定；轨迹结束后无额外归位命令")
    return _save_figure(
        fig,
        "2-3",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_bgmm_promp/scripts/play_coppeliasim.py",
            "src/dobot_bgmm_promp/coppeliasim_client.py",
        ),
        (
            "dobot_bgmm_promp.scripts.play_coppeliasim._model_path",
            "dobot_bgmm_promp.coppeliasim_client.CoppeliaDobotClient.play_cartesian_trajectory",
            "dobot_bgmm_promp.coppeliasim_client.CoppeliaDobotClient._attach_block",
            "dobot_bgmm_promp.coppeliasim_client.CoppeliaDobotClient._release_block",
        ),
    )


def render_algorithm_structures(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    fig, axis, font = _new_diagram(font_path, height=8.0)
    axis.text(
        6.5,
        9.35,
        f"共同输入：{facts.demo_count} 条 CSV；模型内归一化为 {facts.normalized_steps} 点",
        ha="center",
        va="center",
        fontsize=16,
        fontproperties=font,
        fontweight="bold",
    )
    colors = ("#356E9B", "#D97920", "#35895A", "#845C9B")
    y_positions = (7.45, 5.35, 3.25, 1.15)
    for algorithm, color, y in zip(facts.algorithms, colors, y_positions):
        x_positions = (0.55, 3.35, 6.15)
        for index, (x, stage) in enumerate(zip(x_positions, algorithm.pipeline)):
            _box(axis, font, x, y, 2.25, 0.95, stage, color)
            if index:
                _arrow(axis, x_positions[index - 1] + 2.25, y + 0.475, x, y + 0.475)
        details = list(algorithm.parameters)
        if algorithm.segment_sizes:
            details.append("实际片段点数=" + "/".join(map(str, algorithm.segment_sizes)))
        if algorithm.caveat:
            details.append(algorithm.caveat)
        axis.text(8.75, y + 0.475, "\n".join(details), ha="left", va="center", fontsize=9.5, fontproperties=font)
    return _save_figure(
        fig,
        "3-1",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_bgmm_promp/gmr_primitives.py",
            "src/dobot_bgmm_promp/scripts/learn.py",
        ),
        (
            "dobot_bgmm_promp.scripts.learn.ALGORITHM_BUILDERS",
            "dobot_bgmm_promp.gmr_primitives.GMMGMRDMP",
            "dobot_bgmm_promp.gmr_primitives.IncGMMGMRDMP",
            "dobot_bgmm_promp.gmr_primitives.GMMGMRSegmentedDMP",
            "dobot_bgmm_promp.gmr_primitives.BGMMGMRProMP",
            "dobot_bgmm_promp.gmr_primitives._segmented_dmp_rollout",
            "dobot_bgmm_promp.gmr_primitives.BGMMGMRProMP._promp_reconstruct",
        ),
    )


def compose_scene_evidence(
    scene_image: str | Path,
    inventory_json: str | Path,
    output_path: str | Path,
    *,
    font_path: str | Path | None = None,
) -> AssetRecord:
    font_file = resolve_cjk_font(font_path)
    scene = project_path(scene_image)
    inventory_path = project_path(inventory_json)
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    objects = [_normalize_inventory_item(item) for item in payload["objects"]]
    missing = [item["expected_alias"] for item in objects if not item["found"]]
    if missing:
        raise ValueError("Missing required scene objects: " + ", ".join(missing))

    with Image.open(scene) as source:
        source_rgb = source.convert("RGB")
        canvas = Image.new("RGB", (3000, 1688), "white")
        left_box = (70, 190, 1940, 1580)
        fitted = source_rgb.copy()
        fitted.thumbnail((left_box[2] - left_box[0], left_box[3] - left_box[1]), Image.Resampling.LANCZOS)
        canvas.paste(fitted, (left_box[0], left_box[1]))
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(font_file), 56)
    heading_font = ImageFont.truetype(str(font_file), 36)
    body_font = ImageFont.truetype(str(font_file), 27)
    small_font = ImageFont.truetype(str(font_file), 24)
    draw.text((70, 58), "CoppeliaSim 简化自由夹爪场景与只读对象证据", font=title_font, fill="#172B3A")
    draw.text((2020, 190), "Remote API 只读对象清单", font=heading_font, fill="#172B3A")
    state = payload.get("simulation_state")
    state_text = f"simulation_state={state}（截图时未运行）" if state == 0 else f"simulation_state={state}"
    draw.text((2020, 250), state_text, font=small_font, fill="#8A3D2A")
    y = 315
    for item in objects:
        position = item.get("world_position")
        pos_text = ""
        if position:
            pos_text = "  [" + ", ".join(f"{value:.3f}" for value in position) + "]"
        draw.text((2020, y), item["expected_alias"] + pos_text, font=body_font, fill="#264A5B")
        path_text = item["configured_path"]
        if len(path_text) > 60:
            path_text = path_text[:57] + "..."
        draw.text((2045, y + 39), path_text, font=small_font, fill="#526873")
        y += 132
    draw.text((70, 1615), "真实窗口截图；对象信息来自只读 getObject/getObjectAlias/getObjectPosition 查询。", font=small_font, fill="#334E5C")
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, dpi=(300, 300))
    return _asset_record(
        "2-2",
        output,
        (_digest(scene), _digest(inventory_path)),
        ("export_coppeliasim_inventory.collect_object_inventory",),
    )


def update_asset_manifest(records: Sequence[AssetRecord], output_path: str | Path) -> None:
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8")).get("assets", [])
    updated_figure_ids = {record.figure_id for record in records}
    retained = [item for item in existing if item["figure_id"] not in updated_figure_ids]
    payload = {"assets": [*retained, *(asdict(record) for record in records)]}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_cjk_font(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        candidate = Path(explicit)
        if candidate.is_file():
            return candidate
        raise RuntimeError(f"CJK font not found: {candidate}")
    for candidate in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    ):
        if candidate.is_file():
            return candidate
    raise RuntimeError("No CJK font found. Pass --font-path or install a CJK font.")


def _new_diagram(
    font_path: str | Path | None,
    *,
    width: float = 13.0,
    height: float = 7.0,
):
    font = FontProperties(fname=str(resolve_cjk_font(font_path)))
    fig, axis = plt.subplots(figsize=(width, height))
    axis.set_xlim(0, 16.1 if width >= 16 else 13.3)
    axis.set_ylim(0, 10)
    axis.axis("off")
    return fig, axis, font


def _box(axis, font, x: float, y: float, width: float, height: float, text: str, color: str) -> None:
    patch = plt.Rectangle((x, y), width, height, facecolor=color, edgecolor="#263846", linewidth=1.2)
    axis.add_patch(patch)
    axis.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color="white",
        fontsize=9.1,
        fontproperties=font,
        fontweight="bold",
        wrap=True,
    )


def _arrow(axis, x1: float, y1: float, x2: float, y2: float) -> None:
    axis.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "#34495E"})


def _title(axis, font, text: str) -> None:
    center = sum(axis.get_xlim()) / 2
    axis.text(center, 7.75, text, ha="center", fontsize=17, fontproperties=font, fontweight="bold")


def _note(axis, font, text: str) -> None:
    center = sum(axis.get_xlim()) / 2
    axis.text(center, 0.95, text, ha="center", fontsize=11.5, fontproperties=font, color="#A33A2B")


def _save_figure(
    fig,
    figure_id: str,
    output_stem: str | Path,
    source_paths: tuple[str, ...],
    source_symbols: tuple[str, ...],
) -> tuple[AssetRecord, AssetRecord]:
    output = project_path(output_stem)
    output.parent.mkdir(parents=True, exist_ok=True)
    png = output.with_suffix(".png")
    svg = output.with_suffix(".svg")
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    sources = tuple(_digest(project_path(path)) for path in source_paths)
    return (
        _asset_record(figure_id, png, sources, source_symbols),
        _asset_record(figure_id, svg, sources, source_symbols),
    )


def _normalize_inventory_item(item: dict) -> dict:
    if "expected_alias" in item:
        return item
    path = str(item["path"])
    return {
        "expected_alias": path.rsplit("/", 1)[-1],
        "configured_path": path,
        "found": True,
        "actual_alias": str(item.get("alias", "")).lstrip("/"),
        "world_position": item.get("position_world"),
    }


def _digest(path: Path) -> FileDigest:
    data = path.read_bytes()
    return FileDigest(str(path), len(data), sha256(data).hexdigest())


def _asset_record(
    figure_id: str,
    path: Path,
    sources: tuple[FileDigest, ...],
    symbols: tuple[str, ...],
) -> AssetRecord:
    width = height = None
    dpi_x = dpi_y = None
    if path.suffix.lower() == ".png":
        with Image.open(path) as image:
            width, height = image.size
            dpi = image.info.get("dpi")
            if dpi:
                dpi_x, dpi_y = float(dpi[0]), float(dpi[1])
    return AssetRecord(figure_id, _digest(path), width, height, dpi_x, dpi_y, sources, symbols)
