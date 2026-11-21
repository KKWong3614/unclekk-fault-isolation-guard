# 隔离策略配置模板（Isolation Config）

> 对应 Airlock 论文的告警后两档隔离（三材料摘要一致）：
> - 全隔离档（默认）："a default full quarantine tier freezes affected branches without a solver"
> - 优化切档："an assured optimized cut tier uses fence-then-prune to enforce a deadline-aware minimum cut minimizing collateral disruption"

## 配置模板

```yaml
isolation_policy:
  alert_id: "ALT-2026-11-19-001"
  trigger_source: "monitor"          # 告警来源（须可信，见 CHECKPOINT）
  mode: "full_quarantine"            # full_quarantine | optimized_cut
  provenance_dag: "path/to/dag.json"
  trust_tree: "path/to/trust_tree.yaml"
  tainted_root: "agent_B"            # 告警指向的污染根

  full_quarantine:
    freeze_all_downstream: true      # 冻结前向全部受影响分支
    use_solver: false                # 无 solver（论文原话）

  optimized_cut:
    algorithm: "fence-then-prune"    # 论文原话
    objective: "deadline-aware minimum cut"
    deadline_ms: 5000
    minimize: "collateral_disruption"
    # 注意：动态拓扑下是否仍最优 = 待验证（论文诚实边界）
```

## 两档选择指引（详见 references/isolation-modes.md）

| 档 | 何时用 | 优点 | 代价 / 边界 |
|---|---|---|---|
| 全隔离档（默认）| 需要快速、确定性地冻结所有受影响分支；无 solver 环境 | 简单、无需优化器 | 可能冻结较多健康分支（连带中断大）|
| 优化切档（可选）| 密集扩散、希望尽量保住健康工作、有明确截止时间 | 论文报告密集扩散下比全隔离多保留 +46pp 健康工作（论文测试床，本机未复现）| 动态拓扑最优性待验证；需 solver |

## 输出约束
- 本配置是**策略描述**，供宿主 MAS 按需执行；本技能不自动下发冻结/恢复指令（非自动执行，避免 P0）。
- 告警来源不可信或 DAG 不完整 → CHECKPOINT 停下，不生成隔离动作清单。
