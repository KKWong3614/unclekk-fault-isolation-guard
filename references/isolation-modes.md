# 隔离模式：全隔离档 vs 优化切档

> 两者均来自 Airlock 论文摘要（三材料一致）：
> - "a default full quarantine tier freezes affected branches without a solver"
> - "an assured optimized cut tier uses fence-then-prune to enforce a deadline-aware minimum cut minimizing collateral disruption"

## 全隔离档（Full Quarantine，默认）
- **机制**：告警后冻结来源 DAG 前向可达的全部受影响分支。
- **无需 solver**：论文明确 "without a solver"，实现简单、结果确定。
- **代价**：可能冻结较多健康分支（连带中断大）。
- **适用**：需要快速确定性冻结、无优化器环境、污染范围本身就不大。

## 优化切档（Optimized Cut，可选）
- **机制**：fence-then-prune，执行截止时间感知（deadline-aware）的最小割，目标是最小化连带中断（minimizing collateral disruption）。
- **论文报告**：密集扩散下比全隔离多保留 +46pp 健康工作——**论文测试床结果，本机未复现**。
- **代价 / 边界**：需要 solver；"最小割在动态拓扑下未必最优，需更多分布验证"（译稿诚实边界）→ **待验证**。
- **适用**：密集扩散场景、有明确截止时间、希望尽量保住健康工作、具备 solver。

## 选择判据（决策表）
| 条件 | 推荐档 |
|---|---|
| 无 solver / 需确定性快速冻结 / 污染范围小 | 全隔离档 |
| 密集扩散 / 有截止时间 / 有 solver / 想保健康工作 | 优化切档（标注"待验证"）|

## 诚实披露
- 两档的"健康工作保留"数字均来自论文测试床（1832 测试床 + 161 物理智能家居 + 24266 仿真记录），**本机未复现**，引用时必须标注。
- 对照基线（A2A / LangGraph 原生控制）的能力上限限制"相对增益"绝对意义（译稿诚实边界）。
- 本技能提供的是两档的**配置与决策模板**，不含 solver 实现；最小割的具体算法实现留给宿主 MAS。
