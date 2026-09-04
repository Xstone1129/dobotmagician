# Hyperparameter Tuning

使用 `data/demos_suction_turn` 的 8 条带高斯噪声示教轨迹进行两折交叉验证。每折使用一半轨迹训练、另一半验证，时间轴统一归一化到 180 个采样点。参数按验证集平均 RMSE 最小选择；Pearson 相关系数作为同步报告指标（越大越好）。

| Algorithm | Parameters | Folds | Mean RMSE | Mean Pearson |
|---|---|---:|---:|---:|
| gmm_gmr_dmp | n_components=8; dmp_basis=30; dmp_alpha_s=1.0 | 2 | 0.03470883 | 0.91293835 |
| inc_gmm_gmr_dmp | inc_lam=1.0; dmp_basis=80 | 2 | 0.05473871 | 0.86508305 |
| gmm_gmr_segmented_dmp | n_components=8; n_segments=4; dmp_basis=50 | 2 | 0.01859258 | 0.96407012 |
| bgmm_gmr_promp | n_components=6; promp_basis=12; promp_basis_width=0.08 | 2 | 0.04747301 | 0.91947543 |
