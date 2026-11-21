---
slug: unclekk-fault-isolation-guard
name: unclekk-fault-isolation-guard
displayName: UncleKK 多 Agent 故障隔离护栏
version: 1.1.0
summary: >-
  多 Agent 系统"告警之后"的选择性在线故障隔离护栏：树状权限边界 + append-only 来源 DAG → 前向隔离受污染执行、后向溯源根因，默认全隔离档、可选 fence-then-prune 最小割档，尽量保住健康工作。 | Post-alert selective online fault containment for multi-agent systems: tree authority boundaries + append-only provenance DAG, forward-isolate tainted executions and backward-trace root causes, with full-quarantine and fence-then-prune min-cut tiers.
description: >-
  多 Agent 故障隔离护栏。当多 agent 编排（如 DeerFlow 4-agent、agent 编排框架）出现错误跨任务传播，告警已触发、需要在限定爆炸半径的同时保住健康工作、又不想整体回滚时使用。输出三件套：故障隔离配置 + 来源追溯图 + 隔离动作清单，并附一个可跑的最小仿真验证。只做"告警之后的隔离与工作保留"，不做告警检测本身（那是检测层），不是通用安全闸，不做单 agent harness 硬化（那是 SHE）。 | Post-alert selective fault containment for multi-agent orchestration. Use when an error propagates across tasks, an alert has fired, and you need to bound the blast radius while preserving healthy work instead of rolling back everything. Outputs isolation config + provenance trace + isolation action list, plus a runnable minimal simulation. Does alert detection itself? No. Not a general safety gate, not single-agent harness hardening (SHE).
license: MIT
---

# unclekk-fault-isolation-guard（多 Agent 故障隔离护栏）

## Overview
把 Airlock 的"告警后选择性故障隔离"做成 MAS 编排可挂载的运行时护栏。核心思想（论文原话）：运行时权限边界（垂直）与在线来源（水平）协同设计，实现"外科手术式故障隔离而不牺牲健康工作"。

Transform Airlock's post-alert selective containment into a pluggable MAS runtime guardrail. Core idea (paper's words): co-designing runtime authority boundaries (vertical) with online provenance (horizontal) enables surgical fault containment without sacrificing healthy work.

## 何时使用（触发条件）| When to Use (Triggers)
- 多 agent 作用于外部世界（工作流编排、智能家居等），一个 agent 的错误输出在被检测前被下游复用，跨任务扩散
- 告警已触发，需要决定"隔离哪些分支、保留哪些健康工作、如何追溯根因"
- 想补现有护栏栈在"协作期错误传播 / 爆炸半径"上的盲区

**实际调用示例（照着说就能触发）| Trigger examples**：
- 「多 agent 里一个输出错了已告警，要隔离哪些、保留哪些」→ 用：本技能核心场景
- 「错误被下游 agent 复用，怎么追溯影响范围」→ 用：`dag_trace.py` 前向标污染、后向溯源
- 「想给编排框架加个告警后隔离护栏」→ 用：输出三件套可挂宿主 MAS
- 「帮我自动拦截错误 agent / 检测谁出错」→ 部分用/不用：本技能只给建议清单，检测归检测层
- 端到端可跑示例见 `examples/minimal-example.md`；更多场景与资料导航见 `examples/more-examples.md`

🔴 **CHECKPOINT**: 开工前必须确认三件事：① agent 树/权限边界可定义；② 跨 agent 数据消费可被记录成来源 DAG；③ 有可信告警来源。缺任一 → 中止并说明（fail-closed）。

**不适用 | Out of scope**: 不做告警检测本身（那是检测/监控层）；不是通用安全闸；不做单 agent harness 硬化（那是 `unclekk-safety-harness-evolution`）；不把本技能输出当成论文测试床指标的复现。

---

## 三铁律（忠实原著）| Three Iron Rules
1. **只评不改**：每条能力主张可溯源 Airlock 论文三份材料；论文没证明的写"待验证"。
2. **诚实披露**：论文指标（1832/161/24266、+68~96pp、+46pp、零收敛后泄漏）来自论文测试床，**本机未复现**；低星新预印本，不写星标数字，不攀比人气。
3. **统一复验 + fail-closed**：材料冲突、仿真跑不通、权限被写成自动执行、安全审计不过 → 停下报告。

---

## 三个可独立复用的部件 | Three Reusable Components

| 部件 | 作用 | 对应论文概念 | 模板 |
|---|---|---|---|
| 1. 权限树 | 父→子权限收窄，建立节点边界与控制开关 | 树状运行时 EdgeCitadel（垂直维度）| `templates/trust-tree.md` |
| 2. 来源 DAG | append-only 记录跨 agent 数据消费（谁读了谁的输出）| append-only provenance DAG（水平维度）| `templates/provenance-dag.md` |
| 3. 隔离决策 | 告警后前向隔离/后向溯源；全隔离档 vs 最小割档 | 告警后选择性隔离 | `templates/isolation-config.md` + `isolation-action-list.md` |

---

## 工作流 | Workflow

### Step 1：材料核对
读三份材料（论文 raw 摘要 / wiki 编译层 / 中文译稿，以你本机的存放路径为准），交叉核对机制、数字、边界；冲突 → fail-closed。

### Step 2：建模权限树 + 来源 DAG
用 `templates/trust-tree.md` 声明 agent 节点边界与权限收窄；用 `templates/provenance-dag.md` 定义 append-only 消费事件 schema（谁在何时读了谁的输出）。这是隔离追踪的基础数据。

### Step 3：挂告警钩子，定义隔离决策
告警触发后：沿 DAG 前向标出受污染执行与待定动作，后向缩小根因候选。用 `templates/isolation-config.md` 选择隔离档：
- **全隔离档（默认）**：冻结受影响分支，无需 solver；
- **最小割档（可选）**：fence-then-prune 做截止时间感知最小割，最小化连带中断（见 `references/isolation-modes.md`）。
> 说明：权限收窄与动作拦截在本技能中是**配置建议 / 离线仿真**，不是自动执行系统级拦截。

### Step 4：输出三件套
故障隔离配置 + 追溯图 + 隔离动作清单（模板见 templates/）。

### Step 5：最小仿真验证
用 `scripts/simulate_alert.py` + `scripts/dag_trace.py` 跑单 agent 错误注入 → 告警 → 前向隔离污染分支 / 后向溯源根因 / 保住健康工作。明确声明：**这是机制正确性仿真，不是复现论文的 1832 测试床指标**。

### Step 6：安全审计 + 独立复审 + 落库
过 `skills-security-check`（重点看运行期权限与动作拦截，P0 必须 0）→ 换会话独立复审 → 落库回报。

---

## 能力主张溯源（摘要，详见 references/metrics.md 与溯源纪律）

| 能力主张 | 论文出处 | 状态 |
|---|---|---|
| 树状运行时父→子权限收窄建节点边界 | 三材料摘要一致 | 已证明 |
| append-only 来源 DAG 记录跨 agent 消费 | 三材料摘要/核心要点一致 | 已证明 |
| 告警后前向隔离/后向溯源 | 三材料摘要一致 | 已证明 |
| 全隔离档 vs fence-then-prune 最小割档 | 三材料摘要一致 | 已证明 |
| +68~96pp 健康工作、零收敛后泄漏 | 三材料摘要/关键结果一致 | 已证明（论文测试床，本机未复现）|
| 动态拓扑下最小割仍最优 | 译稿诚实边界：需更多分布验证 | **待验证** |
| EdgeCitadel 仓库即论文实现 | 仓库 README 实为 Core+Edge 连接 CLI | **存疑**，以三材料为准（见 repo-discrepancy.md）|

## 局限与边界 | Limitations
单列成段，不藏：最小割在动态拓扑未必最优需更多分布验证；对照基线能力上限限制相对增益绝对意义；仓库与论文机制对应存疑；仿真只证机制正确性非系统 benchmark。详见 `references/metrics.md`、`references/repo-discrepancy.md`。

## 边界声明 | Boundary
SHE（`unclekk-safety-harness-evolution`）管单 agent harness 的四工件自愈护栏；协作期阻断类护栏（概念上如 GUARDIAN，本机无同名实体）管告警前的协作阻断；本技能在告警触发**之后**工作，只决定隔离范围与工作保留，不重复成"又一个通用安全闸"，也不做告警检测、不做单 agent harness 硬化。详见 `references/boundary.md`。

## 安全说明 | Security Note
`scripts/` 均为纯本地文件读写：只读 DAG json、输出隔离清单；不修改真实 agent 权限、不 kill 进程、不 sudo/chmod、不联网。所有"权限收窄""动作拦截"均为配置建议/离线仿真，非自动执行。

## 资源 | Resources
**资料导航（总目录）**：第一次用 → `examples/minimal-example.md`；查问题 → `references/faq.md`；更多场景 → `examples/more-examples.md`；细节按下列分类查。

- `examples/minimal-example.md`（端到端示例：客服编排告警后隔离 + 真实命令/输出 + 误冻失败对照）
- `examples/more-examples.md`（更多场景速查 + 资料导航总目录）
- `examples/data/dag-customer-service.json` / `dag-misfreeze.json`（随包 DAG 数据，可直接复制跑）
- `templates/provenance-dag.md` / `trust-tree.md` / `isolation-config.md` / `isolation-action-list.md`
- `scripts/dag_trace.py`（前向/后向追溯）/ `simulate_alert.py`（最小仿真）
- `references/isolation-modes.md` / `metrics.md` / `repo-discrepancy.md` / `boundary.md` / `faq.md`

## 变更记录 | Changelog
- 1.1.0 (2026-11-20)：应对 SkillHub TRACE 测评（4.5/5）"反模式与FAQ 3.8、缺完整案例/真实结果、实际调用示例不足、无总目录、异常处理弱、开箱即用度低"——① 新增 `references/faq.md`（错误清单/失败情形/反模式/触发示例/FAQ）；② 新增 `examples/minimal-example.md`（端到端 + 真实输出 + 误冻失败对照）、`examples/more-examples.md`（含资料导航总目录 + 4 场景）、`examples/data/*.json`×2；③ 强化两脚本 fail-closed：格式错误友好提示（不再甩 traceback）、缺字段事件告警、注入点/root 不在图中不再假报 PASS、健康节点不在图提示；④ SKILL.md 触发段补实际调用示例、Resources 加总目录并移除内部档案引用。守住边界：最小割仍为配置建议，不夸大自动执行。全部输出真实运行复现。
- 1.0.0 (2026-11-19)：初版，源自 Airlock 论文（arXiv:2611.06727），复用 unclekk-paper2skill 三段式骨架约定。
