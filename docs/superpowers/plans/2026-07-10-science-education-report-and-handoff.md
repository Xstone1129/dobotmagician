# Science Education Report and Handoff Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a college-ready Word report and a beginner-friendly Markdown handoff guide that accurately document the current CoppeliaSim-only Dobot Magician trajectory-learning project.

**Architecture:** Use one shared evidence manifest as the factual source for both deliverables. Build the Markdown guide directly from the repository and verified commands, then build the DOCX from a copy of last year's retained report while preserving its page system and assessment pages. Finish with structural validation, Word/PDF page rendering, and a cross-document claim audit.

**Tech Stack:** Windows PowerShell, Python 3.10+, pytest, python-docx/OOXML, Microsoft Word COM automation, bundled Node.js, PDF.js, `@napi-rs/canvas`, local Chrome/Edge, Markdown, CoppeliaSim ZeroMQ Remote API.

## Global Constraints

- The retained report at `C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx` is read-only and must remain byte-for-byte unchanged.
- The defense assets under `C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06` are evidence sources and must not be modified.
- Do not modify algorithm code, configuration, demonstrations, saved models, plots, or the CoppeliaSim scene.
- Do not overwrite or revert any existing uncommitted workspace changes.
- State clearly that the project is CoppeliaSim-only and has no current real-hardware validation.
- State clearly that the scene uses a simplified free-moving gripper, not the complete Dobot arm or inverse kinematics.
- State clearly that the current task uses one place point and deterministic block attachment/release, not 2x3 palletizing, collision avoidance, or contact-physics grasping.
- Report eight synthetic `t,x,y,z,gripper` demonstrations with 150 time steps each only after verifying the current files.
- Use the supplied metrics without alteration: segmented DMP mean Pearson `0.9934`, mean RMSE `0.0139`; BGMM+GMR+ProMP mean Pearson `0.9867`, mean RMSE `0.0205`.
- Final outputs are `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx` and `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`.
- Task-local evidence, browser screenshots, PDFs, renders, and logs stay under `.codex_tmp/science-education-docs/` and are not final deliverables.
- Use the bundled workspace Python, Node.js, and packages for document/PDF work; use the project Python environment only for repository commands and tests.
- Validate the DOCX structurally and inspect every rendered page before delivery.

---

## File Structure

**Create**

- `.codex_tmp/science-education-docs/evidence/manifest.md` - shared, human-readable fact and asset inventory used by both documents.
- `.codex_tmp/science-education-docs/evidence/metrics.csv` - normalized copy of the supplied metric table for QA comparisons.
- `.codex_tmp/science-education-docs/video-frames/*.png` - representative simulator still frames extracted from the four supplied MP4 files.
- `.codex_tmp/science-education-docs/template/artifact.md` - exact template/page/slot contract distilled from last year's report.
- `.codex_tmp/science-education-docs/build_report.py` - task-local builder that edits a working copy of the retained DOCX and preserves unrelated package parts.
- `.codex_tmp/science-education-docs/render_pdf_pages.mjs` - task-local PDF.js renderer for Word-exported PDF pages.
- `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md` - final beginner handoff guide.
- `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx` - final college report.

**Read Only**

- `docs/superpowers/specs/2026-07-10-science-education-report-and-handoff-design.md` - approved requirements.
- `README.md`, `pyproject.toml`, `configs/default.yaml` - installation and runtime behavior.
- `src/dobot_bgmm_promp/**/*.py` - implementation evidence.
- `tests/test_bgmm_promp.py` - automated validation evidence.
- `models/algorithm_metrics.csv`, `models/algorithm_metrics.md`, `models/*.png` - current quantitative results.
- `C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx` - retained Word template.
- `C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06\*` - supplied figures, CSV, and MP4 files.

---

### Task 1: Freeze the Shared Evidence Manifest

**Files:**

- Create: `.codex_tmp/science-education-docs/evidence/manifest.md`
- Create: `.codex_tmp/science-education-docs/evidence/metrics.csv`
- Read: `configs/default.yaml`
- Read: `src/dobot_bgmm_promp/scripts/learn.py`
- Read: `src/dobot_bgmm_promp/gmr_primitives.py`
- Read: `src/dobot_bgmm_promp/scripts/generate_palletizing_demos.py`
- Read: `src/dobot_bgmm_promp/scripts/play_coppeliasim.py`
- Read: `src/dobot_bgmm_promp/coppeliasim_client.py`
- Read: `tests/test_bgmm_promp.py`
- Read: `models/algorithm_metrics.csv`
- Read: `C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06\皮尔逊系数表.csv`

**Interfaces:**

- Consumes: approved design and the current repository state.
- Produces: a single factual contract containing exact algorithm names, data shape, scene scope, test status, metrics, asset paths, and prohibited claims.

- [ ] **Step 1: Record pre-work protection hashes and status**

Run:

```powershell
$tmp = '.codex_tmp/science-education-docs/evidence'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Get-FileHash 'C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx' -Algorithm SHA256 |
  Format-List | Out-File "$tmp\retained-report-hash.txt" -Encoding utf8
git status --short | Out-File "$tmp\git-status-before.txt" -Encoding utf8
```

Expected: both evidence files exist; no repository file is modified by the commands.

- [ ] **Step 2: Verify the current demonstrations**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
@'
from pathlib import Path
import numpy as np

files = sorted(Path('data/demos_single_place').glob('*.csv'))
print('demo_count=', len(files))
for path in files:
    data = np.genfromtxt(path, delimiter=',', names=True)
    print(path.name, len(data), data.dtype.names)
'@ | python -
```

Expected: `demo_count= 8`; every file has 150 rows and fields `('t', 'x', 'y', 'z', 'gripper')`.

- [ ] **Step 3: Verify tests and saved model interfaces**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider
@'
import joblib
from pathlib import Path

for path in sorted(Path('models').glob('*.joblib')):
    model = joblib.load(path)
    trajectory = model.mean_trajectory()
    print(path.name, type(model).__name__, trajectory.shape,
          float(trajectory[:, 3].min()), float(trajectory[:, 3].max()))
'@ | python -
```

Expected: `5 passed`; four saved models report shape `(150, 4)` and gripper limits within `0.0` and `1.0`.

- [ ] **Step 4: Normalize and compare metric sources**

Run:

```powershell
$repo = Import-Csv 'models/algorithm_metrics.csv'
$defense = Import-Csv 'C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06\皮尔逊系数表.csv'
$columns = 'Algorithm ID','Pearson X','Pearson Y','Pearson Z','Pearson Gripper','Pearson Mean',
           'RMSE X','RMSE Y','RMSE Z','RMSE Gripper','RMSE Mean'
Compare-Object ($repo | Select-Object $columns | ConvertTo-Csv -NoTypeInformation) `
               ($defense | Select-Object $columns | ConvertTo-Csv -NoTypeInformation)
$defense | Export-Csv '.codex_tmp/science-education-docs/evidence/metrics.csv' `
  -NoTypeInformation -Encoding utf8
```

Expected: `Compare-Object` prints nothing; normalized `metrics.csv` is created.

- [ ] **Step 5: Write the complete evidence manifest**

Create `.codex_tmp/science-education-docs/evidence/manifest.md` with this exact structure and verified values:

```markdown
# Evidence Manifest

## Scope
- Simulation only: CoppeliaSim, no current real-hardware run.
- Simplified free-moving gripper, no complete arm and no IK.
- Single configured place point: `[0.34, -0.16, 0.006]`.
- Deterministic threshold-based attach/release, not contact-physics grasping.

## Data
- Directory: `data/demos_single_place/`
- Demonstrations: 8
- Rows per demonstration: 150
- Columns: `t,x,y,z,gripper`
- Source: synthetic cubic-spline waypoint generation.

## Algorithms
| ID | Report label | Implementation |
| --- | --- | --- |
| `gmm_gmr_dmp` | GMM+GMR+DMP | `GMMGMRDMP` |
| `inc_gmm_gmr_dmp` | Inc-GMM+GMR+DMP | `IncGMMGMRDMP` |
| `gmm_gmr_segmented_dmp` | GMM+GMR+Segmented DMP | `GMMGMRSegmentedDMP` |
| `bgmm_gmr_promp` | BGMM+GMR+ProMP | `BGMMGMRProMP` |

## Verified Results
| Algorithm | Pearson Mean | RMSE Mean |
| --- | ---: | ---: |
| GMM+GMR+DMP | 0.9392 | 0.0403 |
| Inc-GMM+GMR+DMP | 0.9397 | 0.0398 |
| GMM+GMR+Segmented DMP | 0.9934 | 0.0139 |
| BGMM+GMR+ProMP | 0.9867 | 0.0205 |

## Tests
- Command: `python -m pytest -q -p no:cacheprovider`
- Result: 5 passed.

## Known Limitations
- `record_coppeliasim.py` writes `t,x,y,z` but current training requires `gripper`.
- Only one place point is configured.
- Several sample APIs repeat the mean trajectory rather than drawing distinct stochastic samples.
- No complete-arm feasibility, collision, obstacle-avoidance, or hardware validation.

## Prohibited Completed-Result Claims
- Real Dobot Magician execution.
- Complete robot arm or inverse kinematics.
- 2x3 or multi-target palletizing.
- Contact-physics grasping.
- Obstacle avoidance.
- Fully probabilistic trajectory sampling.
```

Expected: every number and claim maps to a verified code, configuration, test, CSV, or asset.

- [ ] **Step 6: Commit only if permanent files changed**

No commit is expected for Task 1 because all outputs are under `.codex_tmp/`.

---

### Task 2: Prepare Representative Simulation Frames

**Files:**

- Create: `.codex_tmp/science-education-docs/video-review.html`
- Create: `.codex_tmp/science-education-docs/video-frames/bgmm_gmr_promp.png`
- Create: `.codex_tmp/science-education-docs/video-frames/gmm_gmr_dmp.png`
- Create: `.codex_tmp/science-education-docs/video-frames/gmm_gmr_segmented_dmp.png`
- Create: `.codex_tmp/science-education-docs/video-frames/inc_gmm_gmr_dmp.png`
- Read: the four supplied MP4 files.

**Interfaces:**

- Consumes: algorithm-to-video mapping from Task 1.
- Produces: one clear, labeled simulator frame per algorithm for Word-report figures and a visual success reference for the Markdown guide.

- [ ] **Step 1: Create a local video-review page**

Create `.codex_tmp/science-education-docs/video-review.html` with four labeled `<video controls>` elements pointing to the absolute local MP4 paths. Use `file:///C:/...` URLs with URL-encoded Chinese path segments.

Expected: opening the page in Chrome or Edge shows four playable videos with algorithm labels.

- [ ] **Step 2: Open the page in the local browser**

Run:

```powershell
$page = (Resolve-Path '.codex_tmp/science-education-docs/video-review.html').Path
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  -ArgumentList @('--new-window', "file:///$($page -replace '\\','/')")
```

Expected: a browser window opens with the four videos. If Chrome is unavailable, use `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.

- [ ] **Step 3: Capture the four representative states**

For each video, seek to a frame where the gripper and block are both visible and the algorithm has progressed beyond the initial home pose. Prefer the carrying or release phase because it proves both Cartesian playback and gripper/block logic. Save the browser screenshot crop to the corresponding `.codex_tmp/science-education-docs/video-frames/<algorithm>.png` path.

Expected: four PNGs exist, contain the CoppeliaSim scene rather than a black/loading frame, and use consistent crop proportions.

- [ ] **Step 4: Visually inspect each frame**

Open all four PNGs and confirm:

```text
[ ] Gripper is visible
[ ] Block or place marker is visible
[ ] No browser controls cover the simulator image
[ ] No personal desktop content is visible
[ ] Algorithm label can be provided accurately in the report caption
```

Expected: all five checks pass for every PNG; recapture any failing frame.

- [ ] **Step 5: Commit only if permanent files changed**

No commit is expected for Task 2 because all outputs are under `.codex_tmp/`.

---

### Task 3: Write and Verify the Beginner Markdown Handoff Guide

**Files:**

- Create: `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`
- Read: `.codex_tmp/science-education-docs/evidence/manifest.md`
- Read: `README.md`
- Read: `pyproject.toml`
- Read: `configs/default.yaml`
- Read: `src/dobot_bgmm_promp/scripts/*.py`
- Read: `src/dobot_bgmm_promp/*.py`

**Interfaces:**

- Consumes: the frozen evidence manifest and current repository commands.
- Produces: a standalone Windows/PowerShell guide that a Python beginner can follow without reading the Word report.

- [ ] **Step 1: Create the guide skeleton with real headings**

Create the file with these headings in this order:

```markdown
# Dobot Magician 轨迹学习仿真项目接手与复现手册

## 1. 先看这里：当前项目做到什么程度
## 2. 用最少理论理解四种算法
## 3. 项目目录地图
## 4. Windows 环境准备
## 5. 最短复现流程
## 6. 数据格式与配置文件
## 7. 各脚本分别做什么
## 8. 正常运行后会得到什么
## 9. 常见问题排查
## 10. 当前代码的已知限制
## 11. 下一届推荐开发顺序
## 12. 修改后的验收清单
## 附录 A：常用命令速查
```

Expected: `rg -n '^## ' docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md` shows every planned section exactly once.

- [ ] **Step 2: Write the status and beginner concept sections**

Include:

- one prominent statement that the project is simulation-only;
- a short “能做 / 不能做” comparison;
- plain-language explanations of GMM, GMR, DMP, segmented DMP, incremental GMM, BGMM, and ProMP;
- exact links to `src/dobot_bgmm_promp/gmr_primitives.py`, `src/dobot_bgmm_promp/gmr.py`, `src/dobot_bgmm_promp/dmp.py`, and `src/dobot_bgmm_promp/incremental_gmm.py`.

Expected: no formula is required to follow the reproduction procedure; every algorithm name maps to an exact class/file.

- [ ] **Step 3: Write the Windows setup procedure**

Use these copy-pasteable commands:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pytest -q -p no:cacheprovider
```

Immediately after each command block, state the expected evidence: Python `>=3.10`, successful editable install, and `5 passed` for the current checkout.

Expected: a beginner understands where the prompt should be located and how to activate the environment again in a new PowerShell window.

- [ ] **Step 4: Write the shortest reproduction workflow**

Use these commands and describe their outputs:

```powershell
python -m dobot_bgmm_promp.scripts.learn --config configs/default.yaml
python -m dobot_bgmm_promp.scripts.play_coppeliasim --config configs/default.yaml --place-index 1
```

Explain that `model.algorithm: compare` trains all four models and that `model.active_algorithm` selects playback. List all four legal IDs exactly as implemented.

Expected: the reader can identify the four `.joblib` files, four single-model plots, comparison plot, and metric tables.

- [ ] **Step 5: Explain data generation without destroying the current baseline**

Document the generator command only with a fresh output directory:

```powershell
python -m dobot_bgmm_promp.scripts.generate_palletizing_demos `
  --output-dir .codex_tmp/reproduction-demos `
  --n-per-pose 5 `
  --seed 42
```

Add a warning that the generator appends new `demo_XX.csv` files and should not be run against `data/demos_single_place` unless the user intentionally wants to change the experiment set.

Expected: the guide never instructs a beginner to overwrite the verified eight-demo dataset.

- [ ] **Step 6: Document CoppeliaSim setup and playback checks**

Describe:

- opening `scenes/gripper_palletizing.ttt`;
- verifying the ZeroMQ Remote API service/port `23000`;
- checking `GripperBase`, `GripCenter`, both gripper joints, `PalletBlock`, `PickPoint`, and `Place_01`;
- selecting `model.active_algorithm` in `configs/default.yaml`;
- the expected pick, carry, release, and return-to-home sequence.

Expected: the reader knows that playback moves `GripperBase` directly and that block grasp/release is threshold-based.

- [ ] **Step 7: Write the configuration reference and troubleshooting table**

Cover these exact configuration keys:

```text
model.algorithm
model.active_algorithm
coppeliasim.host
coppeliasim.port
coppeliasim.target_path
coppeliasim.tip_path
coppeliasim.left_gripper_joint_path
coppeliasim.right_gripper_joint_path
coppeliasim.block_path
coppeliasim.pick_position
coppeliasim.place_positions
coppeliasim.pickup_threshold
coppeliasim.release_threshold
coppeliasim.playback_dt
coppeliasim.coordinate_scale
coppeliasim.coordinate_offset
```

Include symptom/cause/action rows for missing module, no demos, missing `gripper`, connection refused, object not found, gripper not moving, block not attaching, block not releasing, and endpoint jumps.

Expected: every action cites an exact file, key, object alias, or command.

- [ ] **Step 8: Document limitations and the safe extension roadmap**

State explicitly:

1. fix four-dimensional recording first;
2. preserve the current tests and metric baseline;
3. add full-arm IK and collision checks in simulation;
4. add multiple place points;
5. add physical/contact-aware grasping;
6. move to real hardware only after limits, emergency stop, speed, and workspace checks are defined.

Expected: no section presents unimplemented roadmap items as existing features.

- [ ] **Step 9: Run Markdown content audits**

Run:

```powershell
$guide = 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
rg -n "实机|真实机械臂|逆运动学|IK|2.?x.?3|避障|接触物理|gripper|record_coppeliasim" $guide
rg -n "TBD|TODO|待补充|稍后|类似上文" $guide
rg -n "python -m pytest|scripts.learn|scripts.play_coppeliasim|active_algorithm" $guide
```

Expected: boundary terms appear only in limitations or future work; placeholder scan prints nothing; all required commands are present.

- [ ] **Step 10: Test the non-simulator commands in a temporary environment context**

Run from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider
python -m dobot_bgmm_promp.scripts.generate_palletizing_demos `
  --output-dir .codex_tmp/reproduction-demos `
  --n-per-pose 2 `
  --seed 42
Get-ChildItem '.codex_tmp/reproduction-demos' -Filter *.csv
```

Expected: tests report `5 passed`; two CSV files are generated in the temporary directory with the correct header.

- [ ] **Step 11: Commit the Markdown guide**

```powershell
git add -- 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
git diff --cached --check
git commit -m "docs: add Dobot simulation handoff guide"
```

Expected: the commit contains only the final Markdown guide.

---

### Task 4: Distill the Retained Word Report Template

**Files:**

- Create: `.codex_tmp/science-education-docs/template/artifact.md`
- Create: `.codex_tmp/science-education-docs/template/style-evidence.json`
- Create: `.codex_tmp/science-education-docs/template/package-inventory.csv`
- Read: `C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx`

**Interfaces:**

- Consumes: the retained report and approved report structure.
- Produces: an exact template contract defining page geometry, sections, editable slots, preserved parts, styles, images, tables, and field behavior.

- [ ] **Step 1: Copy the retained report to a task-local reference path**

Run:

```powershell
$templateDir = '.codex_tmp/science-education-docs/template'
New-Item -ItemType Directory -Force -Path $templateDir | Out-Null
Copy-Item -LiteralPath 'C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx' `
  -Destination "$templateDir\reference.docx"
Get-FileHash "$templateDir\reference.docx" -Algorithm SHA256
```

Expected: the hash matches `.codex_tmp/science-education-docs/evidence/retained-report-hash.txt`.

- [ ] **Step 2: Run structural audits with bundled Python**

Run:

```powershell
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$skill = 'C:\Users\Administrator\.codex\plugins\cache\openai-primary-runtime\documents\26.709.11516\skills\documents'
$ref = '.codex_tmp/science-education-docs/template/reference.docx'
& $py "$skill\scripts\section_audit.py" $ref |
  Out-File '.codex_tmp/science-education-docs/template/section-evidence.txt' -Encoding utf8
& $py "$skill\scripts\style_lint.py" $ref `
  --json '.codex_tmp/science-education-docs/template/style-evidence.json'
& $py "$skill\scripts\heading_audit.py" $ref |
  Out-File '.codex_tmp/science-education-docs/template/heading-evidence.txt' -Encoding utf8
& $py "$skill\scripts\images_audit.py" $ref |
  Out-File '.codex_tmp/science-education-docs/template/image-evidence.txt' -Encoding utf8
& $py "$skill\scripts\fields_report.py" $ref |
  Out-File '.codex_tmp/science-education-docs/template/field-evidence.txt' -Encoding utf8
```

Expected: evidence records two A4 portrait sections, 1.25-inch left/right margins, three tables, six images, and PAGE fields.

- [ ] **Step 3: Inventory all package parts and relationships**

Run:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:REFERENCE_DOCX = (Resolve-Path '.codex_tmp/science-education-docs/template/reference.docx').Path
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
@'
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import csv, os

source = Path(os.environ['REFERENCE_DOCX'])
out = source.parent / 'package-inventory.csv'
with ZipFile(source) as zf, out.open('w', newline='', encoding='utf-8-sig') as fh:
    writer = csv.writer(fh)
    writer.writerow(['part', 'size', 'sha256'])
    for name in sorted(zf.namelist()):
        data = zf.read(name)
        writer.writerow([name, len(data), sha256(data).hexdigest()])
'@ | & $py -
```

Expected: `package-inventory.csv` contains every DOCX package part with a stable hash.

- [ ] **Step 4: Write `artifact.md` with exact editable slots**

Document:

- retained path and SHA-256;
- A4 page size, margins, two sections, first-page header behavior;
- cover title, project type, teacher, personal table, assessment table, contents page, body start, references, and appendix as separate slots;
- which cover metadata is preserved unless the user confirms a replacement;
- three source tables and whether each is preserved or rewritten;
- source images and floating anchors that may be replaced;
- PAGE fields and update requirements;
- the body region as replaceable while section/page furniture is preserved;
- all `word/header*.xml`, `word/footer*.xml`, theme, settings, numbering, and relationship parts as preserve-only unless a documented report edit requires them.

Expected: no `TBD`, `TODO`, or unresolved slot remains; every distinct page/section pattern is accounted for.

- [ ] **Step 5: Verify the retained source is unchanged**

Run:

```powershell
Get-FileHash 'C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx' -Algorithm SHA256
```

Expected: the hash still matches the pre-work record.

- [ ] **Step 6: Commit only if permanent files changed**

No commit is expected for Task 4 because all outputs are under `.codex_tmp/`.

---

### Task 5: Build the Formal Word Report from the Retained Template

**Files:**

- Create: `.codex_tmp/science-education-docs/build_report.py`
- Create: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- Read: `.codex_tmp/science-education-docs/template/artifact.md`
- Read: `.codex_tmp/science-education-docs/evidence/manifest.md`
- Read: `.codex_tmp/science-education-docs/video-frames/*.png`
- Read: supplied and repository trajectory figures.

**Interfaces:**

- Consumes: retained template copy, exact slot contract, shared evidence, metric table, and prepared images.
- Produces: a formal DOCX that preserves the original page system but replaces outdated research content with the verified continuation report.

- [ ] **Step 1: Create the report output directory and working copy**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'reports' | Out-Null
Copy-Item '.codex_tmp/science-education-docs/template/reference.docx' `
  '.codex_tmp/science-education-docs/template/report-working.docx'
```

Expected: the retained OneDrive report remains untouched; all editing targets the task-local working copy.

- [ ] **Step 2: Implement the task-local report builder**

Write `.codex_tmp/science-education-docs/build_report.py` using bundled `python-docx` plus targeted OOXML helpers. The script must:

```python
REFERENCE = Path('.codex_tmp/science-education-docs/template/report-working.docx')
OUTPUT = Path('reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx')
TITLE = '基于 GMM-GMR 运动基元的 Dobot Magician 夹爪码垛轨迹学习仿真研究'
```

Implement these named functions so later QA can inspect responsibilities:

```python
def load_template() -> Document: ...
def update_cover(document: Document) -> None: ...
def preserve_assessment_tables(document: Document) -> None: ...
def replace_contents_page(document: Document) -> None: ...
def replace_body(document: Document) -> None: ...
def add_result_table(document: Document) -> None: ...
def add_figure(document: Document, path: Path, caption: str, width_cm: float) -> None: ...
def configure_heading_styles(document: Document) -> None: ...
def set_update_fields(document: Document) -> None: ...
def save_and_validate(document: Document) -> None: ...
```

The builder must preserve cover identity fields and assessment-table cells unless the approved design or current template supplies the value. It must replace the old project title, manual TOC text, and old research body. It must not invent a new teacher, student number, class, score, or date.

Expected: functions have single responsibilities and the script writes only the planned output DOCX.

- [ ] **Step 3: Configure real heading styles and contents fields**

Use built-in `Heading 1`, `Heading 2`, and `Heading 3` styles with source-derived Times New Roman/Chinese-font appearance and outline levels. Insert a real Word TOC field for levels 1-3, and set `w:updateFields` to true so Word refreshes page numbers on open.

Expected: `heading_audit.py` later reports real heading styles; the contents page is not a pasted manual list.

- [ ] **Step 4: Write the continuation narrative**

Populate these report chapters exactly:

```text
1 引言
  1.1 前期项目基础
  1.2 本阶段研究目标与意义
  1.3 本阶段完成的主要任务
2 系统与实验方案设计
  2.1 项目软件架构
  2.2 简化夹爪码垛仿真场景
  2.3 合成示教轨迹与数据格式
  2.4 训练、评价与回放流程
3 四种 GMM-GMR 运动基元方法
  3.1 GMM 与 GMR 轨迹回归
  3.2 GMM+GMR+DMP
  3.3 Inc-GMM+GMR+DMP
  3.4 GMM+GMR+Segmented DMP
  3.5 BGMM+GMR+ProMP
4 实验结果与分析
  4.1 实验参数与评价指标
  4.2 四种算法轨迹结果
  4.3 Pearson 与 RMSE 对比
  4.4 结果讨论
5 CoppeliaSim 回放验证
  5.1 场景对象与控制链路
  5.2 抓取、搬运与释放过程
  5.3 四种算法回放现象
6 项目总结、局限与后续计划
  6.1 已完成成果
  6.2 当前局限
  6.3 下一阶段研究计划
参考文献
附录 关键命令与成果文件
```

Use the exact evidence boundaries from Task 1. Explain last year's hardware/data-acquisition work only as prior foundation; do not reuse last year's obstacle-avoidance claims as current results.

Expected: every completed-result sentence is supported by code, test, metric, plot, scene, or video evidence.

- [ ] **Step 5: Insert result figures and tables**

Use:

- `C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06\各算法对比.png` as the main comparison figure;
- all four supplied single-algorithm PNGs, placing secondary detail figures in the appendix if the main body becomes too dense;
- four prepared video frames for the playback-validation section;
- a metric table with columns `算法`, `Pearson均值`, `RMSE均值`, `主要特点`.

Set images inline, center them, keep captions with figures, and never use floating anchors for newly inserted images.

Expected: no figure extends beyond the 5.77-inch content width implied by the retained margins; captions use a consistent Chinese figure-number format.

- [ ] **Step 6: Write the reference list without unsupported citations**

Include only sources actually discussed in the report: DMP, GMM/GMR, incremental GMM, Bayesian GMM, ProMP, and CoppeliaSim/ZeroMQ documentation. Preserve the three relevant references from last year's report only where they still support the new text.

Expected: every numbered citation appears in the reference list, and every reference is cited in the body.

- [ ] **Step 7: Run the builder**

Run:

```powershell
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py '.codex_tmp/science-education-docs/build_report.py'
Get-Item 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
```

Expected: the DOCX exists, is non-empty, and the script reports the final paragraph/table/image counts.

- [ ] **Step 8: Run structural document audits**

Run:

```powershell
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$skill = 'C:\Users\Administrator\.codex\plugins\cache\openai-primary-runtime\documents\26.709.11516\skills\documents'
$doc = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
& $py "$skill\scripts\section_audit.py" $doc
& $py "$skill\scripts\heading_audit.py" $doc
& $py "$skill\scripts\images_audit.py" $doc
& $py "$skill\scripts\fields_report.py" $doc
& $py "$skill\scripts\a11y_audit.py" $doc `
  --out_json '.codex_tmp/science-education-docs/report-a11y.json'
```

Expected: A4 geometry and two-section page system remain; real heading styles exist; TOC/PAGE fields are present; new images are inline; no critical accessibility error is reported.

- [ ] **Step 9: Compare preserve-only package parts**

Run a task-local package comparison that fails if an unplanned header, footer, theme, section property, or relationship disappears. Allow documented changes only to `word/document.xml`, its image relationships, added media, styles needed for real headings, settings for `w:updateFields`, and content-type entries needed by new images.

Expected: the comparison prints `preserve-only parts unchanged` and lists only expected editable parts as changed.

- [ ] **Step 10: Commit the initial DOCX**

```powershell
git add -- 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
git diff --cached --check
git commit -m "docs: add science education project report"
```

Expected: the commit contains only the initial final-path DOCX.

---

### Task 6: Render and Visually QA Every Word Report Page

**Files:**

- Create: `.codex_tmp/science-education-docs/report-render/report.pdf`
- Create: `.codex_tmp/science-education-docs/report-render/page-*.png`
- Create: `.codex_tmp/science-education-docs/render_pdf_pages.mjs`
- Modify if necessary: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`

**Interfaces:**

- Consumes: structurally valid DOCX from Task 5.
- Produces: a visually inspected DOCX with correct pagination, captions, tables, headers/footers, and no clipping or overlap.

- [ ] **Step 1: Export the DOCX to PDF using Microsoft Word**

Run Word COM automation with a bounded timeout and a dedicated copy of the final DOCX:

```powershell
$doc = (Resolve-Path 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx').Path
$outDir = (New-Item -ItemType Directory -Force -Path '.codex_tmp/science-education-docs/report-render').FullName
$pdf = Join-Path $outDir 'report.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $opened = $word.Documents.Open($doc, $false, $true)
  $opened.Fields.Update() | Out-Null
  $opened.ExportAsFixedFormat($pdf, 17)
  $opened.Close(0)
} finally {
  $word.Quit()
}
Get-Item $pdf
```

Expected: `report.pdf` exists and is non-empty. If Word COM hangs, stop only the automation instance created for this task, then retry once with a copied DOCX in a short ASCII-only temporary path.

- [ ] **Step 2: Implement the PDF.js page renderer**

Write `.codex_tmp/science-education-docs/render_pdf_pages.mjs` using bundled `pdfjs-dist` and `@napi-rs/canvas`. It must accept `input.pdf output_dir scale`, render every page to `page-001.png`, `page-002.png`, and so on, and print the page count.

Expected: the script has no project dependency changes and reads bundled modules via `NODE_PATH` or absolute imports.

- [ ] **Step 3: Render every PDF page to PNG**

Run:

```powershell
$node = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$env:NODE_PATH = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
& $node '.codex_tmp/science-education-docs/render_pdf_pages.mjs' `
  '.codex_tmp/science-education-docs/report-render/report.pdf' `
  '.codex_tmp/science-education-docs/report-render/pages' `
  '1.5'
```

Expected: one PNG exists for every PDF page and the script prints the same page count Word reports.

- [ ] **Step 4: Inspect every rendered page at full resolution**

For every `page-*.png`, check:

```text
[ ] Cover title fits and personal/assessment fields remain aligned
[ ] Contents page has correct hierarchy and no stale page numbers
[ ] Header/footer and page numbers are present where expected
[ ] No text or image clips at page edges
[ ] No figure is split from its caption
[ ] No table row is clipped or pinned against borders
[ ] Chinese and English fonts render correctly
[ ] No large accidental blank area or orphan heading exists
[ ] All four algorithm figures and simulator frames are legible
[ ] References and appendix paginate cleanly
```

Expected: every page passes every applicable check. Record failures in `.codex_tmp/science-education-docs/report-render/qa-notes.md` with page number and exact defect.

- [ ] **Step 5: Fix defects and repeat the render loop**

For any recorded defect, update the task-local builder or final DOCX, rebuild, rerun structural audits, export a fresh PDF to a new iteration directory, and inspect every page again. Do not patch only the PDF.

Expected: the latest iteration has no open QA note.

- [ ] **Step 6: Commit the visually approved DOCX if it changed**

```powershell
git add -- 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
git diff --cached --check
git commit -m "docs: polish science education report layout"
```

Expected: commit only if the DOCX changed after Task 5; otherwise skip the commit.

---

### Task 7: Run Cross-Document Consistency and Final Delivery Checks

**Files:**

- Verify: `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`
- Verify: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- Verify: retained report and defense assets remain unchanged.

**Interfaces:**

- Consumes: visually approved DOCX, tested Markdown guide, and shared evidence manifest.
- Produces: two internally consistent final artifacts with a clean, scoped git diff and verification record.

- [ ] **Step 1: Re-run the repository regression suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider
```

Expected: `5 passed`.

- [ ] **Step 2: Extract the final DOCX text for claim auditing**

Run with bundled Python and `python-docx`, writing only to `.codex_tmp/science-education-docs/final-report-text.txt`. Include paragraphs, table cells, headers, and footers.

Expected: the extracted text contains the report title, all six numbered chapters, references, and appendix.

- [ ] **Step 3: Compare required facts across both deliverables**

Search both the Markdown guide and extracted DOCX text for:

```text
CoppeliaSim
8 条 / 8个 / eight demonstrations
150
t,x,y,z,gripper
GMM+GMR+DMP
Inc-GMM+GMR+DMP
GMM+GMR+Segmented DMP
BGMM+GMR+ProMP
0.9934
0.0139
单个放置点 / single place
未进行实机验证 / no real-hardware validation
```

Expected: both deliverables agree on scope, algorithm names, dataset, best result, and limitations.

- [ ] **Step 4: Scan for prohibited or exaggerated claims**

Run:

```powershell
$guide = 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
$reportText = '.codex_tmp/science-education-docs/final-report-text.txt'
rg -n "已完成实机|真实机械臂实验成功|完成逆运动学|完成2.?x.?3|完成避障|物理接触抓取成功|随机采样轨迹" $guide,$reportText
rg -n "TBD|TODO|XXXX|待补充|占位|placeholder" $guide,$reportText
```

Expected: both scans print nothing.

- [ ] **Step 5: Verify source protection and repository scope**

Run:

```powershell
Get-FileHash 'C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx' -Algorithm SHA256
git status --short
git diff --name-only HEAD~3..HEAD
```

Expected: retained-report hash matches the pre-work hash; final commits contain only the design/plan plus the two requested deliverables; pre-existing user changes remain present and unaltered.

- [ ] **Step 6: Confirm final artifact existence and sizes**

Run:

```powershell
Get-Item `
  'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md', `
  'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx' |
  Select-Object FullName,Length,LastWriteTime
```

Expected: both final files exist, are non-empty, and have current modification times.

- [ ] **Step 7: Commit any final consistency-only edits**

```powershell
git add -- `
  'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md' `
  'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
git diff --cached --check
git commit -m "docs: finalize science education deliverables"
```

Expected: skip this commit if there are no final artifact changes.

---

## Final Acceptance Criteria

- The Markdown guide can be followed by a learner with basic Python knowledge and no prior CoppeliaSim experience.
- Every command in the guide is PowerShell-compatible and names the expected output or failure check.
- The Word report visibly follows last year's retained template and contains a real, updateable heading/contents hierarchy.
- The Word report contains verified trajectory figures, a verified metrics table, and representative simulator frames from all four supplied videos.
- Both documents clearly separate last year's foundation from the current simulation-only results.
- Both documents state current limitations without presenting roadmap work as completed.
- The repository test suite passes with `5 passed`.
- The retained report and all pre-existing user changes remain untouched.
- Every page of the final DOCX has passed PNG visual inspection.
