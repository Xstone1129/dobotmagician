# Science Education Report and Handoff Documentation Design

**Date**: 2026-07-10
**Status**: Approved design

## Goal

Produce two complementary deliverables for the current Dobot Magician project:

1. A formal Word report for the college, based on last year's report template.
2. A Markdown handoff and reproduction guide for the next science education team.

The two documents have separate responsibilities. The Word report presents the
research work and evidence. The Markdown guide explains how a beginner can run,
understand, troubleshoot, and extend the project.

## Confirmed Research Scope

The documents must describe the implemented project accurately:

- Validation is performed in CoppeliaSim only. No real Dobot Magician hardware
  experiment has been completed in the current project.
- The simulation uses a simplified free-moving Dobot gripper, not the complete
  robot arm. It does not contain inverse kinematics or full arm control.
- The task is a single-place pick, carry, and release sequence. It is not a 2x3
  palletizing experiment and does not implement obstacle avoidance.
- Training uses eight synthetic demonstrations with columns
  `t,x,y,z,gripper`. Each current trajectory contains 150 time steps.
- Four implemented pipelines are compared:
  - GMM + GMR + DMP
  - Incremental GMM + GMR + DMP
  - GMM + GMR + Segmented DMP
  - Bayesian GMM + GMR + ProMP
- The simulator attaches and releases the block through gripper thresholds and
  object parenting. This is deterministic logic rather than contact-physics
  grasping.
- The existing test suite contains five tests and currently passes completely.

Claims about real-hardware validation, complete robot motion, physical grasping,
multi-target palletizing, obstacle avoidance, or mature probabilistic sampling
must not appear as completed results.

## Evidence Sources

### Project Evidence

- Source code under `src/dobot_bgmm_promp/`
- Runtime configuration in `configs/default.yaml`
- Demonstrations in `data/demos_single_place/`
- Saved models and figures under `models/`
- Simplified simulation scene at `scenes/gripper_palletizing.ttt`
- Automated tests in `tests/test_bgmm_promp.py`

### Retained Word Template

Reference document:

`C:\Users\Administrator\OneDrive\文档\科教\许斯烔科教报告.docx`

The retained document remains unchanged. It controls the new report's A4 page
system, cover, assessment tables, contents page, header/footer treatment,
section arrangement, and general visual character.

### Defense Materials

Reference directory:

`C:\Users\Administrator\OneDrive\文档\科教\Xstone答辩材料2026_07_06`

Use the following materials as result evidence:

- Four simulation videos, one per algorithm
- Four single-algorithm trajectory figures
- `各算法对比.png`
- `皮尔逊系数表.csv`

The supplied CSV agrees with the current repository metrics. The key result is
that GMM + GMR + Segmented DMP performs best, with mean Pearson correlation
0.9934 and mean RMSE 0.0139. BGMM + GMR + ProMP ranks second, with mean Pearson
correlation 0.9867 and mean RMSE 0.0205.

## Deliverable 1: Formal Word Report

### Working Title

《基于 GMM-GMR 运动基元的 Dobot Magician 夹爪码垛轨迹学习仿真研究》

### Narrative Positioning

The report is a continuation of last year's work. It briefly identifies the
previous hardware connection, data acquisition, and DMP study as the project
foundation, then focuses on this year's simulation platform, four-algorithm
extension, quantitative comparison, and reproducible results.

The previous report is a formatting and continuity reference, not a source for
copying outdated claims. The current report must clearly distinguish last
year's work from work completed in the present project.

### Structure

1. Cover and assessment pages
   - Retain the college name, course-report identity, individual-project
     selection, division/score table, and assessment table.
   - Replace the project title and update only user-confirmed personal or course
     metadata. Unknown metadata remains unchanged or is left as a clear field;
     it must not be invented.
2. Table of contents
   - Rebuild from real Word heading styles so page numbers can update correctly.
3. Introduction
   - Previous-stage foundation
   - Motivation for simulation validation and algorithm comparison
   - Current objectives and practical significance
4. System and experiment design
   - Software environment and project architecture
   - Simplified CoppeliaSim gripper scene
   - Synthetic demonstration generation
   - `t,x,y,z,gripper` data format
   - Training, evaluation, and playback pipeline
5. Algorithm design
   - Shared GMM/GMR trajectory regression flow
   - GMM + GMR + DMP baseline
   - Incremental GMM + GMR + DMP
   - GMM + GMR + Segmented DMP
   - BGMM + GMR + ProMP
   - Practical differences and implementation boundaries
6. Experimental results and analysis
   - Experimental parameters
   - Four single-algorithm trajectory figures
   - Combined comparison figure
   - Pearson and RMSE table
   - Explanation of why segmented DMP performs best on the current data
   - Discussion of endpoint and gripper-signal differences
7. CoppeliaSim playback validation
   - Scene objects and data flow
   - Gripper-joint control
   - Threshold-based block attachment and release
   - Representative screenshots extracted from the supplied videos
   - Qualitative comparison of the four playback results
8. Project summary, limitations, and future work
   - Completed software and experiment artifacts
   - No real-hardware validation
   - No full robot arm or inverse kinematics
   - No physical contact grasping
   - No multi-place palletizing or obstacle avoidance
   - Recommended next-stage research sequence
9. References
   - Retain relevant DMP literature and add sources for GMM/GMR, incremental
     learning, Bayesian GMM, ProMP, and CoppeliaSim where used.
10. Appendix
   - Only brief key commands and artifact locations. Detailed operation stays in
     the Markdown guide.

### Figures and Tables

- Use the supplied comparison figure as the main quantitative visual.
- Use the segmented-DMP and BGMM-ProMP figures for detailed discussion.
- Include all four single-algorithm figures if page count and readability allow;
  otherwise move secondary figures to the appendix.
- Include a compact metric table containing per-algorithm mean Pearson and mean
  RMSE, plus per-dimension results when space permits.
- Extract representative still frames from the four MP4 files. The frames must
  show the simulator state clearly and use captions that identify the algorithm.
- Do not insert video files directly into the DOCX.

### Word Fidelity and QA

- Build from a copy of the retained report rather than from a blank generic
  template.
- Preserve the A4 layout, 1.25-inch left/right margins, cover conventions,
  assessment tables, and source-derived header/footer treatment.
- Replace manual heading formatting with real Word heading styles while keeping
  the source's visible hierarchy.
- Preserve the retained reference byte-for-byte.
- Validate the final DOCX structurally and visually inspect every rendered page.
- Check tables, captions, page breaks, image scaling, headers, footers, page
  numbers, and contents-page updates before delivery.

## Deliverable 2: Markdown Handoff and Reproduction Guide

### Working Title

《Dobot Magician 轨迹学习仿真项目接手与复现手册》

### Audience

The reader knows basic Python but is using CoppeliaSim and this repository for
the first time. The guide must not assume knowledge of GMM, GMR, DMP, ProMP,
ZeroMQ, Word-report history, or the repository layout.

### Structure

1. Project status at a glance
   - What currently works
   - What does not yet work
   - What a successful reproduction looks like
2. Concepts in plain language
   - Demonstration trajectory
   - GMM and incremental/Bayesian variants
   - GMR
   - DMP, segmented DMP, and ProMP
3. Repository map
   - Configuration, data, models, scene, source, scripts, tests, and reports
4. Windows environment setup
   - Supported Python version
   - Virtual environment creation
   - Editable installation with development dependencies
   - CoppeliaSim Edu and ZeroMQ Remote API prerequisites
5. Fastest reproduction path
   - Verify installation
   - Run tests
   - Generate or inspect demonstrations
   - Train all four algorithms
   - Read metrics and plots
   - Open the supplied scene
   - Select an active model
   - Replay the trajectory
6. Data and configuration reference
   - CSV columns and units
   - Important `configs/default.yaml` fields
   - Model selection, object paths, thresholds, playback timing, scale, and
     offset
7. How each script works
   - Demonstration generation
   - Learning and metric export
   - Scene creation
   - CoppeliaSim recording
   - Playback
8. Expected outputs
   - Model files
   - Single-model plots
   - Comparison plot
   - Metric CSV/Markdown
   - Simulation videos as visual references
9. Troubleshooting
   - Import or installation failures
   - No CSV demonstrations
   - Missing `gripper` column
   - CoppeliaSim connection failure
   - Incorrect object aliases/paths
   - Gripper joints not moving
   - Block not attaching or releasing
   - Endpoint jumps or poor trajectory fit
10. Known code limitations
    - `record_coppeliasim.py` writes only `t,x,y,z`, while the current training
      configuration requires a `gripper` column.
    - The current place selection contains only one configured target.
    - Several model `sample_trajectories` implementations return repeated mean
      trajectories rather than statistically distinct samples.
    - The simplified scene does not test full-arm feasibility or collisions.
11. Safe extension roadmap
    - First preserve the current reproduction baseline
    - Fix and validate four-dimensional recording
    - Add complete robot-arm IK and collision checks
    - Add multiple place points
    - Add contact-aware grasping
    - Move to real hardware only after simulation safety checks
12. Change checklist
    - Tests to run
    - Plots and metrics to regenerate
    - Scene playback checks
    - Files to avoid committing, including caches and temporary outputs

### Writing Rules

- Use copy-pasteable PowerShell commands.
- Explain the expected result immediately after each important command.
- Use warnings for steps that can confuse a beginner.
- Link every core concept to the exact source file that implements it.
- Prefer short sections, numbered procedures, checklists, and troubleshooting
  tables over long theoretical prose.
- Keep detailed mathematical derivations out of the main flow; include only the
  intuition needed to understand and modify the code.

## Output Locations

Planned final artifacts:

- `reports/基于GMM-GMR运动基元的Dobot Magician夹爪码垛轨迹学习仿真研究.docx`
- `docs/Dobot-Magician轨迹学习仿真项目接手与复现手册.md`

Task-local temporary renders, extracted video frames, PDFs, and template
evidence remain under `.codex_tmp/` and are not final deliverables.

## Verification

Before delivery:

1. Rerun `python -m pytest -q -p no:cacheprovider`.
2. Cross-check all reported metrics against the supplied CSV and repository
   metric files.
3. Confirm all algorithm names, paths, commands, and configuration keys against
   the current code.
4. Validate the DOCX package and inspect every rendered page.
5. Confirm the Markdown commands work from the repository root on Windows.
6. Scan both documents for unsupported claims about hardware, IK, collision
   avoidance, physical grasping, or multi-place palletizing.
7. Ensure the retained report and the user's existing uncommitted workspace
   changes remain untouched.

## Non-Goals

- No code or algorithm changes are part of the documentation task.
- No real-hardware execution is attempted.
- No new experimental metrics are invented.
- No replacement of the user's retained report.
- No direct embedding of MP4 video in the formal Word report.
