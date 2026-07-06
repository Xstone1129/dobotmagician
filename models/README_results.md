# Result Figures

These figures compare demonstration trajectories with learned trajectories for the palletizing task.

## Single-Algorithm Figures

- `learned_trajectory_gmm_gmr_dmp.png`: classic `GMM + GMR + DMP`.
- `learned_trajectory_inc_gmm_gmr_dmp.png`: `Incremental GMM + GMR + DMP`.
- `learned_trajectory_gmm_gmr_segmented_dmp.png`: `GMM + GMR + Segmented DMP`.
- `learned_trajectory_bgmm_gmr_promp.png`: `Bayesian GMM + GMR + ProMP`.

Each single-algorithm figure contains four subplots:

- `X position`: end-effector X coordinate over normalized time.
- `Y position`: end-effector Y coordinate over normalized time.
- `Z position`: end-effector Z coordinate over normalized time.
- `Gripper state`: gripper open/close signal over normalized time.

Line meaning:

- Gray lines: original demonstration trajectories.
- Blue transparent lines: generated sample trajectories when available.
- Red line: learned mean output trajectory.

## Comparison Figure

- `trajectory_comparison.png`: four algorithms plotted together against demonstrations.

Line meaning:

- Gray lines: original demonstration trajectories.
- Colored lines: learned output trajectories from each algorithm.
