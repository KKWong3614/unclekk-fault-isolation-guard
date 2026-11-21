# 与已有护栏栈的边界

> 边界声明必须写进产出 SKILL 的"不适用 | Out of scope"段。本机实体已核对，概念性指代如实标注。

## 本机真实存在的相邻技能

| 技能 | 定位 | 与本技能的关系 |
|---|---|---|
| `unclekk-safety-harness-evolution`（SHE）| 单 agent harness 护栏自愈（四工件 + 测诊改验闭环）| **相邻但不同层**。SHE 硬化单个 agent 的 harness；本技能管多 agent 协作期错误跨任务传播后的隔离。不做 SHE 的工作 |
| `unclekk-metacog-self-evolve` | 规则演化引擎（明确不用于多 Agent 无人监督场景）| 不同用途，不作为对比对象 |
| `unclekk-paper2skill` | 论文→三段式骨架元技能 | **上游**。本技能复用其三段式骨架约定（指令/工具/验证 + 溯源表 + 局限段）|

## 本机无独立实体的概念（按概念指代，不虚构）

- **GUARDIAN 类**（任务书所说"GUARDIAN 类管协作期阻断"）：`C:\Users\Administrator\.workbuddy\skills\` 下无同名技能；检索 guardian/fence/airlock/citadel/isolation/fault 等目录名零命中（paper-topic-scout 中出现的 "GuardianAgentBench" 只是论文候选名，非技能）。它是**概念上的协作期阻断护栏**，本机无实体。
  - 边界写法："协作期阻断类护栏（概念上如 GUARDIAN，本机无同名实体）管告警前的协作阻断"——不虚构一个技能做对比。

## 边界总图（护栏层）

```
告警前 ──> 单 agent harness 护栏：SHE（四工件自愈）
       ──> 协作期阻断：概念上的 GUARDIAN 类（本机无实体）
告警后 ──> 本技能：选择性隔离 + 健康工作保留  ← 只做这一段
```

## 一句话边界声明（可直接粘进 SKILL）
> 本技能只做"告警之后"的选择性隔离与工作保留：前向冻结受污染分支、后向溯源根因、尽量保住健康工作。不做告警检测（检测层），不做单 agent harness 硬化（SHE），不是通用安全闸，也不重复实现协作期阻断（GUARDIAN 类，本机无同名实体）。
