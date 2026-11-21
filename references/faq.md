# 常见问题与反模式（FAQ）

> 针对 SkillHub TRACE 测评（4.5/5）"反模式与FAQ 3.8/5、常见问题未集中说明"补齐。
> 遇到问题先看这里；所有报错都来自真实运行验证（见 `examples/minimal-example.md`）。

## 一、常见错误清单（按报错定位）

| 报错 / 现象 | 原因 | 解决 |
|---|---|---|
| `ERROR: DAG 文件读不到: <path>` | `--dag` 路径不对；Git Bash 下 `/tmp` 被当 `C:\tmp` | 用 Windows 原生 `C:/...` 路径；临时文件别放 `/tmp` |
| `ERROR: DAG 解析失败: ...` | JSON 格式错误（尾逗号、单引号、中文引号）| 用标准双引号 JSON；从 `examples/data/` 复制模板改 |
| `ERROR: DAG 结构不合格: 'events' 必须是数组` | events 不是数组（写成对象/字符串）| 按 `templates/provenance-dag.md` 的 schema，events 为数组 |
| `ERROR: DAG 结构不合格: 顶层必须是 JSON 对象` | 文件顶层是数组或裸值 | 顶层包一层 `{ "events": [...] }` |
| `WARN: N 个事件缺 producer/consumer` + `RESULT: FAIL` | 有事件缺必填字段，来源图不完整 | 补齐每条事件的 `producer`/`consumer`；缺字段不再静默跳过 |
| `FAIL: 注入点 X 不在 DAG 节点集合中` | `--root`/`--inject` 写的 agent_id 在图里不存在 | 检查 id 拼写；确认该节点确实出现在某条事件的 producer/consumer 中。这是 fail-closed，不是脚本 bug |
| `WARN: 该节点不在 DAG 中，KEEP 判定无意义` | `--healthy` 声明的节点不在图里 | 只声明图中真实存在的健康节点；否则 KEEP 结论不成立 |
| `某健康节点: 误冻！` + `RESULT: FAIL` | 声明为健康的节点其实在受污染下游 | 说明隔离策略有问题：要么修正 DAG 记录，要么接受该节点应被冻结；别改脚本 |
| `[forward] ... （无下游）` 但退出码 0 | 该节点确实是叶子（无下游消费者）| 正常；若本应有下游却显示无，检查 DAG 是否漏记消费事件 |

## 二、失败情形（脚本什么时候会停下）

1. **格式/结构错误**：退出码 2，友好报错并指向 `templates/provenance-dag.md`。
2. **fail-closed**（退出码 1）：DAG 为空、事件缺字段、root/inject 不在图中、健康节点被误冻或不在图中 → 一律 `RESULT: FAIL`，不得据此做隔离决策。
3. **PHANTOM PASS 已消除**：v1.0.0 曾出现"注入点不在图中却报 PASS"的假阳性，v1.1.0 起注入点不在图直接 FAIL。
4. **健康误冻**：`simulate_alert.py` 发现声明的健康节点落在污染分支 → FAIL，提示调整策略。

## 三、反模式（别这么做）

| 反模式 | 为什么错 | 正确做法 |
|---|---|---|
| 把本技能输出当成"已自动隔离" | 本技能只输出建议清单，不改真实权限/不 kill 进程 | 把三件套交给宿主 MAS 执行；本技能是决策层不是执行层 |
| 用不完整/手改的 DAG 直接决策 | append-only 图缺事件 → 前向漏标、隔离范围错误 | 事件必须齐全；脚本已对缺字段 fail-closed |
| root/inject 写个猜测的 id 就跑 | 不在图中会得到空结果，旧版还会误报 PASS | 确认 id 在图中；脚本现在会 FAIL 拦截 |
| 最小割档当成"自动最优隔离" | 论文只证明在特定测试床最优，动态拓扑待验证 | 最小割是**配置建议 + 离线仿真**，见 `references/isolation-modes.md` |
| 拿本技能做告警检测 | 本技能在告警**之后**工作 | 告警检测归检测/监控层；见 `references/boundary.md` |
| 拿本技能做单 agent harness 硬化 | 那是 SHE 的职责 | 转 `unclekk-safety-harness-evolution` |
| 把论文指标（+68~96pp 等）当本机实测 | 那些是论文测试床指标，本机未复现 | 诚实标注证据范围；本机脚本只证机制正确性 |

## 四、触发示例（测评"触发方式 4.5：实际调用示例不够丰富"）

不知道该不该用时，对照这几句真实需求：

- 「多 agent 编排里一个 agent 输出错了，已经告警，我要隔离哪些、保留哪些」→ 用：本技能核心场景。
- 「错误在被检测前已被下游 agent 复用，怎么追溯影响范围」→ 用：跑 `dag_trace.py` 前向标污染、后向溯源。
- 「想给编排框架加个告警后的隔离护栏」→ 用：输出三件套可直接挂到宿主 MAS。
- 「我想部署自动拦截错误 agent」→ **部分用**：本技能给隔离建议清单，自动执行要宿主系统做。
- 「帮我检测哪个 agent 出错了」→ **不用**，那是告警检测层，本技能在告警后工作。
- 「加固单个 agent 的 harness」→ **不用**，那是 `unclekk-safety-harness-evolution`。

实际命令与输出见 `examples/minimal-example.md`、`examples/more-examples.md`。

## 五、FAQ

**Q：脚本会修改我的 agent 权限或冻结进程吗？**
A：不会。`scripts/` 只读 DAG json、只向 stdout 打印，不改权限、不 kill 进程、不联网、不执行生成代码。所有"权限收窄/动作拦截"均为配置建议 / 离线仿真。

**Q：最小割档（fence-then-prune）能直接替我算出最优隔离方案吗？**
A：不能。本技能只给配置建议与边界说明（`references/isolation-modes.md`），不内置 solver，也不自动执行。论文的最小割最优性在动态拓扑下仍**待验证**，不能当普适结论。

**Q：仿真 PASS 是不是证明我的隔离策略在真实系统里有效？**
A：不是。仿真只证"机制正确性"（前向标污染 / 后向溯源 / 健康分支未被误冻），不是复现论文 1832/161/24266 测试床指标，也未在真实 MAS 上验证。

**Q：DAG 事件要记到什么粒度？**
A：记跨 agent 的每次数据消费（谁在何时读了谁的输出），schema 见 `templates/provenance-dag.md`。只追加不改历史（append-only）。图越完整，追溯越可信；缺事件会 fail-closed。

**Q：EdgeCitadel 仓库能当论文实现直接用吗？**
A：存疑。仓库 README 实为 Core+Edge 连接 CLI，未直接体现论文机制（来源 DAG / 告警隔离 / 最小割）。能力主张只以三份论文材料为准，见 `references/repo-discrepancy.md`。

**Q：示例里的 agent 名（researcher/drafter 等）是真实实验吗？**
A：不是——是我构造的低风险演示数据，用来展示机制（真实运行输出见 `examples/`）。论文真实指标属测试床，本机未复现。
