# Spline Demo Documentation Addition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 Word 科教报告和 Markdown 接手手册中补充基于自然三次样条的 Demo 路径生成说明，并加入两张由当前项目代码生成的图表。

**Architecture:** 先用一个任务临时脚本直接调用当前 Demo 生成器的关键点与插值函数，生成两张共享 PNG；再将同一组事实和图片分别增量写入 Markdown 与 Word。Word 通过工作副本完成局部插入，使用 Microsoft Word 更新真实目录并导出 PDF，最后逐页渲染检查后才替换仓库中的正式报告。

**Tech Stack:** Windows PowerShell、Python、NumPy、SciPy、Matplotlib、python-docx、OOXML、Microsoft Word COM、pypdfium2、pytest、Markdown。

## Global Constraints

- 已批准设计为 `docs/superpowers/specs/2026-07-10-spline-demo-documentation-addition-design.md`。
- 必须同时修改 `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx` 和 `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`。
- 永久新增图片仅为 `docs/images/spline-demo-keypoints.png` 和 `docs/images/spline-demo-variants.png`。
- 图片和文字必须以 `src/dobot_algorithms/scripts/generate_palletizing_demos.py` 的当前行为为准。
- 事实值保持为 8 个关键点、150 个采样点、`NOISE_XY = 0.02`、`NOISE_Z = 0.02`、自然三次样条和夹爪值裁剪到 `[0, 1]`。
- 内容保持简短、工程导向，不扩写 GMR、DMP、分段 DMP 或 ProMP 的轨迹生成理论。
- 不修改 Demo 生成算法、默认参数、训练数据、模型、指标、场景或测试。
- 不把合成 Demo 描述成实机拖动示教、实时在线规划或完整机械臂可执行路径。
- 不声称已经完成逆运动学、碰撞检测、避障、接触物理抓取或实机验证。
- 保留 Word 现有封面、考核表、页眉页脚、A4 页面设置、章节内容和后续图号。
- Word 新标题使用现有三级标题样式 `标题 31`，并通过 Microsoft Word 更新真实目录和页码。
- 所有临时脚本、工作副本、PDF 和渲染页放在 `.codex_tmp/spline-demo-docs/`，不得提交。
- `.superpowers/` 仅为已完成的视觉方案预览，不得提交；任务结束时停止其预览服务器并删除该临时目录。
- 只暂存本计划列出的文件，不处理或回退其他工作区改动。

---

## File Structure

**Create**

- `.codex_tmp/spline-demo-docs/generate_figures.py`：调用当前生成器函数并输出两张正式图。
- `.codex_tmp/spline-demo-docs/edit_report.py`：在 Word 工作副本中局部插入三级标题、正文、伪代码和两张图。
- `.codex_tmp/spline-demo-docs/report-working.docx`：目录更新和视觉检查前的 Word 工作副本。
- `.codex_tmp/spline-demo-docs/report.pdf`：Microsoft Word 导出的检查用 PDF。
- `.codex_tmp/spline-demo-docs/rendered/page-*.png`：使用 pypdfium2 生成的逐页检查图。
- `docs/images/spline-demo-keypoints.png`：8 个关键点与自然三次样条路径图。
- `docs/images/spline-demo-variants.png`：扰动生成的多条 Demo 路径图。
- `docs/superpowers/plans/2026-07-10-spline-demo-documentation-addition.md`：本实施计划。

**Modify**

- `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`：新增样条 Demo 小节并顺延 6 章后续小节编号。
- `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`：在 `2.3` 与 `2.4` 之间新增 `2.3.1` 及两张图。

**Read Only**

- `src/dobot_algorithms/scripts/generate_palletizing_demos.py`：关键点、扰动、样条和输出行为依据。
- `docs/superpowers/specs/2026-07-10-spline-demo-documentation-addition-design.md`：批准范围。
- Word 当前正文、样式、目录、页眉页脚和图题格式。

---

### Task 1: Generate the Two Permanent Spline Figures

**Files:**

- Create: `.codex_tmp/spline-demo-docs/generate_figures.py`
- Create: `docs/images/spline-demo-keypoints.png`
- Create: `docs/images/spline-demo-variants.png`
- Read: `src/dobot_algorithms/scripts/generate_palletizing_demos.py`

**Interfaces:**

- Consumes: `_waypoints_for_place(rng) -> tuple[np.ndarray, np.ndarray]` and `_interpolate(pos, gripper) -> tuple[np.ndarray, np.ndarray]` from the current generator.
- Produces: two 300 dpi PNG files used unchanged by both Markdown and Word.

- [ ] **Step 1: Record the current generator facts before drawing**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
@'
from dobot_algorithms.scripts import generate_palletizing_demos as g
print('HOME=', g.HOME)
print('PICK=', g.PICK)
print('PLACE=', g.PLACE)
print('N_TIME_STEPS=', g.N_TIME_STEPS)
print('NOISE_XY=', g.NOISE_XY)
print('NOISE_Z=', g.NOISE_Z)
'@ | python -
```

Expected: values are `(0.0, 0.0, 0.15)`, `(0.20, -0.16, 0.02)`, `(0.34, -0.16)`, `150`, `0.02`, and `0.02`.

- [ ] **Step 2: Write the task-local figure generator**

Create `.codex_tmp/spline-demo-docs/generate_figures.py` with these rules:

```python
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from dobot_algorithms.scripts.generate_palletizing_demos import (
    NOISE_XY,
    NOISE_Z,
    _interpolate,
    _waypoints_for_place,
)

OUT = Path("docs/images")
OUT.mkdir(parents=True, exist_ok=True)
LABELS = ["HOME", "Pre-pick", "PICK", "Lift", "Pre-place", "PLACE", "Leave", "HOME"]


def keypoint_figure() -> None:
    rng = np.random.default_rng(42)
    points, _ = _waypoints_for_place(rng)
    curve, _ = _interpolate(points, np.array([0, 0, 1, 1, 1, 0, 0, 0], dtype=float))

    fig = plt.figure(figsize=(8.2, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(points[:, 0], points[:, 1], points[:, 2], "--", color="#9aa0a6", label="Key-point polyline")
    ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#1565c0", linewidth=2.4, label="Natural cubic spline")
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], color="#d32f2f", s=34, zorder=5)
    for index, (point, label) in enumerate(zip(points, LABELS), start=1):
        ax.text(point[0], point[1], point[2], f"{index} {label}", fontsize=8)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title("Eight key points and the natural cubic-spline Demo path")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT / "spline-demo-keypoints.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def variants_figure() -> None:
    fig = plt.figure(figsize=(8.2, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    for seed in range(8):
        points, gripper = _waypoints_for_place(np.random.default_rng(seed))
        curve, _ = _interpolate(points, gripper)
        ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], linewidth=1.5, alpha=0.72, label=f"Demo {seed + 1}")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(f"Demo variants: XY +/-{NOISE_XY:.2f} m, Z +/-{NOISE_Z:.2f} m")
    ax.legend(ncol=2, fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(OUT / "spline-demo-variants.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    keypoint_figure()
    variants_figure()
```

Expected: the task-local script imports the real project functions instead of copying the interpolation implementation.

- [ ] **Step 3: Generate the PNG files**

Run:

```powershell
$env:MPLBACKEND = 'Agg'
$env:PYTHONDONTWRITEBYTECODE = '1'
python '.codex_tmp/spline-demo-docs/generate_figures.py'
Get-ChildItem 'docs/images/spline-demo-*.png' | Select-Object Name,Length
```

Expected: both PNG files exist and each is larger than 50 KB.

- [ ] **Step 4: Verify image dimensions and inspect both figures**

Run:

```powershell
@'
from PIL import Image
from pathlib import Path
for path in sorted(Path('docs/images').glob('spline-demo-*.png')):
    with Image.open(path) as image:
        print(path.name, image.size, image.mode)
'@ | python -
```

Expected: both images are readable RGB/RGBA PNGs, at least 1800 pixels wide, with no clipped title, legend, axis label, or waypoint annotation. Visually verify that the first image labels all 8 ordered stages; stages 1 and 8 both use HOME and therefore overlap at the same coordinate. The second image contains 8 distinct Demo curves.

- [ ] **Step 5: Commit only the two permanent figures**

```powershell
git add -- 'docs/images/spline-demo-keypoints.png' 'docs/images/spline-demo-variants.png'
git diff --cached --name-only
git commit -m "docs: add spline demo generation figures"
```

Expected: the commit contains the two PNG files only.

---

### Task 2: Add the Spline Demo Section to the Markdown Guide

**Files:**

- Modify: `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md:291`
- Read: `docs/images/spline-demo-keypoints.png`
- Read: `docs/images/spline-demo-variants.png`

**Interfaces:**

- Consumes: the two permanent image paths and verified generator facts from Task 1.
- Produces: a self-contained `6.2 基于三次样条生成 Demo 路径` section; existing sections `6.2` through `6.4` become `6.3` through `6.5`.

- [ ] **Step 1: Insert the new subsection after the current 6.1 explanation**

Insert the following content immediately before the current `### 6.2 安全地试验数据生成器` heading:

```markdown
### 6.2 基于三次样条生成 Demo 路径

当前项目的主要数据准备工作，是把少量动作关键点扩展成可供模型学习的完整 Demo。每条 Demo 先定义 8 个阶段，再使用自然三次样条生成 150 个连续采样点。

| 序号 | 动作阶段 | 夹爪关键状态 |
| ---: | --- | ---: |
| 1 | HOME 起点 | 0 |
| 2 | 取物点上方 | 0 |
| 3 | PICK 取物 | 1 |
| 4 | 抬升 | 1 |
| 5 | 放置点上方 | 1 |
| 6 | PLACE 放置 | 0 |
| 7 | 离开放置点 | 0 |
| 8 | 返回 HOME | 0 |

生成流程如下：

1. 根据 HOME、PICK、PLACE 和抬升高度构造 8 个关键点。
2. 使用 `NOISE_XY` 和 `NOISE_Z` 对取放位置及高度加入小范围随机扰动。
3. 在归一化相位 `[0, 1]` 上使用 `CubicSpline(..., bc_type="natural")` 插值位置和夹爪状态。
4. 将结果采样为 150 个时刻，把夹爪值裁剪到 `[0, 1]`，再输出 `t,x,y,z,gripper` CSV。

```text
定义 8 个动作关键点和夹爪状态
对 PICK、PLACE 和抬升高度加入小范围随机扰动
执行自然三次样条插值
组合 150 个位置与夹爪采样点
输出 t, x, y, z, gripper CSV
```

![8 个动作关键点与自然三次样条生成的平滑路径](images/spline-demo-keypoints.png)

图 6-1 8 个动作关键点与自然三次样条 Demo 路径。虚线表示直接连接关键点的折线，蓝色曲线表示插值后的连续路径。

![关键点扰动生成的多条 Demo 路径](images/spline-demo-variants.png)

图 6-2 由关键点扰动生成的多条 Demo。曲线差异来自 `NOISE_XY = 0.02` 和 `NOISE_Z = 0.02`，不是四种学习算法的输出差异。

| 参数 | 当前值 | 作用 | 修改后重点检查 |
| --- | ---: | --- | --- |
| `N_TIME_STEPS` | 150 | 每条 Demo 的采样点数 | CSV 行数、训练输入长度和回放时长 |
| `NOISE_XY` | 0.02 | 取放点平面位置扰动范围 | 轨迹是否仍位于合理工作区域 |
| `NOISE_Z` | 0.02 | 取放高度和抬升高度扰动范围 | 是否出现穿过台面或抬升不足 |

三次样条的作用是让相邻阶段之间连续过渡，比直接用折线连接关键点更适合生成平滑的示教路径。这里的路径仍是合成数据，没有经过完整机械臂逆运动学、碰撞检测或实机可达性验证。
```

Expected: the section is concise, contains both figures, and does not discuss GMR/DMP/ProMP path-generation theory.

- [ ] **Step 2: Renumber the following section headings**

Apply these exact replacements in chapter 6 only:

```text
### 6.2 安全地试验数据生成器 -> ### 6.3 安全地试验数据生成器
### 6.3 CoppeliaSim 关键对象 -> ### 6.4 CoppeliaSim 关键对象
### 6.4 常用配置项 -> ### 6.5 常用配置项
```

Expected: `rg -n '^### 6\.'` reports `6.1` through `6.5` exactly once and in order.

- [ ] **Step 3: Run Markdown fact and asset checks**

Run:

```powershell
$guide = 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
rg -n "6\.2 基于三次样条|8 个|150|NOISE_XY|NOISE_Z|bc_type=|spline-demo-keypoints|spline-demo-variants" $guide
rg -n "TBD|TODO|待补充|自主规划|已经完成逆运动学|实机验证完成" $guide
Test-Path 'docs/images/spline-demo-keypoints.png'
Test-Path 'docs/images/spline-demo-variants.png'
```

Expected: all required facts and image links appear; the placeholder/prohibited-claim scan prints nothing; both `Test-Path` calls return `True`.

- [ ] **Step 4: Commit only the Markdown guide**

```powershell
git add -- 'docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md'
git diff --cached --check
git commit -m "docs: explain cubic-spline demo generation"
```

Expected: the commit contains only the Markdown guide.

---

### Task 3: Incrementally Add the Same Content to the Word Report

**Files:**

- Create: `.codex_tmp/spline-demo-docs/edit_report.py`
- Create: `.codex_tmp/spline-demo-docs/report-working.docx`
- Modify after QA: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- Read: `docs/images/spline-demo-keypoints.png`
- Read: `docs/images/spline-demo-variants.png`

**Interfaces:**

- Consumes: existing paragraph `2.4 训练、评价与回放流程` as the insertion anchor, existing styles `标题 31` and `Normal`, and the two permanent figures.
- Produces: a Word working copy containing one new third-level heading, short explanatory text, pseudocode, two centered images, and captions `图 2-1`/`图 2-2`.

- [ ] **Step 1: Inspect the report structure and create a protected working copy**

Run:

```powershell
$report = 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
$tmp = '.codex_tmp/spline-demo-docs'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Get-FileHash $report -Algorithm SHA256 | Format-List | Out-File "$tmp/report-before-hash.txt" -Encoding utf8
Copy-Item -LiteralPath $report -Destination "$tmp/report-working.docx" -Force
@'
from docx import Document
doc = Document(r'.codex_tmp/spline-demo-docs/report-working.docx')
print('paragraphs=', len(doc.paragraphs))
print('inline_shapes=', len(doc.inline_shapes))
print('sections=', len(doc.sections))
for index, paragraph in enumerate(doc.paragraphs):
    if paragraph.text.strip() in {'2.3 合成示教轨迹与数据格式', '2.4 训练、评价与回放流程'}:
        print(index, paragraph.style.name, paragraph.text)
'@ | python -
```

Expected: the working copy reports 159 paragraphs, 5 inline shapes, 2 sections; `2.3` and `2.4` use `标题 21`.

- [ ] **Step 2: Write the local Word editing script**

Create `.codex_tmp/spline-demo-docs/edit_report.py` with the following complete implementation:

```python
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


REPORT = Path(".codex_tmp/spline-demo-docs/report-working.docx")
KEYPOINTS = Path("docs/images/spline-demo-keypoints.png")
VARIANTS = Path("docs/images/spline-demo-variants.png")
ANCHOR_TEXT = "2.4 训练、评价与回放流程"
NEW_HEADING = "2.3.1 基于三次样条的 Demo 生成"


def add_text_before(anchor, text: str, style: str = "Normal", *, center: bool = False):
    paragraph = anchor.insert_paragraph_before(style=style)
    paragraph.add_run(text)
    if center:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return paragraph


def add_image_before(anchor, path: Path) -> None:
    paragraph = anchor.insert_paragraph_before(style="Normal")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=Inches(5.75))


def main() -> None:
    if not REPORT.exists():
        raise FileNotFoundError(REPORT)
    for image in (KEYPOINTS, VARIANTS):
        if not image.exists():
            raise FileNotFoundError(image)

    doc = Document(REPORT)
    texts = [paragraph.text.strip() for paragraph in doc.paragraphs]
    if texts.count(ANCHOR_TEXT) != 1:
        raise RuntimeError(f"Expected one insertion anchor, found {texts.count(ANCHOR_TEXT)}")
    if NEW_HEADING in texts:
        raise RuntimeError("Spline Demo section already exists")

    anchor = next(paragraph for paragraph in doc.paragraphs if paragraph.text.strip() == ANCHOR_TEXT)
    add_text_before(anchor, NEW_HEADING, style="标题 31")
    add_text_before(
        anchor,
        "Demo 生成是本项目的数据准备环节。程序先按照 HOME、取物点上方、PICK、抬升、"
        "放置点上方、PLACE、离开放置点和返回 HOME 的顺序定义 8 个动作关键点，并为其"
        "配置夹爪状态 [0,0,1,1,1,0,0,0]。",
    )
    add_text_before(
        anchor,
        "为了得到动作语义一致但形状略有差异的多条示教轨迹，生成器使用 NOISE_XY=0.02 "
        "和 NOISE_Z=0.02 对取放位置及高度加入随机扰动。随后在归一化相位上采用自然边界"
        "三次样条，将 8 个关键点插值为 150 个连续采样点，并把夹爪插值结果限制在 0 到 1 范围内。",
    )
    pseudocode = add_text_before(
        anchor,
        "关键点定义 -> 位置与高度扰动 -> 自然三次样条插值 -> 夹爪值裁剪 -> "
        "输出 t,x,y,z,gripper CSV",
    )
    for run in pseudocode.runs:
        run.font.name = "Consolas"
        run.font.size = Pt(9)
    add_text_before(
        anchor,
        "三次样条使相邻动作阶段之间连续过渡，相比直接使用折线连接关键点，更适合作为"
        "平滑的 Demo 路径。图 2-1 展示关键点与插值路径，图 2-2 展示相同动作结构在随机"
        "扰动下生成的多条 Demo。",
    )
    add_image_before(anchor, KEYPOINTS)
    add_text_before(anchor, "图 2-1 8 个动作关键点与自然三次样条 Demo 路径", center=True)
    add_image_before(anchor, VARIANTS)
    add_text_before(anchor, "图 2-2 关键点扰动生成的多条 Demo 路径", center=True)
    add_text_before(
        anchor,
        "上述路径是用于仿真实验的合成示教数据，没有经过完整机械臂逆运动学、碰撞检测"
        "或实机可达性验证。",
    )
    doc.save(REPORT)


if __name__ == "__main__":
    main()
```

The script must:

1. open only `.codex_tmp/spline-demo-docs/report-working.docx`;
2. find the unique paragraph whose text is `2.4 训练、评价与回放流程`;
3. insert all new elements immediately before that paragraph;
4. use `标题 31` for `2.3.1 基于三次样条的 Demo 生成`;
5. use `Normal` for body text and pseudocode;
6. center both image paragraphs and captions;
7. preserve the original section properties, tables, headers, footers, relationships, and existing images;
8. fail without saving if the anchor is missing, duplicated, or the new heading already exists.

Use this exact body copy:

```text
Demo 生成是本项目的数据准备环节。程序先按照 HOME、取物点上方、PICK、抬升、放置点上方、PLACE、离开放置点和返回 HOME 的顺序定义 8 个动作关键点，并为其配置夹爪状态 [0,0,1,1,1,0,0,0]。

为了得到动作语义一致但形状略有差异的多条示教轨迹，生成器使用 NOISE_XY=0.02 和 NOISE_Z=0.02 对取放位置及高度加入随机扰动。随后在归一化相位上采用自然边界三次样条，将 8 个关键点插值为 150 个连续采样点，并把夹爪插值结果限制在 0 到 1 范围内。

关键点定义 -> 位置与高度扰动 -> 自然三次样条插值 -> 夹爪值裁剪 -> 输出 t,x,y,z,gripper CSV

三次样条使相邻动作阶段之间连续过渡，相比直接使用折线连接关键点，更适合作为平滑的 Demo 路径。图 2-1 展示关键点与插值路径，图 2-2 展示相同动作结构在随机扰动下生成的多条 Demo。

上述路径是用于仿真实验的合成示教数据，没有经过完整机械臂逆运动学、碰撞检测或实机可达性验证。
```

Use these exact captions:

```text
图 2-1 8 个动作关键点与自然三次样条 Demo 路径
图 2-2 关键点扰动生成的多条 Demo 路径
```

Expected: only a local work copy is edited; the tracked report remains unchanged at this step.

- [ ] **Step 3: Run the Word editor and perform structural assertions**

Run:

```powershell
python '.codex_tmp/spline-demo-docs/edit_report.py'
@'
from docx import Document
doc = Document(r'.codex_tmp/spline-demo-docs/report-working.docx')
texts = [p.text.strip() for p in doc.paragraphs]
heading = texts.index('2.3.1 基于三次样条的 Demo 生成')
next_heading = texts.index('2.4 训练、评价与回放流程')
print('new_heading_style=', doc.paragraphs[heading].style.name)
print('new_block_before_2_4=', heading < next_heading)
print('inline_shapes=', len(doc.inline_shapes))
print('sections=', len(doc.sections))
print('tables=', len(doc.tables))
assert doc.paragraphs[heading].style.name == '标题 31'
assert heading < next_heading
assert len(doc.inline_shapes) == 7
assert len(doc.sections) == 2
assert texts.count('2.3.1 基于三次样条的 Demo 生成') == 1
'@ | python -
```

Expected: the new heading appears once before `2.4`, uses `标题 31`, and the inline image count increases from 5 to 7 without changing section count.

- [ ] **Step 4: Update the real TOC and fields with Microsoft Word**

Run:

```powershell
$path = (Resolve-Path '.codex_tmp/spline-demo-docs/report-working.docx').Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($path)
  if ($doc.TablesOfContents.Count -lt 1) { throw 'The report has no real Word table of contents.' }
  for ($i = 1; $i -le $doc.TablesOfContents.Count; $i++) {
    $doc.TablesOfContents.Item($i).Update() | Out-Null
  }
  $doc.Fields.Update() | Out-Null
  $doc.Save()
  $doc.Close()
} finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
```

Expected: Word completes without a repair prompt; the contents page includes `2.3.1 基于三次样条的 Demo 生成` with a page number.

- [ ] **Step 5: Verify Word package integrity before visual QA**

Run:

```powershell
@'
from zipfile import ZipFile, BadZipFile
from docx import Document

path = r'.codex_tmp/spline-demo-docs/report-working.docx'
with ZipFile(path) as package:
    bad = package.testzip()
    print('bad_member=', bad)
    assert bad is None

doc = Document(path)
texts = '\n'.join(p.text for p in doc.paragraphs)
for required in [
    '2.3.1 基于三次样条的 Demo 生成',
    '图 2-1 8 个动作关键点与自然三次样条 Demo 路径',
    '图 2-2 关键点扰动生成的多条 Demo 路径',
    '2.4 训练、评价与回放流程',
]:
    assert required in texts, required
print('docx_structure=ok')
'@ | python -
```

Expected: `bad_member=None` and `docx_structure=ok`.

---

### Task 4: Export, Render, and Inspect Every Word Page

**Files:**

- Read/modify: `.codex_tmp/spline-demo-docs/report-working.docx`
- Create: `.codex_tmp/spline-demo-docs/report.pdf`
- Create: `.codex_tmp/spline-demo-docs/rendered/page-*.png`
- Modify after passing QA: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`

**Interfaces:**

- Consumes: the structurally valid and TOC-updated Word working copy from Task 3.
- Produces: a visually inspected final Word report and a temporary PDF/page-render evidence set.

- [ ] **Step 1: Export the working copy through Microsoft Word**

Run:

```powershell
$docx = (Resolve-Path '.codex_tmp/spline-demo-docs/report-working.docx').Path
$pdf = Join-Path (Resolve-Path '.codex_tmp/spline-demo-docs').Path 'report.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($docx)
  for ($i = 1; $i -le $doc.TablesOfContents.Count; $i++) {
    $doc.TablesOfContents.Item($i).Update() | Out-Null
  }
  $doc.Fields.Update() | Out-Null
  $doc.Save()
  $doc.ExportAsFixedFormat($pdf, 17)
  $doc.Close()
} finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Get-Item $pdf | Select-Object FullName,Length
```

Expected: `report.pdf` exists and is non-empty.

- [ ] **Step 2: Render every PDF page using bundled pypdfium2**

First call `codex_app__load_workspace_dependencies` and use its bundled Python path. Then run this script with that interpreter:

```python
from pathlib import Path
import pypdfium2 as pdfium

source = Path('.codex_tmp/spline-demo-docs/report.pdf')
out = Path('.codex_tmp/spline-demo-docs/rendered')
out.mkdir(parents=True, exist_ok=True)
pdf = pdfium.PdfDocument(source)
for index in range(len(pdf)):
    page = pdf[index]
    image = page.render(scale=2.0).to_pil()
    image.save(out / f'page-{index + 1:03d}.png')
print('page_count=', len(pdf))
```

Expected: one PNG is created for every PDF page and the count is at least the original report page count.

- [ ] **Step 3: Inspect every rendered page at full resolution**

Open each `page-*.png` with the local image viewer and verify:

```text
[ ] Cover and assessment tables are unchanged and readable
[ ] Contents page includes 2.3.1 with a real page number
[ ] No contents entry is clipped or overlaps another line
[ ] 2.3.1 appears between 2.3 and 2.4
[ ] Both spline figures are sharp, centered, and within page margins
[ ] Figure labels, legends, axes, and waypoint annotations are readable
[ ] Figure captions stay with their corresponding images
[ ] No large blank page or accidental page break appears
[ ] Existing chapter 4 figures and captions remain intact
[ ] Existing tables, headers, footers, and page numbers remain intact
[ ] Chinese and English glyphs render correctly
[ ] No text, table, image, or footer is clipped or overlapping
```

Expected: every page passes all applicable checks. Record any failure with its page number in `.codex_tmp/spline-demo-docs/qa-notes.md`.

- [ ] **Step 4: Fix defects and repeat the complete Word render loop**

If any check fails, adjust only the new block in `.codex_tmp/spline-demo-docs/edit_report.py`, recreate the working copy from the tracked report, rerun Tasks 3.3 through 4.3, and do not accept a partial page spot-check.

Expected: the last render has no unresolved QA notes.

- [ ] **Step 5: Replace the tracked report only after QA passes**

Run:

```powershell
Copy-Item -LiteralPath '.codex_tmp/spline-demo-docs/report-working.docx' `
  -Destination 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx' `
  -Force
```

Expected: the tracked Word report is now byte-identical to the inspected working copy.

- [ ] **Step 6: Commit only the final Word report**

```powershell
git add -- 'reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx'
git diff --cached --name-only
git commit -m "docs: add spline demo generation to report"
```

Expected: the commit contains only the final DOCX.

---

### Task 5: Run Cross-Document and Repository Acceptance Checks

**Files:**

- Read: `src/dobot_algorithms/scripts/generate_palletizing_demos.py`
- Read: `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`
- Read: `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- Read: `docs/images/spline-demo-keypoints.png`
- Read: `docs/images/spline-demo-variants.png`

**Interfaces:**

- Consumes: all four permanent changed deliverables.
- Produces: evidence that Word, Markdown, figures, tests, and repository status meet the approved design without staging unrelated files.

- [ ] **Step 1: Compare the key claims in Word, Markdown, and code**

Run:

```powershell
@'
from pathlib import Path
from docx import Document
from dobot_algorithms.scripts import generate_palletizing_demos as g

md = Path('docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md').read_text(encoding='utf-8')
doc = Document('reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx')
word = '\n'.join(p.text for p in doc.paragraphs)

required = ['8 个', '150', 'NOISE_XY', 'NOISE_Z', '自然三次样条']
for term in required:
    print(term, 'md=', term in md, 'word=', term in word)
assert g.N_TIME_STEPS == 150
assert g.NOISE_XY == 0.02
assert g.NOISE_Z == 0.02
assert '2.3.1 基于三次样条的 Demo 生成' in word
assert '### 6.2 基于三次样条生成 Demo 路径' in md
print('cross_document_claims=ok')
'@ | python -
```

Expected: every term is present in both deliverables and `cross_document_claims=ok` is printed.

- [ ] **Step 2: Run the complete automated test suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider
```

Expected: all current tests pass.

- [ ] **Step 3: Audit the final repository diff and prohibited files**

Run:

```powershell
git status --short --branch
git log -5 --oneline
git diff origin/master...HEAD --name-only
git diff --check
```

Expected: permanent changes for this addition are limited to the approved spec/plan, two PNGs, Markdown guide, and Word report. `.codex_tmp/`, `.superpowers/`, PDF files, rendered pages, scripts, caches, data, models, scenes, and algorithm source files are not committed.

- [ ] **Step 4: Stop and remove the temporary visual companion artifacts**

If `.superpowers/brainstorm/spline-demo-20260710/state/server.pid` exists, read that PID and stop only that process after verifying its command line belongs to the visual companion. Then remove `.superpowers/` and `.codex_tmp/spline-demo-docs/` using native PowerShell after resolving both paths under the repository root.

Expected: the two temporary directories are absent and no unrelated process or file is affected.

- [ ] **Step 5: Confirm final status**

Run:

```powershell
git status --short --branch
```

Expected: no task-created untracked files remain. Any remaining changes are pre-existing user changes and are reported without modification.
