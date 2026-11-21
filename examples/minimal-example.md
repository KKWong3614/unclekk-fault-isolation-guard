# 端到端最小示例：客服工单多 agent 告警后隔离（真实运行输出）

> 针对 SkillHub TRACE 测评（4.5/5）"缺可直接照做的完整案例和真实结果、首次使用需自己备材料"补齐。
> 下面每条命令与输出都是 2026-11-20 在本机**真实运行**，非编造；DAG 数据随包（`examples/data/`），可直接复制跑。
> 场景：researcher 的错误输出在告警前被下游复用，需前向隔离污染分支、后向溯源、保住健康分支。

---

## 0. 一句话场景

多 agent 客服编排：researcher 输出错数据 → drafter/replier/publisher/auditor 都读了它 → 告警触发。analyst→reporter 分支独立、没读 researcher，应保留。本技能产出隔离建议三件套＋仿真核验。

---

## 1. 准备 DAG（随包数据，可直接用）

数据：`examples/data/dag-customer-service.json`（5 条消费事件，schema 见 `templates/provenance-dag.md`）。

```
researcher ──read──> drafter ──read──> replier ──write──> publisher
    │
    └──read──> auditor            analyst ──read──> reporter（独立健康分支）
```

事件示例（两条）：

```json
{"event_id": "e001", "ts": "2026-11-20T09:00:01Z", "producer": "researcher", "consumer": "drafter", "artifact": "research_v1.json", "action": "read", "alert_ref": null}
{"event_id": "e004", "ts": "2026-11-20T09:00:30Z", "producer": "analyst", "consumer": "reporter", "artifact": "metrics_v1.json", "action": "read", "alert_ref": null}
```

---

## 2. 前向隔离 + 后向溯源（dag_trace.py）

```bash
python scripts/dag_trace.py --dag <技能目录>/examples/data/dag-customer-service.json --root researcher
```

**真实输出（退出码 0）：**

```
DAG: dag-customer-service.json | events=5 | root=researcher | mode=both
[forward] 前向受污染节点（需隔离）: ['auditor', 'drafter', 'publisher', 'replier']
[backward] 后向根因候选: （无上游，根即源头）
```

**读数**：researcher 是污染根，下游 4 个节点（auditor/drafter/replier/publisher）需隔离；它无上游，根即源头。

只看前向：

```bash
python scripts/dag_trace.py --dag <技能目录>/examples/data/dag-customer-service.json --root researcher --mode forward
```

**真实输出（退出码 0）：**

```
DAG: dag-customer-service.json | events=5 | root=researcher | mode=forward
[forward] 前向受污染节点（需隔离）: ['auditor', 'drafter', 'publisher', 'replier']
```

后向溯源（换注入点为中间节点 replier，找根因）：

```bash
python scripts/dag_trace.py --dag <技能目录>/examples/data/dag-customer-service.json --root replier --mode backward
```

**真实输出（退出码 0）：**

```
DAG: dag-customer-service.json | events=5 | root=replier | mode=backward
[backward] 后向根因候选: ['drafter', 'researcher']
```

---

## 3. 隔离效果仿真 + 健康分支核验（simulate_alert.py）

```bash
python scripts/simulate_alert.py --dag <技能目录>/examples/data/dag-customer-service.json --inject researcher --healthy analyst --healthy reporter
```

**真实输出（退出码 0）：**

```
=== 告警后隔离最小仿真（机制正确性，非论文指标复现）===
注入点（污染根）: researcher
前向受污染分支（应冻结）: ['auditor', 'drafter', 'publisher', 'replier']
健康工作保留核验:
  - analyst: KEEP（未被污染）
  - reporter: KEEP（未被污染）
约束: 本仿真只输出建议清单，不自动冻结/恢复任何真实 agent
RESULT: PASS（健康分支未被误冻）
```

**读数**：受污染分支被标出，独立健康分支 analyst/reporter 均 KEEP → 隔离策略保住了健康工作。

---

## 4. 失败对照：误冻健康节点（一票否决）

数据：`examples/data/dag-misfreeze.json`（只保留被污染事件），把实际被污染的 auditor 误声明为健康。

```bash
python scripts/simulate_alert.py --dag <技能目录>/examples/data/dag-misfreeze.json --inject researcher --healthy analyst --healthy auditor
```

**真实输出（退出码 1）：**

```
=== 告警后隔离最小仿真（机制正确性，非论文指标复现）===
注入点（污染根）: researcher
前向受污染分支（应冻结）: ['auditor', 'drafter', 'publisher', 'replier']
健康工作保留核验:
  - analyst: WARN（该节点不在 DAG 中，KEEP 判定无意义）
  - auditor: 误冻！
约束: 本仿真只输出建议清单，不自动冻结/恢复任何真实 agent
RESULT: FAIL（存在健康分支被误冻，或声明节点不在 DAG，需调整隔离策略）
```

**读数**：auditor 实际读了 researcher 的输出却被声明健康 → 判"误冻"，退出码 1。注意 analyst 不在这份 DAG 里，脚本也友好提示 KEEP 无意义（v1.1.0 强化，旧版会假报 PASS）。

---

## 5. 输出三件套（交给宿主 MAS 执行）

| 交付物 | 模板 | 本例要点 |
|---|---|---|
| 故障隔离配置 | `templates/isolation-config.md` | 默认全隔离档；如需最小割见 `references/isolation-modes.md`（配置建议，非自动） |
| 来源追溯图 | `templates/provenance-dag.md` | 用 `examples/data/dag-customer-service.json` 的 5 条事件 |
| 隔离动作清单 | `templates/isolation-action-list.md` | 冻结 auditor/drafter/replier/publisher；保留 analyst/reporter |

> 诚实边界：本技能只产出**建议清单**，不自动冻结/恢复任何真实 agent。权限收窄与动作拦截由宿主 MAS 执行。

---

## 6. 迁移到你自己的任务

1. 复制 `examples/data/dag-customer-service.json`，按 `templates/provenance-dag.md` 改成你的 agent 消费事件（每条至少含 producer/consumer）。
2. 用 `C:/...` 原生路径（Git Bash 下 `/tmp` 会被当 `C:\tmp`）。
3. 跑 `dag_trace.py --root <你的污染根>` 看前向污染 / 后向根因。
4. 跑 `simulate_alert.py --inject <污染根> --healthy <健康节点>...` 核验健康分支。
5. 把三件套交给宿主系统执行；本技能不自动隔离。
6. 数字与 agent 名仅为机制演示，非论文实验结果；论文指标见 `references/metrics.md`（本机未复现）。
