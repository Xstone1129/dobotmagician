# Evidence-Based Report Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an evidence-backed revision of the retained Dobot Magician Word report and Markdown handoff guide, adding reproducible system, simulator, and playback evidence without overstating the current simulation-only implementation.

**Architecture:** Keep repository facts, generated report figures, DOCX package edits, and render QA as separate layers. Build source-driven diagrams and read-only CoppeliaSim evidence as permanent assets; edit an unpacked working copy of the retained DOCX with direct OOXML patches; verify structure automatically; then use isolated Word/WPS export workers plus Poppler full-page rendering. Until the user supplies 6-8 confirmed video frames, publish only the explicitly named `待回放关键帧` working copy and never insert a blank figure 5-1.

**Tech Stack:** Python 3.10+, NumPy, Matplotlib, Pillow, PyYAML, pytest, Ruff, CoppeliaSim ZeroMQ Remote API, OOXML, Microsoft Word COM, WPS COM, Windows PowerShell 5.1, Poppler, Orca Computer Use.

---

## Global Constraints

- The retained baseline is `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`; do not overwrite it during this plan.
- The pre-frame output is `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx`.
- The final output without `待回放关键帧` is created only after the user supplies and confirms 6-8 real playback frames and the second full QA pass succeeds.
- Do not read evidence from or reuse `.codex_tmp_source*`, `reports/images_to_insert.xml`, `reports/insert_images.py`, `reports/paper_new.zip`, or `reports/paper_temp.zip`.
- Do not reuse images from the rejected fake supplemental report or generate photorealistic simulator/playback images.
- State the implemented scope as a simplified CoppeliaSim single-place palletizing simulation with a free-moving gripper. Do not claim complete-arm kinematics, IK, RRT, collision avoidance, contact grasping, hardware execution, or real-robot validation.
- Treat `models/algorithm_metrics.csv` as the numerical result source. Segmented DMP has the best Pearson mean (`0.9934`); Inc-GMM+DMP has the best RMSE mean (`0.0123`).
- Describe segmented DMP as four near-equal `numpy.array_split` segments with sizes `38/38/37/37`, not four exactly equal segments.
- Describe playback as running to the model trajectory endpoint. There is no independent return-to-HOME command.
- The current configured `active_algorithm` is `bgmm_gmr_promp`; the user's video model must be recorded from the user's confirmation in `frames.json`, not inferred from configuration or filenames.
- Preserve cover pages, assessment tables, headers, footers, themes, numbering, styles, section properties, `image1.png/rId8`, and fallback cover asset `image2.png/rId9`.
- Use `PYTHONUTF8=1` and the bundled Python for DOCX/PDF tooling. Use the project Python environment for repository code, Matplotlib, Pillow, pytest, and Ruff.
- Run `git status --short` before each commit and stage exact paths only. Ignore the user's existing untracked files listed above.

## File Structure

**Create**

- `src/dobot_algorithms/report_figures.py` - source-of-truth dataclasses, fact collection, report diagram rendering, scene composition, playback collage validation, and asset manifest writing.
- `src/dobot_algorithms/scripts/generate_report_figures.py` - `diagrams`, `scene`, and `playback` CLI subcommands.
- `src/dobot_algorithms/scripts/export_coppeliasim_inventory.py` - read-only Remote API object inventory exporter.
- `tests/test_report_figures.py` - figure fact, rendering, manifest, scene, and playback validation tests.
- `tests/test_export_coppeliasim_inventory.py` - read-only inventory exporter tests.
- `reports/evidence/coppeliasim/scene-overview.png` - real CoppeliaSim scene screenshot captured through Orca Computer Use.
- `reports/evidence/coppeliasim/object-inventory.json` - read-only Remote API evidence for required objects.
- `reports/figures/figure-2-1-project-data-flow.png` and `.svg` - project architecture/data flow.
- `reports/figures/figure-2-2-coppeliasim-scene-and-objects.png` - real scene plus clearly labeled Remote API inventory.
- `reports/figures/figure-2-3-playback-state-machine.png` and `.svg` - playback/control state machine.
- `reports/figures/figure-3-1-algorithm-structures.png` and `.svg` - four-algorithm structure comparison.
- `reports/figures/manifest.json` - input/output hashes, dimensions, DPI, and source symbols.
- `scripts/report_qa/OfficeWorker.ps1` - one isolated Word/WPS COM operation.
- `scripts/report_qa/Invoke-ReportQa.ps1` - timeout-safe orchestration, fallback export, and Poppler rendering.
- `scripts/report_qa/verify_render.py` - PDF/PNG structural assertions.
- `tests/report_qa_timeout_safety.ps1` - exact-process termination and fallback safety tests.
- `.codex_tmp/evidence-report-revision/verify_report_docx.py` - task-local read-only DOCX verifier.
- `.codex_tmp/evidence-report-revision/unpacked/` - unpacked working DOCX package.
- `.codex_tmp/evidence-report-qa/<timestamp>/` - each isolated QA run.

**Modify**

- `pyproject.toml` - add direct Pillow dependency and report-figure CLI entries.
- `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md` - current metrics, parameters, evidence-generation procedure, paper comparison, and precise scope.
- `.codex_tmp/evidence-report-revision/unpacked/word/document.xml` - direct text, table, and image insertion patches.
- `.codex_tmp/evidence-report-revision/unpacked/word/_rels/document.xml.rels` - `rId23`-`rId26` image relationships; `rId27` only after frames arrive.
- `.codex_tmp/evidence-report-revision/unpacked/word/settings.xml` - enable automatic field updates.

**Read Only**

- `docs/superpowers/specs/2026-07-17-evidence-based-report-revision-design.md`
- `configs/default.yaml`
- `data/demos_single_place/*.csv`
- `src/dobot_algorithms/gmr_primitives.py`
- `src/dobot_algorithms/coppeliasim_client.py`
- `src/dobot_algorithms/scripts/learn.py`
- `src/dobot_algorithms/scripts/play_coppeliasim.py`
- `src/dobot_algorithms/scripts/generate_palletizing_demos.py`
- `src/dobot_algorithms/scripts/create_gripper_palletizing_scene.py`
- `models/algorithm_metrics.csv`, `models/algorithm_metrics.md`, `models/*.png`, `models/*.joblib`
- `scenes/gripper_palletizing.ttt`
- `C:/Users/Administrator/OneDrive/文档/科教/刘暾东 等 - 2024 - 基于分段动态运动基元的机械臂轨迹学习与避障方法.pdf`
- `C:/Users/Administrator/OneDrive/文档/科教/基于分段动态运动基元的Dobot Magician机械臂轨迹学习与避障研究.pptx`

---

### Task 1: Freeze Baseline Evidence and Protection Hashes

**Files:**

- Create: `.codex_tmp/evidence-report-revision/baseline.sha256`
- Create: `.codex_tmp/evidence-report-revision/repository-evidence.json`
- Create: `.codex_tmp/evidence-report-revision/paper-evidence.md`
- Create: `.codex_tmp/evidence-report-revision/ppt-claim-audit.md`
- Read: all read-only sources listed above

- [ ] **Step 1: Record the baseline document and current worktree**

Run:

```powershell
$tmp = '.codex_tmp/evidence-report-revision'
$src = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Get-FileHash -Algorithm SHA256 $src |
  Format-List | Out-File "$tmp/baseline.sha256" -Encoding utf8
git status --short | Out-File "$tmp/git-status-before.txt" -Encoding utf8
```

Expected: `baseline.sha256` contains one SHA-256 for the retained DOCX; the status log records but does not modify the user's current untracked files.

- [ ] **Step 2: Prove the algorithm baseline still has five tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest tests/test_bgmm_promp.py -q -p no:cacheprovider
```

Expected: exactly `5 passed`.

- [ ] **Step 3: Verify demonstrations, model outputs, parameters, and metrics**

Run:

```powershell
@'
from pathlib import Path
import csv
import json
import joblib
import numpy as np
import yaml

config = yaml.safe_load(Path("configs/default.yaml").read_text(encoding="utf-8"))
demos = sorted(Path("data/demos_single_place").glob("*.csv"))
metrics = list(csv.DictReader(Path("models/algorithm_metrics.csv").open(encoding="utf-8-sig")))
models = {}
for path in sorted(Path("models").glob("*.joblib")):
    trajectory = joblib.load(path).mean_trajectory()
    models[path.name] = {
        "shape": list(trajectory.shape),
        "finite": bool(np.isfinite(trajectory).all()),
        "gripper_min": float(trajectory[:, 3].min()),
        "gripper_max": float(trajectory[:, 3].max()),
    }

payload = {
    "demo_count": len(demos),
    "demo_rows": {path.name: sum(1 for _ in path.open(encoding="utf-8")) - 1 for path in demos},
    "parameters": {
        key: config[key]["params"]
        for key in (
            "gmm_gmr_dmp",
            "inc_gmm_gmr_dmp",
            "gmm_gmr_segmented_dmp",
            "bgmm_gmr_promp",
        )
    },
    "active_algorithm": config["model"]["active_algorithm"],
    "metrics": metrics,
    "models": models,
}
Path(".codex_tmp/evidence-report-revision/repository-evidence.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

assert payload["demo_count"] == 8
assert set(payload["demo_rows"].values()) == {150}
assert payload["active_algorithm"] == "bgmm_gmr_promp"
assert all(item["shape"] == [150, 4] and item["finite"] for item in models.values())
assert all(0.0 <= item["gripper_min"] <= item["gripper_max"] <= 1.0 for item in models.values())
assert [int(len(part)) for part in np.array_split(np.empty((150, 4)), 4)] == [38, 38, 37, 37]
'@ | python -
```

Expected: `repository-evidence.json` is created and all assertions pass. It records DMP bases `15`, `50`, `35`, ProMP bases `25`, width `0.08`, and the four current metric rows. This command loads models read-only; it does not retrain or rewrite them.

- [ ] **Step 4: Extract paper and PPT claims from the original files, not `.codex_tmp_source*`**

Run:

```powershell
$env:PYTHONUTF8 = '1'
$py = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$paper = 'C:/Users/Administrator/OneDrive/文档/科教/刘暾东 等 - 2024 - 基于分段动态运动基元的机械臂轨迹学习与避障方法.pdf'
$ppt = 'C:/Users/Administrator/OneDrive/文档/科教/基于分段动态运动基元的Dobot Magician机械臂轨迹学习与避障研究.pptx'
@'
from pathlib import Path
import re
import sys
import pdfplumber
from pptx import Presentation

paper_path, ppt_path = map(Path, sys.argv[1:])
with pdfplumber.open(paper_path) as pdf:
    paper_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

paper_checks = {
    "MAF": "MAF" in paper_text,
    "DTW": "DTW" in paper_text,
    "RRT": "RRT" in paper_text,
    "collision": "碰撞" in paper_text,
    "six_axis": "六轴机械臂" in paper_text,
}
assert all(paper_checks.values())
Path(".codex_tmp/evidence-report-revision/paper-evidence.md").write_text(
    "# Paper evidence\n\n" + "\n".join(f"- {key}: {value}" for key, value in paper_checks.items()) + "\n",
    encoding="utf-8",
)

prs = Presentation(ppt_path)
claims = []
for slide_number, slide in enumerate(prs.slides, start=1):
    text = "\n".join(
        shape.text for shape in slide.shapes if getattr(shape, "has_text_frame", False)
    )
    if re.search(r"真实环境|完成了SDMP|RRT|避障|Dobot Magician上的部署", text):
        claims.append(f"- Slide {slide_number}: " + " / ".join(text.splitlines()))
Path(".codex_tmp/evidence-report-revision/ppt-claim-audit.md").write_text(
    "# PPT claims requiring correction\n\n" + "\n".join(claims) + "\n",
    encoding="utf-8",
)
assert any("真实环境" in claim for claim in claims)
'@ | & $py - $paper $ppt
```

Expected: paper evidence confirms MAF, DTW, RRT, collision checking, and six-axis experiments; the PPT audit identifies unsupported project claims such as real-environment validation so they are not copied into the revised report.

- [ ] **Step 5: Commit policy**

No commit. All Task 1 outputs are ignored task-local evidence.

---

### Task 2: Add Tested Source-Driven Report Figure Facts

**Files:**

- Create: `tests/test_report_figures.py`
- Create: `src/dobot_algorithms/report_figures.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add failing baseline-fact tests**

Create the start of `tests/test_report_figures.py`:

```python
from pathlib import Path
import json
import shutil

import pytest
from PIL import Image

from dobot_algorithms.report_figures import (
    collect_report_facts,
    compose_playback_frames,
    render_algorithm_structures,
)


def test_default_report_facts_match_verified_baseline():
    facts = collect_report_facts("configs/default.yaml")

    assert facts.demo_count == 8
    assert facts.normalized_steps == 150
    assert facts.data_columns == ("x", "y", "z", "gripper")
    assert [item.algorithm_id for item in facts.algorithms] == [
        "gmm_gmr_dmp",
        "inc_gmm_gmr_dmp",
        "gmm_gmr_segmented_dmp",
        "bgmm_gmr_promp",
    ]
    segmented = next(
        item for item in facts.algorithms
        if item.algorithm_id == "gmm_gmr_segmented_dmp"
    )
    assert segmented.segment_sizes == (38, 38, 37, 37)
    assert facts.playback.active_algorithm == "bgmm_gmr_promp"
    assert facts.playback.pickup_threshold == pytest.approx(0.65)
    assert facts.playback.release_threshold == pytest.approx(0.35)
    assert facts.playback.release_after_phase == pytest.approx(0.5)
    assert facts.playback.endpoint_label == "播放至模型轨迹末端"
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```powershell
python -m pytest tests/test_report_figures.py::test_default_report_facts_match_verified_baseline `
  -q -p no:cacheprovider
```

Expected: FAIL with `ModuleNotFoundError: No module named 'dobot_algorithms.report_figures'`.

- [ ] **Step 3: Add Pillow and the public fact dataclasses**

In `pyproject.toml`, add:

```toml
    "Pillow>=10",
```

Create `src/dobot_algorithms/report_figures.py` with these public types and imports:

```python
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image, ImageDraw, ImageFont

from dobot_algorithms.io import load_config, load_demonstrations, project_path
from dobot_algorithms.scripts.learn import ALGORITHM_BUILDERS


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
```

- [ ] **Step 4: Implement fact collection with exact current values**

Add:

```python
def collect_report_facts(
    config_path: str | Path = "configs/default.yaml",
) -> ReportFigureFacts:
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
        raise ValueError(
            f"Report diagrams require one shared n_time_steps value, got {sorted(steps)}."
        )
    normalized_steps = steps.pop()
    algorithms = tuple(
        _algorithm_fact(
            algorithm_id,
            label,
            config[algorithm_id]["params"],
            normalized_steps,
        )
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
    algorithm_id: str,
    label: str,
    params: dict,
    normalized_steps: int,
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
        sizes = tuple(
            quotient + (1 if index < remainder else 0)
            for index in range(count)
        )
        return AlgorithmFigureFact(
            algorithm_id,
            label,
            ("经典 GMM", "GMR", "近等长分段 DMP"),
            (
                f"GMM 分量={params['n_components']}",
                f"片段数={count}",
                f"每段 DMP 基函数上限={params['dmp_basis']}",
            ),
            segment_sizes=sizes,
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
```

- [ ] **Step 5: Run the fact test**

Run:

```powershell
python -m pytest tests/test_report_figures.py::test_default_report_facts_match_verified_baseline `
  -q -p no:cacheprovider
```

Expected: `1 passed`.

- [ ] **Step 6: Commit the fact layer**

```powershell
git add -- pyproject.toml src/dobot_algorithms/report_figures.py tests/test_report_figures.py
git diff --cached --check
git commit -m "feat: add evidence-backed report figure facts"
```

Expected: the commit contains only the dependency, dataclasses/fact collection, and the first tests. After this dependency change, run `python -m pip install -e ".[dev]"` once before later CLI/test steps if the active environment was installed before Task 2.

---

### Task 3: Render the Three Source-Driven Diagrams and Manifest

**Files:**

- Modify: `tests/test_report_figures.py`
- Modify: `src/dobot_algorithms/report_figures.py`
- Create: `src/dobot_algorithms/scripts/generate_report_figures.py`
- Modify: `pyproject.toml`
- Create: `reports/figures/figure-2-1-project-data-flow.png`
- Create: `reports/figures/figure-2-1-project-data-flow.svg`
- Create: `reports/figures/figure-2-3-playback-state-machine.png`
- Create: `reports/figures/figure-2-3-playback-state-machine.svg`
- Create: `reports/figures/figure-3-1-algorithm-structures.png`
- Create: `reports/figures/figure-3-1-algorithm-structures.svg`
- Create: `reports/figures/manifest.json`

- [ ] **Step 1: Add failing diagram and manifest tests**

Append to `tests/test_report_figures.py`:

```python
from dobot_algorithms.report_figures import (
    render_playback_state_machine,
    render_project_data_flow,
    update_asset_manifest,
)


def _assert_png_record(record):
    path = Path(record.output.path)
    assert path.suffix == ".png"
    assert path.exists()
    assert record.width_px >= 1654
    assert record.height_px > 600
    assert record.dpi_x == pytest.approx(300, abs=1)
    assert record.dpi_y == pytest.approx(300, abs=1)


def test_diagrams_render_png_svg_and_manifest(tmp_path: Path):
    facts = collect_report_facts("configs/default.yaml")
    records = []
    records.extend(render_project_data_flow(facts, tmp_path / "figure-2-1"))
    records.extend(render_playback_state_machine(facts, tmp_path / "figure-2-3"))
    records.extend(render_algorithm_structures(facts, tmp_path / "figure-3-1"))
    update_asset_manifest(records, tmp_path / "manifest.json")

    assert len(records) == 6
    for record in records[::2]:
        _assert_png_record(record)
    assert all(Path(record.output.path).exists() for record in records)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {item["figure_id"] for item in manifest["assets"]} == {"2-1", "2-3", "3-1"}
    update_asset_manifest([records[0]], tmp_path / "manifest.json")
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {item["figure_id"] for item in manifest["assets"]} == {"2-1", "2-3", "3-1"}
    assert "返回 HOME" not in (tmp_path / "figure-2-3.svg").read_text(encoding="utf-8")
    assert "播放至模型轨迹末端" in (tmp_path / "figure-2-3.svg").read_text(encoding="utf-8")


def test_missing_cjk_font_fails_without_writing(tmp_path: Path):
    facts = collect_report_facts("configs/default.yaml")
    with pytest.raises(RuntimeError, match="CJK font"):
        render_algorithm_structures(
            facts,
            tmp_path / "missing",
            font_path=tmp_path / "absent.ttf",
        )
    assert not list(tmp_path.glob("missing.*"))
```

- [ ] **Step 2: Run the diagram tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_report_figures.py -q -p no:cacheprovider
```

Expected: FAIL because render and manifest functions are not implemented.

- [ ] **Step 3: Add the renderer helpers and exact public signatures**

Add to `report_figures.py`. The three public functions below use the exact bodies shown in Step 3a and Step 3b; do not leave ellipses in the implementation:

```python
def render_project_data_flow(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    return _render_project_data_flow_impl(facts, output_stem, font_path)


def render_playback_state_machine(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    return _render_playback_state_machine_impl(facts, output_stem, font_path)


def render_algorithm_structures(
    facts: ReportFigureFacts,
    output_stem: str | Path,
    *,
    font_path: str | Path | None = None,
) -> tuple[AssetRecord, AssetRecord]:
    return _render_algorithm_structures_impl(facts, output_stem, font_path)


def update_asset_manifest(
    records: Sequence[AssetRecord],
    output_path: str | Path,
) -> None:
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8")).get("assets", [])
    updated_figure_ids = {record.figure_id for record in records}
    retained = [
        item for item in existing
        if item["figure_id"] not in updated_figure_ids
    ]
    payload = {"assets": [*retained, *(asdict(record) for record in records)]}
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
    raise RuntimeError(
        "No CJK font found. Pass --font-path or install Microsoft YaHei/Noto Sans CJK."
    )


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
    return AssetRecord(
        figure_id,
        _digest(path),
        width,
        height,
        dpi_x,
        dpi_y,
        sources,
        symbols,
    )


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
```

- [ ] **Step 3a: Implement the shared diagram primitives and figures 2-1/2-3**

Add:

```python
def _new_diagram(font_path: str | Path | None, *, height: float = 7.0):
    font = FontProperties(fname=str(resolve_cjk_font(font_path)))
    fig, axis = plt.subplots(figsize=(13.0, height))
    axis.set_xlim(0, 13)
    axis.set_ylim(0, 10)
    axis.axis("off")
    return fig, axis, font


def _box(axis, font, x: float, y: float, width: float, height: float, text: str, color: str):
    patch = plt.Rectangle(
        (x, y), width, height,
        facecolor=color, edgecolor="#2F3B4A", linewidth=1.2,
    )
    axis.add_patch(patch)
    axis.text(
        x + width / 2, y + height / 2, text,
        ha="center", va="center", color="white", fontsize=10,
        fontproperties=font, fontweight="bold", wrap=True,
    )


def _arrow(axis, x1: float, y1: float, x2: float, y2: float):
    axis.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops={"arrowstyle": "->", "lw": 1.7, "color": "#34495E"},
    )


def _render_project_data_flow_impl(facts, output_stem, font_path):
    fig, axis, font = _new_diagram(font_path)
    labels = (
        f"{facts.demo_count} 条 CSV\nt,x,y,z,gripper",
        f"load_demonstrations\n归一化为 {facts.normalized_steps} 点",
        "GMM / Inc-GMM / BGMM",
        "GMR 条件均值轨迹",
        "DMP / 近等长分段 DMP\n/ 确定性 ProMP",
        "joblib / 轨迹图 / 指标表",
        "play_coppeliasim.py\nZeroMQ -> CoppeliaSim",
    )
    colors = ("#4C78A8", "#4C78A8", "#F58518", "#F58518", "#54A24B", "#54A24B", "#B279A2")
    x_positions = (0.2, 2.05, 3.9, 5.75, 7.6, 9.45, 11.05)
    widths = (1.55, 1.55, 1.55, 1.55, 1.55, 1.35, 1.7)
    for index, (label, color, x, width) in enumerate(zip(labels, colors, x_positions, widths)):
        _box(axis, font, x, 4.3, width, 1.5, label, color)
        if index:
            _arrow(axis, x_positions[index - 1] + widths[index - 1], 5.05, x, 5.05)
    axis.text(
        6.5, 7.7, "项目架构与数据流（全部节点映射到当前源码或产物）",
        ha="center", fontsize=17, fontproperties=font, fontweight="bold",
    )
    axis.text(
        6.5, 2.2,
        "当前范围：简化自由夹爪单点码垛仿真；无完整机械臂、IK、碰撞检测或 RRT",
        ha="center", fontsize=12, fontproperties=font, color="#A33A2B",
    )
    return _save_figure(
        fig,
        "2-1",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_algorithms/io.py",
            "src/dobot_algorithms/scripts/learn.py",
            "src/dobot_algorithms/scripts/play_coppeliasim.py",
        ),
        (
            "dobot_algorithms.io.load_demonstrations",
            "dobot_algorithms.scripts.learn.ALGORITHM_BUILDERS",
            "dobot_algorithms.scripts.play_coppeliasim._model_path",
        ),
    )


def _render_playback_state_machine_impl(facts, output_stem, font_path):
    fig, axis, font = _new_diagram(font_path, height=7.5)
    playback = facts.playback
    labels = (
        f"active_algorithm\n{playback.active_algorithm}",
        f"加载 joblib\n{facts.normalized_steps}x4 轨迹",
        f"设置位置\n{playback.target_path}",
        "设置左右夹爪关节",
        f"gripper >= {playback.pickup_threshold:.2f}\nsetObjectParent 绑定",
        f"phase > {playback.release_after_phase:.1f} 且\ngripper <= {playback.release_threshold:.2f}\n解除绑定",
        playback.endpoint_label,
    )
    colors = ("#4C78A8", "#4C78A8", "#F58518", "#F58518", "#54A24B", "#54A24B", "#B279A2")
    x_positions = (0.2, 2.05, 3.9, 5.75, 7.6, 9.45, 11.3)
    for index, (label, color, x) in enumerate(zip(labels, colors, x_positions)):
        _box(axis, font, x, 4.1, 1.5, 1.8, label, color)
        if index:
            _arrow(axis, x_positions[index - 1] + 1.5, 5.0, x, 5.0)
    axis.text(
        6.5, 7.7, "回放控制链路与抓放状态机",
        ha="center", fontsize=17, fontproperties=font, fontweight="bold",
    )
    axis.text(
        6.5, 1.9,
        "阈值触发 + setObjectParent；无接触力、距离或碰撞判断；无独立返回 HOME 命令",
        ha="center", fontsize=12, fontproperties=font, color="#A33A2B",
    )
    return _save_figure(
        fig,
        "2-3",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_algorithms/scripts/play_coppeliasim.py",
            "src/dobot_algorithms/coppeliasim_client.py",
        ),
        (
            "dobot_algorithms.scripts.play_coppeliasim._model_path",
            "dobot_algorithms.coppeliasim_client.CoppeliaDobotClient.play_cartesian_trajectory",
            "dobot_algorithms.coppeliasim_client.CoppeliaDobotClient._set_gripper_joints",
            "dobot_algorithms.coppeliasim_client.CoppeliaDobotClient._attach_block",
            "dobot_algorithms.coppeliasim_client.CoppeliaDobotClient._release_block",
        ),
    )
```

- [ ] **Step 3b: Implement figure 3-1 completely**

Add:

```python
def _render_algorithm_structures_impl(facts, output_stem, font_path):
    fig, axis, font = _new_diagram(font_path, height=8.0)
    axis.text(
        6.5, 9.4,
        f"共同输入：{facts.demo_count} 条 CSV，模型内归一化为 {facts.normalized_steps} 点",
        ha="center", va="center", fontsize=16,
        fontproperties=font, fontweight="bold",
    )
    colors = ("#4C78A8", "#F58518", "#54A24B", "#B279A2")
    y_positions = (7.5, 5.5, 3.5, 1.5)
    for algorithm, color, y in zip(facts.algorithms, colors, y_positions):
        x_positions = (0.7, 3.7, 6.7)
        for index, (x, stage) in enumerate(zip(x_positions, algorithm.pipeline)):
            _box(axis, font, x, y, 2.2, 0.9, stage, color)
            if index:
                _arrow(axis, x_positions[index - 1] + 2.2, y + 0.45, x, y + 0.45)
        details = list(algorithm.parameters)
        if algorithm.segment_sizes:
            details.append("实际片段点数=" + "/".join(map(str, algorithm.segment_sizes)))
        if algorithm.caveat:
            details.append(algorithm.caveat)
        axis.text(
            9.4, y + 0.45, "\n".join(details),
            ha="left", va="center", fontsize=9.5, fontproperties=font,
        )
    return _save_figure(
        fig,
        "3-1",
        output_stem,
        (
            "configs/default.yaml",
            "src/dobot_algorithms/gmr_primitives.py",
            "src/dobot_algorithms/scripts/learn.py",
        ),
        (
            "dobot_algorithms.scripts.learn.ALGORITHM_BUILDERS",
            "dobot_algorithms.gmr_primitives.GMMGMRDMP",
            "dobot_algorithms.gmr_primitives.IncGMMGMRDMP",
            "dobot_algorithms.gmr_primitives.GMMGMRSegmentedDMP",
            "dobot_algorithms.gmr_primitives.BGMMGMRProMP",
            "dobot_algorithms.gmr_primitives._segmented_dmp_rollout",
            "dobot_algorithms.gmr_primitives.BGMMGMRProMP._promp_reconstruct",
        ),
    )
```

Implement each renderer with a minimum `figsize=(13.0, 7.0)` and explicit YaHei `FontProperties`. The mandatory content is:

```text
Figure 2-1:
8 CSV -> io.load_demonstrations -> 150-point normalization ->
GMM / Inc-GMM / BGMM -> GMR -> DMP / near-equal segmented DMP / deterministic ProMP ->
joblib + plots + metrics -> play_coppeliasim.py -> ZeroMQ -> CoppeliaSim

Figure 2-3:
active_algorithm -> load joblib -> 150x4 trajectory -> set GripperBase position ->
set gripper joints -> gripper >= 0.65 attach with setObjectParent ->
phase > 0.5 and gripper <= 0.35 release -> play to model trajectory endpoint
Prominent caveat: threshold trigger + setObjectParent; no contact force, distance, or collision decision

Figure 3-1:
GMM -> GMR -> single DMP (8 components, 15 bases)
Inc-GMM -> GMR -> single DMP (inc_lam=0.25, 50 bases)
GMM -> GMR -> near-equal segmented DMP (38/38/37/37, 35 bases per segment max)
BGMM -> GMR -> deterministic ProMP basis reconstruction (8, 25, width 0.08)
Prominent caveat: no independent weight-distribution sampling
```

Use these source symbols in asset records:

```python
(
    "dobot_algorithms.io.load_demonstrations",
    "dobot_algorithms.scripts.learn.ALGORITHM_BUILDERS",
    "dobot_algorithms.gmr_primitives._segmented_dmp_rollout",
    "dobot_algorithms.gmr_primitives.BGMMGMRProMP._promp_reconstruct",
    "dobot_algorithms.scripts.play_coppeliasim._model_path",
    "dobot_algorithms.coppeliasim_client.CoppeliaDobotClient.play_cartesian_trajectory",
)
```

- [ ] **Step 4: Add the tested CLI**

Create `src/dobot_algorithms/scripts/generate_report_figures.py`:

```python
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from dobot_algorithms.report_figures import (
    collect_report_facts,
    compose_playback_frames,
    compose_scene_evidence,
    render_algorithm_structures,
    render_playback_state_machine,
    render_project_data_flow,
    update_asset_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate evidence-backed report figures.")
    parser.add_argument("--font-path")
    parser.add_argument("--manifest", default="reports/figures/manifest.json")
    subparsers = parser.add_subparsers(dest="command", required=True)
    diagrams = subparsers.add_parser("diagrams")
    diagrams.add_argument("--config", default="configs/default.yaml")
    diagrams.add_argument("--output-dir", default="reports/figures")
    scene = subparsers.add_parser("scene")
    scene.add_argument("--scene-image", required=True)
    scene.add_argument("--inventory", required=True)
    scene.add_argument(
        "--output",
        default="reports/figures/figure-2-2-coppeliasim-scene-and-objects.png",
    )
    playback = subparsers.add_parser("playback")
    playback.add_argument("--frames-manifest", required=True)
    playback.add_argument(
        "--output",
        default="reports/figures/figure-5-1-playback-keyframes.png",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records = []
    if args.command == "diagrams":
        facts = collect_report_facts(args.config)
        output_dir = Path(args.output_dir)
        records.extend(render_project_data_flow(
            facts, output_dir / "figure-2-1-project-data-flow", font_path=args.font_path
        ))
        records.extend(render_playback_state_machine(
            facts, output_dir / "figure-2-3-playback-state-machine", font_path=args.font_path
        ))
        records.extend(render_algorithm_structures(
            facts, output_dir / "figure-3-1-algorithm-structures", font_path=args.font_path
        ))
    elif args.command == "scene":
        records.append(compose_scene_evidence(
            args.scene_image, args.inventory, args.output, font_path=args.font_path
        ))
    else:
        records.append(compose_playback_frames(
            args.frames_manifest, args.output, font_path=args.font_path
        ))
    update_asset_manifest(records, args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Add to `[project.scripts]`:

```toml
dobot-report-figures = "dobot_algorithms.scripts.generate_report_figures:main"
```

Do not add an `all` command and do not generate placeholders.

- [ ] **Step 5: Run the tests and generate permanent diagrams**

Run:

```powershell
python -m pytest tests/test_report_figures.py -q -p no:cacheprovider
python -m dobot_algorithms.scripts.generate_report_figures `
  --manifest reports/figures/manifest.json `
  diagrams `
  --config configs/default.yaml `
  --output-dir reports/figures
```

Expected: all report figure tests pass; six diagram assets and `manifest.json` exist; each PNG is at least 1654 px wide and approximately 300 DPI.

- [ ] **Step 6: Inspect all three PNGs**

Open:

```text
reports/figures/figure-2-1-project-data-flow.png
reports/figures/figure-2-3-playback-state-machine.png
reports/figures/figure-3-1-algorithm-structures.png
```

Expected: Chinese glyphs render correctly; no text or arrow overlaps; `38/38/37/37` is legible; figure 2-3 says trajectory endpoint rather than return HOME; there are no robot photos or unsupported RRT/IK modules.

- [ ] **Step 7: Commit diagram code and assets**

```powershell
git add -- pyproject.toml `
  src/dobot_algorithms/report_figures.py `
  src/dobot_algorithms/scripts/generate_report_figures.py `
  tests/test_report_figures.py `
  reports/figures/figure-2-1-project-data-flow.png `
  reports/figures/figure-2-1-project-data-flow.svg `
  reports/figures/figure-2-3-playback-state-machine.png `
  reports/figures/figure-2-3-playback-state-machine.svg `
  reports/figures/figure-3-1-algorithm-structures.png `
  reports/figures/figure-3-1-algorithm-structures.svg `
  reports/figures/manifest.json
git diff --cached --check
git commit -m "feat: generate evidence-backed report diagrams"
```

Expected: no model, data, scene, DOCX, or rejected supplemental file is staged.

---

### Task 4: Export and Compose Real CoppeliaSim Scene Evidence

**Files:**

- Create: `tests/test_export_coppeliasim_inventory.py`
- Create: `src/dobot_algorithms/scripts/export_coppeliasim_inventory.py`
- Modify: `tests/test_report_figures.py`
- Modify: `src/dobot_algorithms/report_figures.py`
- Modify: `pyproject.toml`
- Create: `reports/evidence/coppeliasim/scene-overview.png`
- Create: `reports/evidence/coppeliasim/object-inventory.json`
- Create: `reports/figures/figure-2-2-coppeliasim-scene-and-objects.png`
- Modify: `reports/figures/manifest.json`

- [ ] **Step 1: Add failing read-only inventory tests**

Create `tests/test_export_coppeliasim_inventory.py`:

```python
from dobot_algorithms.scripts.export_coppeliasim_inventory import (
    collect_object_inventory,
    required_object_paths,
)


class FakeReadOnlySim:
    def __init__(self):
        self.paths = {"/GripperBase": 1, "/Floor": 2}
        self.aliases = {1: "GripperBase", 2: "Floor"}
        self.positions = {1: [0.0, 0.0, 0.15], 2: [0.2, -0.12, -0.002]}

    def getObject(self, path):
        return self.paths[path]

    def getObjectAlias(self, handle):
        return self.aliases[handle]

    def getObjectPosition(self, handle, relative_to):
        assert relative_to == -1
        return self.positions[handle]


def test_inventory_collection_uses_only_read_methods():
    inventory = collect_object_inventory(
        FakeReadOnlySim(),
        {"GripperBase": "/GripperBase", "Floor": "/Floor", "Missing": "/Missing"},
    )
    assert inventory[0]["actual_alias"] == "GripperBase"
    assert inventory[1]["world_position"] == [0.2, -0.12, -0.002]
    assert inventory[2]["found"] is False


def test_required_paths_include_every_report_object():
    paths = required_object_paths({
        "coppeliasim": {
            "target_path": "/GripperBase",
            "tip_path": "/GripperBase/GripCenter",
            "left_gripper_joint_path": "/left",
            "right_gripper_joint_path": "/right",
            "block_path": "/PalletBlock",
            "place_positions": [[0.34, -0.16, 0.006]],
        }
    })
    assert set(paths) == {
        "GripperBase", "GripCenter", "GripperJawLeftJoint", "GripperJawRightJoint",
        "PalletBlock", "PickPoint", "Place_01", "Floor",
    }
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest tests/test_export_coppeliasim_inventory.py -q -p no:cacheprovider
```

Expected: FAIL because the exporter module does not exist.

- [ ] **Step 3: Implement the read-only exporter**

Create `src/dobot_algorithms/scripts/export_coppeliasim_inventory.py` with these functions:

```python
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
from pathlib import Path

from dobot_algorithms.io import load_config, project_path


def required_object_paths(config: dict) -> dict[str, str]:
    sim = config["coppeliasim"]
    paths = {
        "GripperBase": sim["target_path"],
        "GripCenter": sim["tip_path"],
        "GripperJawLeftJoint": sim["left_gripper_joint_path"],
        "GripperJawRightJoint": sim["right_gripper_joint_path"],
        "PalletBlock": sim["block_path"],
        "PickPoint": "/PickPoint",
        "Floor": "/Floor",
    }
    for index, _ in enumerate(sim["place_positions"], start=1):
        paths[f"Place_{index:02d}"] = f"/Place_{index:02d}"
    return paths


def collect_object_inventory(sim, paths: Mapping[str, str]) -> list[dict]:
    inventory = []
    for expected_alias, object_path in paths.items():
        try:
            handle = sim.getObject(object_path)
            alias = str(sim.getObjectAlias(handle))
            position = [float(value) for value in sim.getObjectPosition(handle, -1)]
            inventory.append({
                "expected_alias": expected_alias,
                "configured_path": object_path,
                "found": True,
                "actual_alias": alias,
                "world_position": position,
            })
        except Exception as exc:
            inventory.append({
                "expected_alias": expected_alias,
                "configured_path": object_path,
                "found": False,
                "error_type": type(exc).__name__,
            })
    return inventory


def connect_read_only(config: dict):
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    sim_config = config["coppeliasim"]
    client = RemoteAPIClient(host=sim_config["host"], port=int(sim_config["port"]))
    return client.require("sim")


def export_inventory(config_path: str | Path, output_path: str | Path) -> dict:
    config = load_config(config_path)
    objects = collect_object_inventory(connect_read_only(config), required_object_paths(config))
    payload = {
        "capture_mode": "read-only Remote API object lookup",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": config["coppeliasim"]["host"],
        "port": int(config["coppeliasim"]["port"]),
        "objects": objects,
    }
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a read-only CoppeliaSim object inventory.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument(
        "--output", default="reports/evidence/coppeliasim/object-inventory.json"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = export_inventory(args.config, args.output)
    missing = [item["expected_alias"] for item in payload["objects"] if not item["found"]]
    if missing:
        print("Missing required objects: " + ", ".join(missing))
        return 2
    print(f"Exported read-only inventory: {project_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

This module may call only `RemoteAPIClient`, `client.require("sim")`, `sim.getObject`, `sim.getObjectAlias`, and `sim.getObjectPosition`. It must not contain `startSimulation`, `stopSimulation`, or any `set*` call.

Add to `[project.scripts]`:

```toml
dobot-export-scene-inventory = "dobot_algorithms.scripts.export_coppeliasim_inventory:main"
```

- [ ] **Step 4: Add the failing scene-composition test**

Append to `tests/test_report_figures.py`:

```python
from dobot_algorithms.report_figures import compose_scene_evidence


def test_scene_composition_requires_all_objects_and_labels_inventory(tmp_path: Path):
    scene = tmp_path / "scene.png"
    Image.new("RGB", (1600, 900), "#dde7ef").save(scene)
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({
        "capture_mode": "read-only Remote API object lookup",
        "objects": [
            {"expected_alias": name, "configured_path": f"/{name}", "found": True,
             "actual_alias": name, "world_position": [0.0, 0.0, 0.0]}
            for name in (
                "GripperBase", "GripCenter", "GripperJawLeftJoint",
                "GripperJawRightJoint", "PalletBlock", "PickPoint", "Place_01", "Floor",
            )
        ],
    }, ensure_ascii=False), encoding="utf-8")

    record = compose_scene_evidence(scene, inventory, tmp_path / "figure-2-2.png")
    assert record.figure_id == "2-2"
    assert record.width_px >= 1654
    assert record.dpi_x == pytest.approx(300, abs=1)

    payload = json.loads(inventory.read_text(encoding="utf-8"))
    payload["objects"][0]["found"] = False
    inventory.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required"):
        compose_scene_evidence(scene, inventory, tmp_path / "rejected.png")
```

- [ ] **Step 5: Implement scene composition**

Add:

```python
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
    missing = [item["expected_alias"] for item in payload["objects"] if not item["found"]]
    if missing:
        raise ValueError("Missing required scene objects: " + ", ".join(missing))

    with Image.open(scene) as source:
        source_rgb = source.convert("RGB")
        canvas = Image.new("RGB", (2400, 1350), "white")
        left_box = (80, 150, 1560, 1280)
        source_rgb.thumbnail((left_box[2] - left_box[0], left_box[3] - left_box[1]))
        x = left_box[0] + (left_box[2] - left_box[0] - source_rgb.width) // 2
        y = left_box[1] + (left_box[3] - left_box[1] - source_rgb.height) // 2
        canvas.paste(source_rgb, (x, y))

    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(font_file), 48)
    body_font = ImageFont.truetype(str(font_file), 30)
    draw.text((80, 50), "CoppeliaSim 简化场景总览", font=title_font, fill="#172B4D")
    draw.text((1620, 50), "Remote API 只读对象清单", font=title_font, fill="#172B4D")
    y = 160
    for item in payload["objects"]:
        position = ", ".join(f"{value:.3f}" for value in item["world_position"])
        draw.multiline_text(
            (1620, y),
            f"{item['actual_alias']}\n{item['configured_path']}\n世界坐标 [{position}]",
            font=body_font,
            fill="#23374D",
            spacing=6,
        )
        y += 135

    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, dpi=(300, 300))
    return _asset_record(
        "2-2",
        output,
        (_digest(scene), _digest(inventory_path)),
        ("export_coppeliasim_inventory.collect_object_inventory",),
    )
```

The right heading must remain exactly `Remote API 只读对象清单`; never imitate the CoppeliaSim UI object tree.

- [ ] **Step 6: Run unit tests and static read-only audit**

Run:

```powershell
python -m pytest tests/test_export_coppeliasim_inventory.py tests/test_report_figures.py `
  -q -p no:cacheprovider
rg -n "startSimulation|stopSimulation|\.set[A-Z]" `
  src/dobot_algorithms/scripts/export_coppeliasim_inventory.py
```

Expected: all tests pass; `rg` prints nothing.

- [ ] **Step 7: Start CoppeliaSim and capture an unobstructed real scene**

Run:

```powershell
Start-Process `
  -FilePath 'C:/Program Files/CoppeliaRobotics/CoppeliaSimEdu/coppeliaSim.exe' `
  -ArgumentList (Resolve-Path 'scenes/gripper_palletizing.ttt').Path
```

Then start Orca if needed:

```powershell
Start-Process -FilePath 'F:/Program Files/Orca/Orca.exe' -WindowStyle Hidden
& 'F:/Program Files/Orca/resources/bin/orca.exe' status --json
& 'F:/Program Files/Orca/resources/bin/orca.exe' computer capabilities --json
```

Use the Computer Use skill's fresh-state loop:

```powershell
& 'F:/Program Files/Orca/resources/bin/orca.exe' computer list-apps --json
& 'F:/Program Files/Orca/resources/bin/orca.exe' computer list-windows --app CoppeliaSim --json
& 'F:/Program Files/Orca/resources/bin/orca.exe' computer get-app-state `
  --app CoppeliaSim --restore-window --json
```

Close or move registration, console, firewall, Orca, or other obscuring windows using only element indices from the latest returned state. Capture the unobstructed CoppeliaSim window screenshot. In the same PowerShell command where `get-app-state --json` is called, parse `result.screenshot.path` from that fresh JSON and copy that exact file:

```powershell
New-Item -ItemType Directory -Force -Path 'reports/evidence/coppeliasim' | Out-Null
$stateJson = & 'F:/Program Files/Orca/resources/bin/orca.exe' computer get-app-state `
  --app CoppeliaSim --restore-window --json
$state = $stateJson | ConvertFrom-Json
$screenshotPath = $state.result.screenshot.path
if (-not (Test-Path -LiteralPath $screenshotPath)) {
  throw "Fresh Orca screenshot was not written: $screenshotPath"
}
Copy-Item -LiteralPath $screenshotPath `
  -Destination 'reports/evidence/coppeliasim/scene-overview.png'
```

Expected: the saved PNG is a real screen capture of `gripper_palletizing.ttt`, with the gripper, block, pick marker, place marker, and floor visible and no unrelated desktop content.

- [ ] **Step 8: Export the live read-only inventory and compose figure 2-2**

Run while the scene is open:

```powershell
python -m dobot_algorithms.scripts.export_coppeliasim_inventory `
  --config configs/default.yaml `
  --output reports/evidence/coppeliasim/object-inventory.json

python -m dobot_algorithms.scripts.generate_report_figures `
  --manifest reports/figures/manifest.json `
  scene `
  --scene-image reports/evidence/coppeliasim/scene-overview.png `
  --inventory reports/evidence/coppeliasim/object-inventory.json `
  --output reports/figures/figure-2-2-coppeliasim-scene-and-objects.png
```

Expected: inventory exit code `0`; all eight required aliases have `found: true`; figure 2-2 exists at 300 DPI and does not crop the screenshot.

- [ ] **Step 9: Inspect and commit the real scene evidence**

Visually confirm the screenshot is real, unobstructed, and matches the JSON object set. Then run:

```powershell
git add -- pyproject.toml `
  src/dobot_algorithms/report_figures.py `
  src/dobot_algorithms/scripts/export_coppeliasim_inventory.py `
  tests/test_report_figures.py `
  tests/test_export_coppeliasim_inventory.py `
  reports/evidence/coppeliasim/scene-overview.png `
  reports/evidence/coppeliasim/object-inventory.json `
  reports/figures/figure-2-2-coppeliasim-scene-and-objects.png `
  reports/figures/manifest.json
git diff --cached --check
git commit -m "feat: add real CoppeliaSim report evidence"
```

Expected: no scene `.ttt` change and no generated fake image is staged.

---

### Task 5: Add Playback-Frame Validation Without Creating a Placeholder

**Files:**

- Modify: `tests/test_report_figures.py`
- Modify: `src/dobot_algorithms/report_figures.py`
- Read later: `reports/evidence/playback/frames.json`
- Read later: `reports/evidence/playback/frame-01.png` through `frame-08.png`
- Create later: `reports/figures/figure-5-1-playback-keyframes.png`

- [ ] **Step 1: Add failing playback-validation tests**

Append:

```python
def _write_frame_manifest(tmp_path: Path, frame_count: int = 6) -> Path:
    frames = []
    for index in range(frame_count):
        path = tmp_path / f"frame-{index + 1:02d}.png"
        Image.new("RGB", (800, 450), (40 + index * 20, 80, 120)).save(path)
        frames.append({"file": path.name, "label": f"可观察阶段 {index + 1}"})
    manifest = tmp_path / "frames.json"
    manifest.write_text(json.dumps({
        "model_id": "bgmm_gmr_promp",
        "recorded_date": "2026-07-17",
        "frames": frames,
    }, ensure_ascii=False), encoding="utf-8")
    return manifest


def test_playback_collage_accepts_only_confirmed_observable_metadata(tmp_path: Path):
    manifest = _write_frame_manifest(tmp_path)
    record = compose_playback_frames(manifest, tmp_path / "collage.png")
    assert record.figure_id == "5-1"
    assert record.width_px >= 1654

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["frames"][0]["gripper"] = 0.73
    manifest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported frame metadata"):
        compose_playback_frames(manifest, tmp_path / "rejected.png")


def test_playback_collage_rejects_duplicates_and_mismatched_dimensions(tmp_path: Path):
    manifest = _write_frame_manifest(tmp_path)
    shutil.copyfile(tmp_path / "frame-01.png", tmp_path / "frame-02.png")
    with pytest.raises(ValueError, match="duplicate"):
        compose_playback_frames(manifest, tmp_path / "duplicate.png")

    manifest = _write_frame_manifest(tmp_path)
    Image.new("RGB", (640, 480), "red").save(tmp_path / "frame-06.png")
    with pytest.raises(ValueError, match="identical dimensions"):
        compose_playback_frames(manifest, tmp_path / "mismatch.png")

    manifest = _write_frame_manifest(tmp_path)
    for index in range(6):
        Image.new("RGB", (800, 600), (40 + index * 20, 80, 120)).save(
            tmp_path / f"frame-{index + 1:02d}.png"
        )
    with pytest.raises(ValueError, match="uncropped 16:9"):
        compose_playback_frames(manifest, tmp_path / "wrong-ratio.png")


@pytest.mark.parametrize("frame_count", [5, 9])
def test_playback_collage_requires_six_to_eight_frames(tmp_path: Path, frame_count: int):
    manifest = _write_frame_manifest(tmp_path, frame_count=frame_count)
    with pytest.raises(ValueError, match="6 to 8"):
        compose_playback_frames(manifest, tmp_path / "count.png")


def test_playback_collage_rejects_unconfirmed_model_id(tmp_path: Path):
    manifest = _write_frame_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["model_id"] = "unknown_model"
    manifest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="user-confirmed legal model_id"):
        compose_playback_frames(manifest, tmp_path / "model.png")
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m pytest tests/test_report_figures.py -q -p no:cacheprovider
```

Expected: FAIL because `compose_playback_frames` is not implemented.

- [ ] **Step 3: Implement strict frame input validation**

Add:

```python
def _load_frame_inputs(manifest_path: Path) -> tuple[dict, list[Path]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("model_id") not in ALGORITHM_BUILDERS:
        raise ValueError("frames.json must contain a user-confirmed legal model_id.")
    if not manifest.get("recorded_date"):
        raise ValueError("frames.json must record the user-confirmed recording date.")

    frames = manifest.get("frames", [])
    if not 6 <= len(frames) <= 8:
        raise ValueError("Playback evidence requires 6 to 8 frames.")
    paths = []
    for item in frames:
        extra = set(item) - {"file", "label"}
        if extra:
            raise ValueError(
                f"Unsupported frame metadata {sorted(extra)}; do not infer phase, index, or gripper values."
            )
        if not item.get("label"):
            raise ValueError("Every frame needs an observable-state label.")
        path = manifest_path.parent / item["file"]
        if not path.is_file() or path.suffix.lower() != ".png":
            raise ValueError(f"Missing PNG playback frame: {path}")
        paths.append(path)

    digests = [_digest(path).sha256 for path in paths]
    if len(set(digests)) != len(digests):
        raise ValueError("Playback frame set contains duplicate evidence files.")
    with Image.open(paths[0]) as first:
        expected_size = first.size
    if expected_size[0] * 9 != expected_size[1] * 16:
        raise ValueError(
            "Playback frames must be user-prepared, uncropped 16:9 images; "
            "the tool will not crop evidence."
        )
    for path in paths[1:]:
        with Image.open(path) as image:
            if image.size != expected_size:
                raise ValueError(
                    "Playback frames must have identical dimensions; the tool will not crop evidence."
                )
    return manifest, paths
```

- [ ] **Step 4: Implement the collage**

Add:

```python
def compose_playback_frames(
    frames_manifest: str | Path,
    output_path: str | Path,
    *,
    font_path: str | Path | None = None,
) -> AssetRecord:
    font_file = resolve_cjk_font(font_path)
    manifest_path = project_path(frames_manifest)
    manifest, paths = _load_frame_inputs(manifest_path)
    columns = 3 if len(paths) == 6 else 4
    rows = 2
    cell_width, cell_height = 900, 620
    canvas = Image.new("RGB", (columns * cell_width, rows * cell_height + 140), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(font_file), 46)
    label_font = ImageFont.truetype(str(font_file), 30)
    draw.text(
        (40, 30),
        f"当前模型真实回放关键帧（用户确认模型：{manifest['model_id']}）",
        font=title_font,
        fill="#172B4D",
    )
    row_counts = (3, 3) if len(paths) == 6 else ((4, 3) if len(paths) == 7 else (4, 4))
    for index, (item, path) in enumerate(zip(manifest["frames"], paths)):
        with Image.open(path) as image:
            frame = image.convert("RGB")
            frame.thumbnail((cell_width - 40, cell_height - 100))
        row = 0 if index < row_counts[0] else 1
        column = index if row == 0 else index - row_counts[0]
        row_offset = (columns - row_counts[row]) * cell_width // 2
        x = row_offset + column * cell_width + (cell_width - frame.width) // 2
        y0 = 120 + row * cell_height
        canvas.paste(frame, (x, y0))
        draw.text(
            (row_offset + column * cell_width + 20, y0 + cell_height - 75),
            item["label"],
            font=label_font,
            fill="#23374D",
        )
    output = project_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, dpi=(300, 300))
    return _asset_record(
        "5-1",
        output,
        tuple(_digest(path) for path in (manifest_path, *paths)),
        ("user-confirmed playback frames",),
    )
```

- [ ] **Step 5: Run the tests and prove missing input fails rather than creating a placeholder**

Run:

```powershell
python -m pytest tests/test_report_figures.py -q -p no:cacheprovider
python -m dobot_algorithms.scripts.generate_report_figures `
  playback `
  --frames-manifest reports/evidence/playback/frames.json
```

Expected: tests pass; the CLI fails with a missing-file error because the user's frames are not present; `reports/figures/figure-5-1-playback-keyframes.png` does not exist.

- [ ] **Step 6: Commit only the validation capability**

```powershell
git add -- src/dobot_algorithms/report_figures.py tests/test_report_figures.py
git diff --cached --check
git commit -m "feat: validate real playback report frames"
```

Expected: no `frames.json`, frame PNG, figure 5-1, or blank placeholder is committed.

---

### Task 6: Synchronize the Markdown Handoff Guide

**Files:**

- Modify: `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`
- Read: `models/algorithm_metrics.csv`
- Read: `reports/figures/manifest.json`
- Read: `.codex_tmp/evidence-report-revision/paper-evidence.md`
- Read: `.codex_tmp/evidence-report-revision/ppt-claim-audit.md`

- [ ] **Step 1: Update the scope and endpoint claims**

Replace statements that the current playback “returns HOME” as an explicit controller action with:

```markdown
回放脚本按模型输出的 150 个轨迹点依次执行，最后停在模型轨迹末端。当前代码没有独立的“返回 HOME”命令；只有模型末端坐标和实际画面能够证明时，才可把最后状态描述为返回 HOME。
```

Keep the synthetic generator's eighth waypoint labeled HOME, because that is directly defined in `generate_palletizing_demos.py`; distinguish that generator fact from the playback controller behavior.

- [ ] **Step 2: Replace the stale metric table and conclusion**

Use this exact table:

```markdown
| 算法 | Pearson 均值 | RMSE 均值 |
| --- | ---: | ---: |
| GMM+GMR+DMP | 0.9871 | 0.0187 |
| Inc-GMM+GMR+DMP | 0.9927 | 0.0123 |
| GMM+GMR+Segmented DMP | 0.9934 | 0.0139 |
| BGMM+GMR+ProMP | 0.9867 | 0.0205 |
```

Follow it with:

```markdown
当前同一组合成数据上，分段 DMP 的 Pearson 均值最高；Inc-GMM+DMP 的 RMSE 均值最低。两项指标衡量的是轨迹重构，不代表任务成功率、避障能力或实机性能。
```

- [ ] **Step 3: Add the exact parameter and segmentation table**

Insert:

```markdown
| 算法 | 混合模型参数 | 运动基元参数 |
| --- | --- | --- |
| GMM+GMR+DMP | 8 个 GMM 分量 | 15 个 DMP 基函数 |
| Inc-GMM+GMR+DMP | `inc_lam=0.25` | 50 个 DMP 基函数 |
| GMM+GMR+Segmented DMP | 8 个 GMM 分量 | `numpy.array_split` 近等长 4 段，实际 38/38/37/37 点，每段最多 35 个 DMP 基函数 |
| BGMM+GMR+ProMP | 8 个候选 BGMM 分量 | 25 个高斯基函数，宽度 0.08 |
```

- [ ] **Step 4: Replace the unsafe generator example with the exact eight-demo baseline**

Document:

```powershell
python -m dobot_algorithms.scripts.generate_palletizing_demos `
  --output-dir <空目录> `
  --n-per-pose 8 `
  --seed 42
```

State that the generator appends numbered files, so exact reconstruction requires an empty directory.

- [ ] **Step 5: Add a report-evidence reproduction subsection**

Add commands for:

```powershell
python -m dobot_algorithms.scripts.generate_report_figures `
  --manifest reports/figures/manifest.json `
  diagrams --config configs/default.yaml --output-dir reports/figures

python -m dobot_algorithms.scripts.export_coppeliasim_inventory `
  --config configs/default.yaml `
  --output reports/evidence/coppeliasim/object-inventory.json

python -m dobot_algorithms.scripts.generate_report_figures `
  scene `
  --scene-image reports/evidence/coppeliasim/scene-overview.png `
  --inventory reports/evidence/coppeliasim/object-inventory.json
```

Explain that the scene screenshot must come from a real open CoppeliaSim window and that the right panel is a Remote API inventory, not a simulated UI tree.

- [ ] **Step 6: Add the paper-reproduction boundary table**

Insert:

```markdown
| 论文内容 | 当前项目状态 |
| --- | --- |
| MAF 平滑与 DTW 时间对齐 | 未实现；当前使用自然三次样条生成固定 150 点合成数据 |
| 分段 DMP | 实现近等长 4 段对照方法，实际 38/38/37/37 点 |
| RRT 避障路径与分段点确定 | 未实现 |
| 障碍物检测、碰撞检查和安全距离 | 未实现 |
| 完整机械臂、IK 与关节控制 | 未实现 |
| 物块搬运 | 简化自由夹爪场景中使用阈值与 `setObjectParent` 实现 |
| 实机实验 | 未开展 |
```

State that paper figures, if cited, must be labeled `引自文献 [1]` and never presented as project results.

- [ ] **Step 7: Add playback-frame instructions without inventing metadata**

Document a `frames.json` example using neutral filenames:

```json
{
  "model_id": "bgmm_gmr_promp",
  "recorded_date": "2026-07-17",
  "frames": [
    {"file": "frame-01.png", "label": "HOME 初始状态"},
    {"file": "frame-02.png", "label": "到达取物点上方"},
    {"file": "frame-03.png", "label": "闭爪并触发绑定"},
    {"file": "frame-04.png", "label": "抬升物块"},
    {"file": "frame-05.png", "label": "搬运至放置点上方"},
    {"file": "frame-06.png", "label": "打开夹爪并释放"}
  ]
}
```

Clarify that `model_id` and date are user-confirmed; no frame index, phase, or exact gripper value may be inferred. If the final frame visibly returns HOME, the user may label it that way; otherwise use `播放至轨迹末端`.

- [ ] **Step 8: Audit the guide**

Run:

```powershell
$guide = 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
rg -n "0\.9392|0\.0403|0\.9397|0\.0398|综合表现仅次|两项指标均最好" $guide
rg -n "等长 4 段|平均分成 4 段|独立.*返回 HOME|完成.*RRT|真实环境.*验证" $guide
rg -n "0\.9871|0\.0187|0\.9927|0\.0123|38/38/37/37|论文复现边界|Remote API" $guide
rg -n "TBD|TODO|待补充|类似上文" $guide
```

Expected: the first, second, and fourth scans print nothing; the third prints the expected updated facts.

- [ ] **Step 9: Commit the guide**

```powershell
git add -- 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
git diff --cached --check
git commit -m "docs: align Dobot handoff guide with current evidence"
```

Expected: only the Markdown guide is committed.

---

### Task 7: Build a Read-Only DOCX Contract Verifier

**Files:**

- Create: `.codex_tmp/evidence-report-revision/verify_report_docx.py`
- Read: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- Read later: the pre-frame revised working copy

- [ ] **Step 1: Write the verifier CLI and baseline checks**

Create `.codex_tmp/evidence-report-revision/verify_report_docx.py` with this interface. Run it with the repository root as the current working directory so `models/...` checks resolve correctly:

```python
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile

from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

ANCHORS = {
    "6729C10F", "47E04918", "5F33A188", "5AC8BDF1", "2BF76456", "4CD0F97A",
    "769E2BCD", "2D034924", "27E5D114", "3692BFD0", "1F5608E5", "42A005EB",
    "1BEA7B19", "746BA622", "52DC0ACB", "5E96EEA0",
}


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def load_parts(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as package:
        return {name: package.read(name) for name in package.namelist()}


def text(root) -> str:
    return "".join(root.xpath(".//w:t/text()", namespaces=NS))


def verify_baseline(parts: dict[str, bytes]) -> dict:
    document = etree.fromstring(parts["word/document.xml"])
    styles = etree.fromstring(parts["word/styles.xml"])
    rels = etree.fromstring(parts["word/_rels/document.xml.rels"])
    para_ids = document.xpath("//w:p/@w14:paraId", namespaces=NS)
    assert ANCHORS <= set(para_ids)
    assert len(document.xpath("//w:sectPr", namespaces=NS)) == 2
    for section in document.xpath("//w:sectPr", namespaces=NS):
        size = section.xpath("./w:pgSz", namespaces=NS)[0]
        margin = section.xpath("./w:pgMar", namespaces=NS)[0]
        assert (size.get(f"{{{NS['w']}}}w"), size.get(f"{{{NS['w']}}}h")) == ("11906", "16838")
        assert (
            margin.get(f"{{{NS['w']}}}top"),
            margin.get(f"{{{NS['w']}}}right"),
            margin.get(f"{{{NS['w']}}}bottom"),
            margin.get(f"{{{NS['w']}}}left"),
        ) == ("1440", "1800", "1440", "1800")
    style_ids = set(styles.xpath("//w:style/@w:styleId", namespaces=NS))
    assert {"a", "11", "21", "31", "a6", "TOC1", "TOC2", "TOC3"} <= style_ids
    relationships = {
        item.get("Id"): item.get("Target")
        for item in rels.xpath("//pr:Relationship", namespaces=NS)
    }
    assert relationships["rId8"] == "media/image1.png"
    assert relationships["rId9"] == "media/image2.png"
    assert [relationships[f"rId{value}"] for value in range(13, 18)] == [
        f"media/image{value - 10}.png" for value in range(13, 18)
    ]
    doc_pr_ids = [int(value) for value in document.xpath("//wp:docPr/@id", namespaces=NS)]
    assert len(doc_pr_ids) == len(set(doc_pr_ids))
    assert max(doc_pr_ids) == 64
    instructions = "".join(document.xpath("//w:instrText/text()", namespaces=NS))
    assert 'TOC \\o "1-3" \\h \\z \\u' in instructions
    body = document.xpath("//w:body", namespaces=NS)[0]
    body_children = list(body)
    first_section_index = next(
        index for index, child in enumerate(body_children)
        if child.tag == f"{{{NS['w']}}}p"
        and child.get(f"{{{NS['w14']}}}paraId") == "66DEF860"
    )
    first_section = body_children[first_section_index].xpath("./w:pPr/w:sectPr", namespaces=NS)[0]
    final_section = body.xpath("./w:sectPr", namespaces=NS)[0]
    preserve_parts = [
        "word/styles.xml", "word/numbering.xml", "word/theme/theme1.xml",
        "word/header1.xml", "word/header2.xml", "word/header3.xml",
        "word/footer1.xml", "word/footer2.xml", "word/footer3.xml",
        "word/media/image1.png", "word/media/image2.png",
    ]
    return {
        "parts": {name: digest(parts[name]) for name in preserve_parts},
        "first_section": digest(etree.tostring(first_section)),
        "final_section": digest(etree.tostring(final_section)),
        "last_rendered_page_breaks": len(
            document.xpath("//w:lastRenderedPageBreak", namespaces=NS)
        ),
    }
```

- [ ] **Step 2: Add revised-stage checks**

Add:

```python
def verify_revised(
    parts: dict[str, bytes], baseline_hashes: dict, *, final: bool = False
) -> None:
    for name, expected in baseline_hashes["parts"].items():
        assert digest(parts[name]) == expected, f"preserve-only part changed: {name}"

    document = etree.fromstring(parts["word/document.xml"])
    rels = etree.fromstring(parts["word/_rels/document.xml.rels"])
    settings = etree.fromstring(parts["word/settings.xml"])
    body = document.xpath("//w:body", namespaces=NS)[0]
    body_children = list(body)
    first_section_index = next(
        index for index, child in enumerate(body_children)
        if child.tag == f"{{{NS['w']}}}p"
        and child.get(f"{{{NS['w14']}}}paraId") == "66DEF860"
    )
    first_section = body_children[first_section_index].xpath("./w:pPr/w:sectPr", namespaces=NS)[0]
    final_section = body.xpath("./w:sectPr", namespaces=NS)[0]
    assert digest(etree.tostring(first_section)) == baseline_hashes["first_section"]
    assert digest(etree.tostring(final_section)) == baseline_hashes["final_section"]
    relationships = {
        item.get("Id"): item.get("Target")
        for item in rels.xpath("//pr:Relationship", namespaces=NS)
    }
    assert [relationships[f"rId{value}"] for value in range(23, 27)] == [
        "media/figure_2_1_architecture.png",
        "media/figure_2_2_coppeliasim_scene.png",
        "media/figure_2_3_playback_control.png",
        "media/figure_3_1_algorithm_comparison.png",
    ]
    relationship_ids = rels.xpath("//pr:Relationship/@Id", namespaces=NS)
    assert len(relationship_ids) == len(set(relationship_ids))
    doc_pr_ids = [int(value) for value in document.xpath("//wp:docPr/@id", namespaces=NS)]
    assert len(doc_pr_ids) == len(set(doc_pr_ids))
    assert {65, 66, 67, 68} <= set(doc_pr_ids)
    assert not document.xpath("//wp:anchor", namespaces=NS)
    assert len(document.xpath("//w:lastRenderedPageBreak", namespaces=NS)) == (
        baseline_hashes["last_rendered_page_breaks"]
    )
    update_fields = settings.xpath("//w:updateFields/@w:val", namespaces=NS)
    assert update_fields == ["true"]

    body_text = text(document)
    for old in ("0.9392", "0.0403", "0.9397", "0.0398", "综合表现仅次于分段 DMP"):
        assert old not in body_text
    for current in ("0.9871", "0.0187", "0.9927", "0.0123", "38、38、37、37"):
        assert current in body_text
    for caption in (
        "图 2-1 项目架构与数据流",
        "图 2-2 CoppeliaSim 简化场景与对象清单",
        "图 2-3 回放控制链路与抓放状态机",
        "图 3-1 四种算法结构对照",
    ):
        assert body_text.count(caption) == 1
    assert "图 5-1" not in body_text
    assert "待补充" not in body_text

    expected_result_images = {
        "word/media/image3.png": "models/trajectory_comparison.png",
        "word/media/image4.png": "models/learned_trajectory_gmm_gmr_dmp.png",
        "word/media/image5.png": "models/learned_trajectory_inc_gmm_gmr_dmp.png",
        "word/media/image6.png": "models/learned_trajectory_gmm_gmr_segmented_dmp.png",
        "word/media/image7.png": "models/learned_trajectory_bgmm_gmr_promp.png",
    }
    for package_name, repository_name in expected_result_images.items():
        assert digest(parts[package_name]) == digest(Path(repository_name).read_bytes())

    expected_pairs = {
        "A1702101": "A1702102",
        "A1702201": "A1702202",
        "A1702301": "A1702302",
        "A1703101": "A1703102",
    }
    for image_id, caption_id in expected_pairs.items():
        image_nodes = document.xpath(
            f"//w:body/w:p[@w14:paraId='{image_id}']", namespaces=NS
        )
        assert len(image_nodes) == 1
        image_node = image_nodes[0]
        assert image_node.xpath("./w:pPr/w:keepNext", namespaces=NS)
        assert image_node.xpath(".//wp:inline", namespaces=NS)
        sibling = image_node.getnext()
        assert sibling is not None
        assert sibling.get(f"{{{NS['w14']}}}paraId") == caption_id
    if final:
        assert relationships["rId27"] == "media/figure_5_1_playback_frames.png"
        assert 69 in doc_pr_ids
        assert body_text.count("图 5-1 用户提供的当前模型真实回放关键帧") == 1
        assert digest(parts["word/media/figure_5_1_playback_frames.png"]) == digest(
            Path("reports/figures/figure-5-1-playback-keyframes.png").read_bytes()
        )
    else:
        assert "rId27" not in parts["word/_rels/document.xml.rels"].decode("utf-8")
        assert "rId27" not in parts["word/document.xml"].decode("utf-8")
```

- [ ] **Step 3: Add CLI and run baseline verification**

Add:

```python
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage", choices=("baseline", "revised", "revised-final"), required=True
    )
    parser.add_argument("--doc", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path(".codex_tmp/evidence-report-revision/docx-contract.json"),
    )
    args = parser.parse_args()
    parts = load_parts(args.doc)
    if args.stage == "baseline":
        contract = {"preserve_contract": verify_baseline(parts)}
        args.contract.parent.mkdir(parents=True, exist_ok=True)
        args.contract.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    else:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        verify_revised(
            parts,
            contract["preserve_contract"],
            final=args.stage == "revised-final",
        )
    print(f"DOCX {args.stage} contract passed: {args.doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run:

```powershell
$env:PYTHONUTF8 = '1'
$py = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$src = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
& $py '.codex_tmp/evidence-report-revision/verify_report_docx.py' `
  --stage baseline --doc $src
```

Expected: `DOCX baseline contract passed` and `docx-contract.json` is created.

- [ ] **Step 4: Commit policy**

No commit. The verifier and contract remain under ignored `.codex_tmp/`; actual DOCX edits in Task 8 are direct and reviewable XML patches.

---

### Task 8: Patch the Pre-Frame DOCX Working Copy Directly in OOXML

**Files:**

- Modify: `.codex_tmp/evidence-report-revision/unpacked/word/document.xml`
- Modify: `.codex_tmp/evidence-report-revision/unpacked/word/_rels/document.xml.rels`
- Modify: `.codex_tmp/evidence-report-revision/unpacked/word/settings.xml`
- Replace: `.codex_tmp/evidence-report-revision/unpacked/word/media/image3.png` through `image7.png`
- Create: `.codex_tmp/evidence-report-revision/unpacked/word/media/figure_2_1_architecture.png`
- Create: `.codex_tmp/evidence-report-revision/unpacked/word/media/figure_2_2_coppeliasim_scene.png`
- Create: `.codex_tmp/evidence-report-revision/unpacked/word/media/figure_2_3_playback_control.png`
- Create: `.codex_tmp/evidence-report-revision/unpacked/word/media/figure_3_1_algorithm_comparison.png`
- Create: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx`

- [ ] **Step 1: Validate and unpack without run merging**

Run:

```powershell
$env:PYTHONUTF8 = '1'
$py = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$skill = 'C:/Users/Administrator/.agents/skills/docx'
$src = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
$work = '.codex_tmp/evidence-report-revision/unpacked'

& $py "$skill/scripts/office/validate.py" $src
& $py "$skill/scripts/office/unpack.py" $src $work `
  --merge-runs false --simplify-redlines false
```

Expected: validation passes and the unpacked package retains complex cover `mc:AlternateContent`, TOC fields, and all seven original media files.

- [ ] **Step 2: Copy current result images and generated evidence images**

Run:

```powershell
$media = '.codex_tmp/evidence-report-revision/unpacked/word/media'
Copy-Item 'models/trajectory_comparison.png' "$media/image3.png" -Force
Copy-Item 'models/learned_trajectory_gmm_gmr_dmp.png' "$media/image4.png" -Force
Copy-Item 'models/learned_trajectory_inc_gmm_gmr_dmp.png' "$media/image5.png" -Force
Copy-Item 'models/learned_trajectory_gmm_gmr_segmented_dmp.png' "$media/image6.png" -Force
Copy-Item 'models/learned_trajectory_bgmm_gmr_promp.png' "$media/image7.png" -Force
Copy-Item 'reports/figures/figure-2-1-project-data-flow.png' `
  "$media/figure_2_1_architecture.png"
Copy-Item 'reports/figures/figure-2-2-coppeliasim-scene-and-objects.png' `
  "$media/figure_2_2_coppeliasim_scene.png"
Copy-Item 'reports/figures/figure-2-3-playback-state-machine.png' `
  "$media/figure_2_3_playback_control.png"
Copy-Item 'reports/figures/figure-3-1-algorithm-structures.png' `
  "$media/figure_3_1_algorithm_comparison.png"
```

Expected: binary copies complete; `image1.png` and `image2.png` remain untouched.

- [ ] **Step 3: Calculate each new image's OOXML height**

Run:

```powershell
Add-Type -AssemblyName System.Drawing
Get-ChildItem "$media/figure_*.png" | ForEach-Object {
  $image = [Drawing.Image]::FromFile($_.FullName)
  try {
    [long]$cy = [Math]::Round(5040000 * $image.Height / $image.Width)
    [pscustomobject]@{Name=$_.Name; Width=$image.Width; Height=$image.Height; Cx=5040000; Cy=$cy}
  } finally {
    $image.Dispose()
  }
} | Format-Table
```

Expected: every image is at least 1654 px wide; each calculated `Cy` is at most `4320000`. If not, revise the source diagram layout before continuing.

- [ ] **Step 4: Add `rId23`-`rId26` relationships directly**

Use `apply_patch` on `word/_rels/document.xml.rels`, inserting before `</Relationships>`:

```xml
<Relationship Id="rId23" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure_2_1_architecture.png"/>
<Relationship Id="rId24" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure_2_2_coppeliasim_scene.png"/>
<Relationship Id="rId25" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure_2_3_playback_control.png"/>
<Relationship Id="rId26" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure_3_1_algorithm_comparison.png"/>
```

Expected: no `rId27` exists in the pre-frame package.

- [ ] **Step 5: Insert the four image/caption blocks at exact anchors**

Use `apply_patch` directly on `word/document.xml`. Insert after `6729C10F`, `5F33A188`, `2BF76456`, and `769E2BCD`. For figure 2-1, use this template and replace both `IMAGE_HEIGHT_EMU` tokens with the integer `Cy` measured in Step 3; the literal token must not remain in the XML:

```xml
<w:p w14:paraId="A1702101" w14:textId="77777777" w:rsidR="00363E6B" w:rsidRDefault="00363E6B">
  <w:pPr><w:keepNext/><w:spacing w:before="80" w:after="0"/><w:jc w:val="center"/></w:pPr>
  <w:r><w:rPr><w:noProof/></w:rPr><w:drawing>
    <wp:inline distT="0" distB="0" distL="0" distR="0" wp14:anchorId="B1702101" wp14:editId="C1702101">
      <wp:extent cx="5040000" cy="IMAGE_HEIGHT_EMU"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
      <wp:docPr id="65" name="Figure 2-1" descr="项目架构与数据流"/>
      <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic><pic:nvPicPr><pic:cNvPr id="65" name="figure_2_1_architecture.png" descr="项目架构与数据流"/><pic:cNvPicPr/></pic:nvPicPr>
          <pic:blipFill><a:blip r:embed="rId23"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
          <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="5040000" cy="IMAGE_HEIGHT_EMU"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
        </pic:pic>
      </a:graphicData></a:graphic>
    </wp:inline>
  </w:drawing></w:r>
</w:p>
<w:p w14:paraId="A1702102" w14:textId="77777777" w:rsidR="00363E6B" w:rsidRDefault="00363E6B">
  <w:pPr><w:keepLines/><w:spacing w:after="80"/><w:jc w:val="center"/></w:pPr>
  <w:r><w:rPr><w:sz w:val="18"/></w:rPr><w:t>图 2-1 项目架构与数据流</w:t></w:r>
</w:p>
```

Use this fixed ID table for the other figures:

| Figure | Image paraId | Caption paraId | anchorId | editId | docPr | rId | Caption |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| 2-2 | `A1702201` | `A1702202` | `B1702201` | `C1702201` | 66 | `rId24` | `图 2-2 CoppeliaSim 简化场景与对象清单` |
| 2-3 | `A1702301` | `A1702302` | `B1702301` | `C1702301` | 67 | `rId25` | `图 2-3 回放控制链路与抓放状态机` |
| 3-1 | `A1703101` | `A1703102` | `B1703101` | `C1703101` | 68 | `rId26` | `图 3-1 四种算法结构对照` |

Do not copy `w:lastRenderedPageBreak`. The image paragraph has `keepNext`; the caption uses `keepLines` but not `keepNext`, so the caption stays with the image without forcing the next body paragraph onto the same page.

- [ ] **Step 6: Replace stale parameter, method, metric, and playback paragraphs**

Use whole-`<w:p>` replacements keyed by `w14:paraId` and keep the original `paraId`, `rsid`, and paragraph properties. Required final text:

```text
27E5D114: 四种算法使用相同的 8 条示教数据和 150 个归一化时刻。各算法当前参数见表 4-1。分段方法使用 numpy.array_split 将 150 点 GMR 参考轨迹分为 4 个近等长片段，实际长度为 38、38、37、37 点。
2B8F4FB0: 分段方法先完成经典 GMM 和 GMR，再使用 numpy.array_split 将 GMR 参考轨迹分为 4 个近等长片段，实际长度为 38、38、37、37 点；每段分别训练 DMP 后按顺序拼接。该实现用于比较局部运动基元表达，不包含论文中由碰撞检测和 RRT 避障路径确定分段点的链路。
1F5608E5: 夹爪离开放置点，随后继续播放至模型轨迹末端。当前代码没有独立的返回 HOME 命令。
42A005EB: 用户已经录制当前模型回放视频，将自行提供 6 至 8 张关键帧。收到并确认实际模型 ID 前，本工作副本不插入图 5-1，也不根据旧答辩视频或当前 active_algorithm 推测视频模型。
```

Replace the old result paragraphs with current, evidence-bounded conclusions:

```text
53D3E52C: 图 4-1 给出了四种算法在同一组合成示教数据上的整体对比。四种模型均输出 150×4 轨迹；曲线只用于观察重构趋势，算法优劣以表 4-2 的 Pearson 与 RMSE 均值分别比较。
49916EF6: 图 4-2 显示 GMM+GMR+DMP 的当前输出。其 Pearson 均值为 0.9871，RMSE 均值为 0.0187，能够复现总体动作阶段，但局部位置与夹爪过渡仍存在误差。
7E9984E5: 图 4-3 显示 Inc-GMM+GMR+DMP 的当前输出。其 Pearson 均值为 0.9927，RMSE 均值为 0.0123；RMSE 均值是四种方法中最低，但这不等同于任务成功率或避障性能最佳。
00E4AEE6: 图 4-4 显示分段 DMP 的当前输出。其 Pearson 均值为 0.9934，是四种方法中最高；RMSE 均值为 0.0139，并非最低。
3A5C4B87: 图 4-5 显示 BGMM+GMR+ProMP 的当前输出。其 Pearson 均值为 0.9867，RMSE 均值为 0.0205。当前实现是确定性基函数重构，不支持独立随机轨迹采样的结论。
10215BEB: 从总体指标看，分段 DMP 的 Pearson 均值最高，Inc-GMM+DMP 的 RMSE 均值最低。因此不能把任一方法描述为两项总体指标都最优，也不能按单一综合排名代替分指标结论。
6AD00C5A: 这些指标来自同一组合成数据上的轨迹重构比较。Pearson 衡量变化趋势，RMSE 衡量数值误差；二者都不能证明抓取成功率、碰撞安全、避障能力或实机性能。
4A6C1852: 分段 DMP 在 Pearson 指标上占优，可能与单点码垛轨迹具有明显阶段性有关；Inc-GMM+DMP 在 RMSE 指标上占优，则说明当前参数下整体数值误差更小。该解释仅针对当前合成基线。
2FEDE6CB: 当前 8 条数据均由同一套关键点、自然三次样条和扰动规则生成。结果不能替代真实示教、多目标泛化、完整机械臂可达性、任务成功率或避障实验。
```

- [ ] **Step 7: Insert the parameter table and renumber the metric caption**

After paragraph `27E5D114`, insert caption `表 4-1 四种算法当前关键参数` and a four-row table cloned from the existing third table's borders, header shading, font size, cell margins, and style `a6`. Use columns:

```text
算法 | 混合模型参数 | 运动基元参数
GMM+GMR+DMP | 8 个 GMM 分量 | 15 个 DMP 基函数
Inc-GMM+GMR+DMP | inc_lam=0.25 | 50 个 DMP 基函数
GMM+GMR+Segmented DMP | 8 个 GMM 分量 | 近等长 4 段（38/38/37/37），每段最多 35 个基函数
BGMM+GMR+ProMP | 8 个候选 BGMM 分量 | 25 个高斯基函数，宽度 0.08
```

Use total width `8221 dxa` with columns `3300/2200/2721`, and set both grid widths and cell `w:tcW` values.

Replace paragraph `36D55658` with `表 4-2 四种算法总体评价指标` and update exact metric cells:

```text
5E780527: 0.9871
3D6A9C42: 0.0187
29B6EEF9: 0.9927
69FA94AE: 0.0123
```

- [ ] **Step 8: Replace section 6.2 with the paper-comparison boundary**

Preserve bookmark `id=27` and name `_Toc234605501` in paragraph `1BEA7B19`, changing only its title text to:

```text
6.2 论文复现边界与当前局限
```

Replace paragraphs `0D813471` through `1568E6D1` with one introduction, the following two-column table, and one conclusion before `746BA622`:

```text
论文内容 | 当前项目状态
MAF 平滑与 DTW 时间对齐 | 未实现；当前使用自然三次样条生成固定 150 点合成数据
分段 DMP | 使用 numpy.array_split 实现近等长 4 段对照方法，实际 38/38/37/37 点
RRT 避障路径与分段点确定 | 未实现
障碍物检测、碰撞检查和安全距离 | 未实现
完整机械臂、IK 与关节控制 | 未实现
物块搬运 | 简化自由夹爪场景中以阈值和 setObjectParent 实现
实机实验 | 未开展
```

Use total width `8221 dxa`, columns `3200/5021`, table style `a6`, header shading `D9EAF7`, and repeat the header row. Final body text must say paper figures are literature evidence and must be labeled `引自文献 [1]`, not project results.

- [ ] **Step 9: Update appendix reproduction commands**

Replace `52DC0ACB` with a paragraph stating that permanent evidence includes the current five result plots, four source-driven/real-scene figures, asset manifest, scene inventory, four models, metrics, and scene file; figure 5-1 remains pending user-provided frames.

After `52DC0ACB` and before `5E96EEA0`, insert code-formatted paragraphs cloned from `5E96EEA0` for:

```text
python -m pytest tests/test_bgmm_promp.py -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
python -m dobot_algorithms.scripts.generate_palletizing_demos --output-dir <空目录> --n-per-pose 8 --seed 42
python -m dobot_algorithms.scripts.learn --config configs/default.yaml
python -m dobot_algorithms.scripts.generate_report_figures --manifest reports/figures/manifest.json diagrams --config configs/default.yaml --output-dir reports/figures
python -m dobot_algorithms.scripts.export_coppeliasim_inventory --config configs/default.yaml --output reports/evidence/coppeliasim/object-inventory.json
python -m dobot_algorithms.scripts.play_coppeliasim --config configs/default.yaml --place-index 1
```

Remove duplicate old command paragraphs if the same command already follows.

- [ ] **Step 10: Enable Word field updates**

Use `apply_patch` on `word/settings.xml`. Immediately before `<w:compat>`, insert:

```xml
<w:updateFields w:val="true"/>
```

Expected: it appears exactly once.

- [ ] **Step 11: Pack, validate, and run the revised contract**

Run:

```powershell
$out = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx'
& $py "$skill/scripts/office/pack.py" $work $out --original $src --validate true
& $py "$skill/scripts/office/validate.py" $out
& $py "$skill/scripts/office/validate.py" $out --original $src
& $py '.codex_tmp/evidence-report-revision/verify_report_docx.py' `
  --stage revised --doc $out
```

Expected: all three validations pass; the revised contract confirms four new figures, current metrics, current five result images, no figure 5-1, no blank placeholder, and unchanged preserve-only parts.

- [ ] **Step 12: Prove the retained report did not change**

Run:

```powershell
$before = (Select-String -LiteralPath '.codex_tmp/evidence-report-revision/baseline.sha256' `
  -Pattern 'Hash\s*:' | ForEach-Object { ($_ -split ':',2)[1].Trim() })
$after = (Get-FileHash -Algorithm SHA256 $src).Hash
if ($before -ne $after) { throw 'Retained report changed before visual QA.' }
```

Expected: no exception.

- [ ] **Step 13: Commit the pre-frame DOCX working copy**

```powershell
git add -- 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx'
git status --short
git commit -m "docs: revise Dobot report with evidence-backed figures"
```

Expected: only the explicitly named pre-frame DOCX is committed; the retained baseline remains unchanged.

---

### Task 9: Add Timeout-Safe Word/WPS Render QA

**Files:**

- Create: `scripts/report_qa/OfficeWorker.ps1`
- Create: `scripts/report_qa/Invoke-ReportQa.ps1`
- Create: `scripts/report_qa/verify_render.py`
- Create: `tests/report_qa_timeout_safety.ps1`

- [ ] **Step 1: Write the failing exact-process safety test**

Create `tests/report_qa_timeout_safety.ps1`. It must dot-source `Invoke-ReportQa.ps1`, start two hidden `powershell.exe` processes, mark one as task-owned, and assert:

```powershell
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../scripts/report_qa/Invoke-ReportQa.ps1"

$owned = Start-Process powershell.exe -ArgumentList '-NoProfile','-Command','Start-Sleep 60' `
  -WindowStyle Hidden -PassThru
$unrelated = Start-Process powershell.exe -ArgumentList '-NoProfile','-Command','Start-Sleep 60' `
  -WindowStyle Hidden -PassThru
try {
  Stop-ExactProcess `
    -Id $owned.Id `
    -StartTicks $owned.StartTime.ToUniversalTime().Ticks `
    -ExpectedPath $owned.Path `
    -AllowedNames @($owned.ProcessName)
  if (Get-Process -Id $owned.Id -ErrorAction SilentlyContinue) {
    throw 'Owned process survived.'
  }
  if (-not (Get-Process -Id $unrelated.Id -ErrorAction SilentlyContinue)) {
    throw 'Unrelated process was terminated.'
  }
  try {
    Stop-ExactProcess `
      -Id $unrelated.Id `
      -StartTicks 0 `
      -ExpectedPath $unrelated.Path `
      -AllowedNames @($unrelated.ProcessName)
    throw 'Mismatched marker was accepted.'
  } catch {
    if ($_.Exception.Message -notmatch 'Refusing') { throw }
  }
} finally {
  if (Get-Process -Id $owned.Id -ErrorAction SilentlyContinue) { Stop-Process -Id $owned.Id -Force }
  if (Get-Process -Id $unrelated.Id -ErrorAction SilentlyContinue) { Stop-Process -Id $unrelated.Id -Force }
}
```

Also append this source scan so the test fails on bulk-kill patterns:

```powershell
$source = Get-Content -LiteralPath "$PSScriptRoot/../scripts/report_qa/Invoke-ReportQa.ps1" -Raw
foreach ($forbidden in ('taskkill', 'Get-Process WINWORD | Stop-Process', 'Stop-Process -Name')) {
  if ($source -like "*$forbidden*") { throw "Forbidden bulk-kill pattern: $forbidden" }
}
Write-Output 'report_qa_timeout_safety passed'
```

- [ ] **Step 2: Run the safety test and verify failure**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File tests/report_qa_timeout_safety.ps1
```

Expected: FAIL because the QA scripts do not exist.

- [ ] **Step 3: Implement `Stop-ExactProcess` and marker validation**

Create `scripts/report_qa/Invoke-ReportQa.ps1` with this optional `param(...)` block as the first executable statement, followed by strict mode and the functions. This lets the safety test dot-source functions without running the workflow:

```powershell
param(
  [string]$Source,
  [string]$Baseline,
  [string]$OutputRoot = '.codex_tmp/evidence-report-qa',
  [int]$ExpectedTables = 5,
  [int]$ExpectedInlineShapes = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Stop-ExactProcess {
  param(
    [int]$Id,
    [long]$StartTicks,
    [string]$ExpectedPath,
    [string[]]$AllowedNames
  )
  $process = Get-Process -Id $Id -ErrorAction SilentlyContinue
  if (-not $process) { return }
  if ($process.StartTime.ToUniversalTime().Ticks -ne $StartTicks) {
    throw "Refusing to terminate reused PID $Id."
  }
  if ($AllowedNames -notcontains $process.ProcessName) {
    throw "Refusing to terminate unexpected process $($process.ProcessName)."
  }
  if (-not [StringComparer]::OrdinalIgnoreCase.Equals($process.Path, $ExpectedPath)) {
    throw 'Refusing to terminate process with unexpected path.'
  }
  Stop-Process -Id $Id -Force
}


function Stop-ExactlyMarkedOfficeProcess {
  param([string]$MarkerPath)
  if (-not (Test-Path -LiteralPath $MarkerPath)) { return }
  $marker = Get-Content -LiteralPath $MarkerPath -Raw | ConvertFrom-Json
  if ($marker.CreatedByTask -ne $true) { throw 'Refusing unowned Office marker.' }
  $allowed = if ($marker.Engine -eq 'Word') { @('WINWORD') } else { @('wps') }
  Stop-ExactProcess `
    -Id $marker.OfficePid `
    -StartTicks $marker.OfficeStartTicks `
    -ExpectedPath $marker.OfficePath `
    -AllowedNames $allowed
}
```

- [ ] **Step 4: Implement the isolated COM worker**

Create `scripts/report_qa/OfficeWorker.ps1` with parameters `Engine`, `Mode`, `Source`, `Pdf`, `MarkerPath`, and `ResultPath`. Add the Win32 PID lookup and COM ownership guard:

```powershell
param(
  [ValidateSet('Word','Wps')][string]$Engine,
  [ValidateSet('Prepare','Export')][string]$Mode,
  [string]$Source,
  [string]$Pdf,
  [string]$MarkerPath,
  [string]$ResultPath
)

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class NativeMethods {
  [DllImport("user32.dll")]
  public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@

$comName = if ($Engine -eq 'Word') { 'Word.Application' } else { 'KWPS.Application' }
$processName = if ($Engine -eq 'Word') { 'WINWORD' } else { 'wps' }
$preexistingIds = @(Get-Process -Name $processName -ErrorAction SilentlyContinue | ForEach-Object Id)
$app = New-Object -ComObject $comName
$app.Visible = $false
$app.DisplayAlerts = 0
$officePid = [uint32]0
$hWnd = [IntPtr]$app.Hwnd
if ($hWnd -eq [IntPtr]::Zero) {
  [Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null
  throw "$Engine COM did not expose a window handle; refusing untracked process ownership."
}
[void][NativeMethods]::GetWindowThreadProcessId($hWnd, [ref]$officePid)
if ($officePid -eq 0) {
  [Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null
  throw "$Engine COM process ID could not be resolved."
}
if ($preexistingIds -contains [int]$officePid) {
  [Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null
  throw "COM reused a pre-existing $processName process."
}
$officeProcess = Get-Process -Id $officePid
[pscustomobject]@{
  HostPid = $PID
  HostStartTicks = (Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks
  OfficePid = $officePid
  OfficeStartTicks = $officeProcess.StartTime.ToUniversalTime().Ticks
  OfficePath = $officeProcess.Path
  Engine = $Engine
  CreatedByTask = $true
  Stage = $Mode
} | ConvertTo-Json | Set-Content -LiteralPath $MarkerPath -Encoding UTF8
```

For `Prepare`, open writable, update the single TOC and all fields, repaginate, save, and write `Pages`, `TOCs`, `Fields`, `Sections`, `Tables`, and `InlineShapes` to `ResultPath`. For `Export`, open read-only and use:

```powershell
$doc = $null
try {
  if ($Mode -eq 'Prepare') {
    $doc = $app.Documents.Open($Source, $false, $false, $false)
    for ($index = 1; $index -le $doc.TablesOfContents.Count; $index++) {
      [void]$doc.TablesOfContents.Item($index).Update()
    }
    [void]$doc.Fields.Update()
    [void]$doc.Repaginate()
    $doc.Save()
    [pscustomobject]@{
      Pages = $doc.ComputeStatistics(2)
      TOCs = $doc.TablesOfContents.Count
      Fields = $doc.Fields.Count
      Sections = $doc.Sections.Count
      Tables = $doc.Tables.Count
      InlineShapes = $doc.InlineShapes.Count
    } | ConvertTo-Json | Set-Content -LiteralPath $ResultPath -Encoding UTF8
  } else {
    $doc = $app.Documents.Open($Source, $false, $true, $false)
    if ($Engine -eq 'Word') {
      $doc.ExportAsFixedFormat(
        $Pdf, 17, $false, 0, 0, 1, 1, 0,
        $true, $true, 1, $true, $true, $false
      )
    } else {
      $doc.ExportAsFixedFormat($Pdf, 17)
    }
    [pscustomobject]@{Pdf=$Pdf; Engine=$Engine} |
      ConvertTo-Json | Set-Content -LiteralPath $ResultPath -Encoding UTF8
  }
} finally {
  if ($doc -ne $null) {
    $doc.Close($false)
    [Runtime.InteropServices.Marshal]::FinalReleaseComObject($doc) | Out-Null
  }
  $app.Quit()
  [Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null
}
```

The pre-existing PID guard above proves this COM process is task-owned before this `finally` block can call `Quit`.

- [ ] **Step 5: Implement timed workers, Word-to-WPS fallback, and Poppler rendering**

Add to `Invoke-ReportQa.ps1`:

```powershell
function Invoke-TimedWorker {
  param(
    [string]$Engine,
    [string]$Mode,
    [string]$Source,
    [string]$Pdf,
    [string]$RunDir,
    [int]$TimeoutMs = 90000
  )
  $marker = Join-Path $RunDir "marker-$($Engine.ToLower())-$($Mode.ToLower()).json"
  $result = Join-Path $RunDir "result-$($Engine.ToLower())-$($Mode.ToLower()).json"
  $stdout = Join-Path $RunDir "stdout-$($Engine.ToLower())-$($Mode.ToLower()).log"
  $stderr = Join-Path $RunDir "stderr-$($Engine.ToLower())-$($Mode.ToLower()).log"
  $worker = Join-Path $PSScriptRoot 'OfficeWorker.ps1'
  $arguments = @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File', $worker,
    '-Engine', $Engine, '-Mode', $Mode, '-Source', $Source,
    '-Pdf', $Pdf, '-MarkerPath', $marker, '-ResultPath', $result
  )
  $powershellExe = (Get-Command powershell.exe -ErrorAction Stop).Source
  $process = Start-Process -FilePath $powershellExe `
    -ArgumentList $arguments -WindowStyle Hidden `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  $hostStartTicks = $process.StartTime.ToUniversalTime().Ticks
  if (-not $process.WaitForExit($TimeoutMs)) {
    Stop-ExactlyMarkedOfficeProcess -MarkerPath $marker
    Stop-ExactProcess -Id $process.Id -StartTicks $hostStartTicks `
      -ExpectedPath $powershellExe -AllowedNames @('powershell')
    return [pscustomobject]@{Success=$false; TimedOut=$true; ResultPath=$result}
  }
  return [pscustomobject]@{Success=($process.ExitCode -eq 0); TimedOut=$false; ResultPath=$result}
}


function Test-ValidPdf {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return $false }
  $item = Get-Item -LiteralPath $Path
  if ($item.Length -lt 65536) { return $false }
  $bytes = [IO.File]::ReadAllBytes($Path)
  return [Text.Encoding]::ASCII.GetString($bytes, 0, 5) -eq '%PDF-'
}


function Get-Sha256 {
  param([string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}
```

At the end of the script, run the main workflow only when the file is invoked rather than dot-sourced:

```powershell
if ($MyInvocation.InvocationName -ne '.') {
  if ([string]::IsNullOrWhiteSpace($Source) -or [string]::IsNullOrWhiteSpace($Baseline)) {
    throw 'Invoke-ReportQa.ps1 requires -Source and -Baseline.'
  }
  $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $runDir = Join-Path $OutputRoot $timestamp
  $renderDir = Join-Path $runDir 'rendered'
  New-Item -ItemType Directory -Force -Path $runDir,$renderDir | Out-Null
  $candidateDocx = Join-Path $runDir 'candidate.docx'
  Copy-Item -LiteralPath $Source -Destination $candidateDocx
  $baselineStart = Get-Sha256 $Baseline

  $prepare = Invoke-TimedWorker -Engine Word -Mode Prepare -Source $candidateDocx `
    -Pdf '' -RunDir $runDir
  if (-not $prepare.Success) { throw 'Word preparation failed or timed out.' }
  $prepareMeta = Get-Content -LiteralPath $prepare.ResultPath -Raw | ConvertFrom-Json
  if ($prepareMeta.TOCs -ne 1) { throw 'Expected exactly one TOC.' }
  if ($prepareMeta.Sections -ne 2) { throw 'Expected exactly two sections.' }
  if ($prepareMeta.Tables -ne $ExpectedTables) {
    throw "Expected $ExpectedTables tables, found $($prepareMeta.Tables)."
  }
  if ($prepareMeta.InlineShapes -ne $ExpectedInlineShapes) {
    throw "Expected $ExpectedInlineShapes inline shapes, found $($prepareMeta.InlineShapes)."
  }

  $python = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
  $validator = 'C:/Users/Administrator/.agents/skills/docx/scripts/office/validate.py'
  & $python $validator $candidateDocx -v
  if ($LASTEXITCODE -ne 0) { throw 'DOCX validation failed after Word preparation.' }

  $wordPdf = Join-Path $runDir 'word.pdf'
  $wpsPdf = Join-Path $runDir 'wps.pdf'
  $exportStart = Get-Date
  $wordResult = Invoke-TimedWorker -Engine Word -Mode Export -Source $candidateDocx `
    -Pdf $wordPdf -RunDir $runDir
  if (-not $wordResult.Success -or -not (Test-ValidPdf $wordPdf)) {
    $wpsResult = Invoke-TimedWorker -Engine Wps -Mode Export -Source $candidateDocx `
      -Pdf $wpsPdf -RunDir $runDir
    if (-not $wpsResult.Success -or -not (Test-ValidPdf $wpsPdf)) {
      throw 'Both Word and WPS export failed.'
    }
    $acceptedPdf = $wpsPdf
    $engine = 'Wps'
  } else {
    $acceptedPdf = $wordPdf
    $engine = 'Word'
  }
  $exportDurationMs = [int]((Get-Date) - $exportStart).TotalMilliseconds
```

Continue inside the same `if ($MyInvocation.InvocationName -ne '.')` block. Call the exact executables, not broken `.cmd` wrappers:

```powershell
$pdfInfo = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdfinfo.exe'
$pdfToPpm = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
$pdfInfoOutput = & $pdfInfo $acceptedPdf
if ($LASTEXITCODE -ne 0) { throw 'pdfinfo rejected the PDF.' }
& $pdfToPpm -png -r 180 $acceptedPdf (Join-Path $renderDir 'page')
if ($LASTEXITCODE -ne 0) { throw 'pdftoppm rendering failed.' }

& $python (Join-Path $PSScriptRoot 'verify_render.py') `
  --pdf $acceptedPdf --render-dir $renderDir --expected-pages $prepareMeta.Pages
if ($LASTEXITCODE -ne 0) { throw 'Rendered-page verification failed.' }

$baselineEnd = Get-Sha256 $Baseline
if ($baselineStart -ne $baselineEnd) { throw 'Retained baseline hash changed.' }
$pagesMatch = $pdfInfoOutput | Select-String '^Pages:\s+(\d+)$'
if (-not $pagesMatch) { throw 'pdfinfo output did not contain a page count.' }
$pdfPages = $pagesMatch.Matches[0].Groups[1].Value
$pngCount = @(Get-ChildItem -LiteralPath $renderDir -Filter 'page-*.png').Count
  [pscustomobject]@{
    CandidateSha256 = Get-Sha256 $candidateDocx
    PdfSha256 = Get-Sha256 $acceptedPdf
    Engine = $engine
    FallbackUsed = ($engine -eq 'Wps')
    ExportDurationMs = $exportDurationMs
    WordPages = [int]$prepareMeta.Pages
    PdfPages = [int]$pdfPages
    PngCount = $pngCount
    BaselineStartSha256 = $baselineStart
    BaselineEndSha256 = $baselineEnd
  } | ConvertTo-Json | Set-Content `
    -LiteralPath (Join-Path $runDir 'qa-manifest.json') -Encoding UTF8
}
```

- [ ] **Step 6: Implement automatic PDF/PNG assertions**

Create `scripts/report_qa/verify_render.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageStat
from pypdf import PdfReader


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path, required=True)
    parser.add_argument("--expected-pages", type=int, required=True)
    args = parser.parse_args()

    pages = len(PdfReader(args.pdf).pages)
    assert pages == args.expected_pages
    pngs = sorted(args.render_dir.glob("page-*.png"))
    assert len(pngs) == pages
    for index, path in enumerate(pngs, start=1):
        assert path.stem.endswith(f"{index:02d}") or path.stem.endswith(f"{index:03d}")
        assert path.stat().st_size > 20_000
        with Image.open(path) as image:
            image.verify()
        with Image.open(path).convert("L") as image:
            assert 1450 <= image.width <= 1525
            assert 2050 <= image.height <= 2150
            assert ImageStat.Stat(image).var[0] > 5.0
    print(f"Render verification passed: {pages} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The block above writes the complete required `qa-manifest.json`.

- [ ] **Step 7: Run the process-safety test**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File tests/report_qa_timeout_safety.ps1
```

Expected: PASS; the owned process is stopped, the unrelated process survives until test cleanup, mismatched markers are refused, and forbidden bulk-kill patterns are absent.

- [ ] **Step 8: Commit QA tooling**

```powershell
git add -- scripts/report_qa/OfficeWorker.ps1 `
  scripts/report_qa/Invoke-ReportQa.ps1 `
  scripts/report_qa/verify_render.py `
  tests/report_qa_timeout_safety.ps1
git diff --cached --check
git commit -m "test: add timeout-safe report render QA"
```

Expected: only reusable QA tooling is committed.

---

### Task 10: Run Structural, PDF, and Full-Page QA on the Pre-Frame Copy

**Files:**

- Read: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx`
- Create: `.codex_tmp/evidence-report-qa/<timestamp>/candidate.docx`
- Create: `.codex_tmp/evidence-report-qa/<timestamp>/word.pdf` or `wps.pdf`
- Create: `.codex_tmp/evidence-report-qa/<timestamp>/rendered/page-*.png`
- Create: `.codex_tmp/evidence-report-qa/<timestamp>/qa-manifest.json`
- Create: `.codex_tmp/evidence-report-qa/<timestamp>/qa-notes.md`

- [ ] **Step 1: Run the DOCX validator again**

Run:

```powershell
$env:PYTHONUTF8 = '1'
$py = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$validator = 'C:/Users/Administrator/.agents/skills/docx/scripts/office/validate.py'
$candidate = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx'
& $py $validator $candidate -v
```

Expected: exit code `0`, no repair warning.

- [ ] **Step 2: Run isolated Word preparation and export QA**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts/report_qa/Invoke-ReportQa.ps1 `
  -Source $candidate `
  -Baseline 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx' `
  -OutputRoot '.codex_tmp/evidence-report-qa' `
  -ExpectedTables 5 `
  -ExpectedInlineShapes 10
```

Expected: Word preparation reports `TOCs=1`, `Sections=2`, `Tables=5`, and `InlineShapes=10`; the retained baseline has six inline shapes and the pre-frame revision adds four evidence figures. If any count differs, stop and inspect the package rather than relaxing the expectation. The accepted PDF page count equals Word `ComputeStatistics(2)`; PNG count equals PDF page count. The page count need not remain 14, but every additional page must be explained by new figures/tables/content.

- [ ] **Step 3: Reject an inconsistent WPS fallback**

If `qa-manifest.json` shows `engine=Wps`, compare WPS PDF page count with the Word prepare page count. If they differ, mark the run failed and use visible Microsoft Word GUI `另存为 PDF`; do not accept the WPS version as final evidence.

Expected: only a page-consistent WPS PDF may proceed to visual inspection.

- [ ] **Step 4: Inspect every rendered page**

Use the PDF skill's render-and-inspect requirement. Check every `rendered/page-*.png` and record `PASS` or a concrete defect in `qa-notes.md` for:

```text
[ ] Cover and fallback logo render correctly
[ ] Assessment pages unchanged
[ ] TOC has one entry set and updated page numbers
[ ] Heading 6.2 reads 论文复现边界与当前局限
[ ] Figures 2-1, 2-2, 2-3, and 3-1 are sharp and have centered captions
[ ] Figure 2-2 says Remote API 只读对象清单
[ ] Tables 4-1 and 4-2 fit within 14.65 cm content width
[ ] All five current result plots are sharp and correctly captioned
[ ] No figure 5-1 placeholder exists
[ ] Headers, footers, and page numbers remain correct
[ ] No Chinese tofu, crop, overlap, isolated heading, caption split, or blank page
```

Expected: zero open defects. If any page fails, patch the unpacked XML or source figure, rebuild the pre-frame DOCX, and repeat Tasks 8-10.

- [ ] **Step 5: Re-run automatic and repository tests**

Run:

```powershell
python -m pytest tests/test_bgmm_promp.py -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
python -m ruff check src tests
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File tests/report_qa_timeout_safety.ps1
git diff --check
```

Expected: algorithm baseline still reports `5 passed`; full suite reports all current tests passed with its actual larger count; Ruff and PowerShell safety test pass; `git diff --check` is clean.

- [ ] **Step 6: Record the retained baseline hash at the end**

Run:

```powershell
$src = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
$before = (Select-String -LiteralPath '.codex_tmp/evidence-report-revision/baseline.sha256' `
  -Pattern 'Hash\s*:' | ForEach-Object { ($_ -split ':',2)[1].Trim() })
$after = (Get-FileHash -Algorithm SHA256 $src).Hash
if ($before -ne $after) { throw 'Retained baseline changed during QA.' }
```

Expected: hashes match.

- [ ] **Step 7: Commit QA-driven corrections only when concrete files changed**

If QA required changes, inspect `git status --short`, then explicitly list each corrected permanent file in `git add --`; for example, if only figure 2-2 and the pre-frame DOCX changed:

```powershell
git add -- 'reports/figures/figure-2-2-coppeliasim-scene-and-objects.png' `
  'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订_待回放关键帧.docx'
git diff --cached --check
git commit -m "fix: resolve report render QA defects"
```

Replace the example list with the actual changed permanent files and omit unchanged paths. If no corrections were needed, no commit is required.

---

### Task 11: Complete Figure 5-1 After the User Supplies Real Frames

**Files:**

- Create: `reports/evidence/playback/frames.json`
- Create: `reports/evidence/playback/frame-01.png` through `frame-06.png`, `frame-07.png`, or `frame-08.png`
- Create: `reports/figures/figure-5-1-playback-keyframes.png`
- Modify: `reports/figures/manifest.json`
- Modify: `.codex_tmp/evidence-report-revision/unpacked/word/document.xml`
- Modify: `.codex_tmp/evidence-report-revision/unpacked/word/_rels/document.xml.rels`
- Create: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订.docx`

- [ ] **Step 1: Copy the user's frames without editing their evidence**

Place 6-8 user-provided PNGs in `reports/evidence/playback/` using neutral names `frame-01.png` through `frame-08.png`. Do not crop, enhance, interpolate, or generate replacement frames.

Expected: all frames have identical dimensions and visibly come from the user's current recording.

- [ ] **Step 2: Write `frames.json` from user-confirmed facts only**

Ask the user for the confirmed model ID, recording date, and labels before writing the file. Once supplied, write a concrete JSON document using the confirmed values and this schema (the example values below are illustrative and must not be copied unless the user confirms them):

```json
{
  "model_id": "bgmm_gmr_promp",
  "recorded_date": "2026-07-17",
  "frames": [
    {"file": "frame-01.png", "label": "HOME 初始状态"},
    {"file": "frame-02.png", "label": "到达取物点上方"},
    {"file": "frame-03.png", "label": "闭爪并触发绑定"},
    {"file": "frame-04.png", "label": "抬升物块"},
    {"file": "frame-05.png", "label": "搬运至放置点上方"},
    {"file": "frame-06.png", "label": "打开夹爪并释放"}
  ]
}
```

Allowed `model_id` values are the four keys in `ALGORITHM_BUILDERS`. Do not add inferred phase, trajectory index, timestamp, or gripper values. Label the final frame `返回 HOME` only if the image itself clearly proves that state; otherwise use `播放至轨迹末端`.

- [ ] **Step 3: Generate and inspect figure 5-1**

Run:

```powershell
python -m dobot_algorithms.scripts.generate_report_figures `
  --manifest reports/figures/manifest.json `
  playback `
  --frames-manifest reports/evidence/playback/frames.json `
  --output reports/figures/figure-5-1-playback-keyframes.png
```

Expected: command succeeds; collage is 300 DPI, at least 1654 px wide, uses all 6-8 nonduplicate frames without cropping, and includes the user-confirmed model ID.

- [ ] **Step 4: Add `rId27` and figure 5-1 directly to OOXML**

In `document.xml.rels`, add:

```xml
<Relationship Id="rId27" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure_5_1_playback_frames.png"/>
```

Copy the collage to `word/media/figure_5_1_playback_frames.png`. Insert it after `1F5608E5` and before `42A005EB`, using:

```text
image paraId=A1705101
caption paraId=A1705102
anchorId=B1705101
editId=C1705101
docPr=69
caption=图 5-1 用户提供的当前模型真实回放关键帧
```

Use width `5040000 EMU` and calculate proportional height. Replace `42A005EB` with a factual description of the confirmed model/date and observable stages; remove the pre-frame pending language.

- [ ] **Step 5: Pack the final-named report and run every validation again**

Run:

```powershell
$final = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订.docx'
& $py "$skill/scripts/office/pack.py" $work $final --original $src --validate true
& $py "$skill/scripts/office/validate.py" $final
& $py "$skill/scripts/office/validate.py" $final --original $src
& $py '.codex_tmp/evidence-report-revision/verify_report_docx.py' `
  --stage revised-final --doc $final
```

The already-defined `revised-final` mode requires `rId27`, `docPr=69`, exactly one figure 5-1 caption, and an embedded media hash identical to `reports/figures/figure-5-1-playback-keyframes.png`.

Expected: all DOCX checks pass.

- [ ] **Step 6: Repeat the complete render QA**

Run Task 10 against the final-named report with `-ExpectedTables 5 -ExpectedInlineShapes 11`. Expected Word metadata changes from pre-frame QA only by one inline shape and any explainable page-count increase. Inspect every page again; do not inspect only the new page.

Expected: zero structural or visual defects and unchanged retained-baseline hash.

- [ ] **Step 7: Commit final frame evidence and final report**

```powershell
git add -- reports/evidence/playback/frames.json `
  reports/evidence/playback/frame-*.png `
  reports/figures/figure-5-1-playback-keyframes.png `
  reports/figures/manifest.json `
  'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究_证据型完整修订.docx'
git diff --cached --check
git commit -m "docs: complete report with real playback evidence"
```

Expected: the final commit includes only user-provided real frames, their manifest/collage, the updated asset manifest, and the final-named DOCX. The retained baseline and pre-frame copy remain available.

---

## Final Verification Checklist

- [ ] `python -m pytest tests/test_bgmm_promp.py -q -p no:cacheprovider` reports `5 passed`.
- [ ] `python -m pytest -q -p no:cacheprovider` passes all current tests and records the actual total.
- [ ] `python -m ruff check src tests` passes.
- [ ] `tests/report_qa_timeout_safety.ps1` passes without bulk process termination.
- [ ] `models/algorithm_metrics.csv`, the Markdown guide, and both DOCX metric tables agree exactly.
- [ ] Figure 2-2 contains a real scene screenshot and a clearly labeled Remote API inventory.
- [ ] Figures 2-1, 2-3, and 3-1 map to current source symbols and parameters.
- [ ] The pre-frame DOCX contains no figure 5-1 placeholder and remains explicitly named `待回放关键帧`.
- [ ] The final-named DOCX exists only after user-confirmed frames are embedded.
- [ ] Word reports one TOC, two sections, and the expected table/inline-shape counts for the relevant stage.
- [ ] PDF page count equals Word's page count; PNG count equals PDF page count.
- [ ] Every page passes visual inspection for Chinese text, layout, images, captions, tables, headers, footers, and page numbers.
- [ ] The retained baseline DOCX SHA-256 is unchanged.
- [ ] No rejected supplemental artifact, `.codex_tmp_source*` file, or generated fake image is staged or committed.
