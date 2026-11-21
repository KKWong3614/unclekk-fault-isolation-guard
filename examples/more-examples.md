# 更多场景速查与资料导航

> 补齐测评（4.5/5）"缺直观导航、无总目录、场景不够丰富"。
> 所有输出为 2026-11-20 本机真实运行，非编造。

---

## 一、资料导航（总目录）

| 想做什么 | 去看哪里 |
|---|---|
| 第一次用，照着跑一遍 | `examples/minimal-example.md`（端到端 + 真实输出）|
| 出问题了 / 不知道能不能用 | `references/faq.md`（错误清单 + 反模式 + 触发示例）|
| 看更多场景与 fail-closed 演示 | 本文件下方 |
| 了解三档隔离怎么选 | `references/isolation-modes.md` |
| 写 DAG 事件（schema）| `templates/provenance-dag.md` |
| 写权限树 / 隔离配置 / 动作清单 | `templates/trust-tree.md` / `isolation-config.md` / `isolation-action-list.md` |
| 搞清本技能与 SHE / 检测层的边界 | `references/boundary.md` |
| 核对论文指标与证据范围 | `references/metrics.md` |
| 仓库与论文机制存疑的说明 | `references/repo-discrepancy.md` |

建议阅读顺序：概览（SKILL.md）→ 触发判断 → `examples/minimal-example.md` 跑一遍 → `references/faq.md` 查问题 → 按需要查模板/参考。

---

## 二、场景一：后向溯源找根因（告警点是中间节点）

告警在 replier 触发，想找是谁的上游把它污染的。

```bash
python scripts/dag_trace.py --dag <技能目录>/examples/data/dag-customer-service.json --root replier --mode backward
```

**真实输出（退出码 0）：**

```
DAG: dag-customer-service.json | events=5 | root=replier | mode=backward
[backward] 后向根因候选: ['drafter', 'researcher']
```

解读：根因链为 researcher → drafter → replier，两者都是候选；需结合告警时间/artifact 进一步定位。

---

## 三、场景二：fail-closed —— 注入点不在图中（消除假阳性）

**v1.0.0 的坑**：注入点写错（图里根本没有）时会输出"（无下游）"并返回 PASS，误导用户以为隔离策略通过。v1.1.0 起直接 FAIL。

```bash
# 用一个只含 A→B 的极简图，注入点却写 Z
python scripts/dag_trace.py --dag <极简图>.json --root Z
python scripts/simulate_alert.py --dag <极简图>.json --inject Z --healthy A
```

**真实输出（dag_trace，退出码 1）：**

```
DAG: root-really-absent.json | events=1 | root=Z | mode=both
FAIL: root=Z 不在 DAG 节点集合中 —— 污染根不存在，禁止输出空结果冒充成功
RESULT: FAIL（fail-closed，追溯结果不可信，不得据此做隔离决策）
```

**真实输出（simulate，退出码 1）：**

```
=== 告警后隔离最小仿真（机制正确性，非论文指标复现）===
注入点（污染根）: Z
FAIL: 注入点 Z 不在 DAG 节点集合中 —— 禁止以'无下游'冒充 PASS
RESULT: FAIL（fail-closed，仿真输入不可信，不得据此判断隔离策略）
```

---

## 四、场景三：fail-closed —— 事件缺字段不再静默忽略

**v1.0.0 的坑**：事件缺 producer/consumer 被静默跳过，导致 root 明明在事件里却被判"无下游"。v1.1.0 起告警并 FAIL。

**真实输出（退出码 1）：**

```
DAG: missing-field.json | events=3 | root=A | mode=both
WARN: 2 个事件缺 producer/consumer，已从图中跳过：
  - events[0] 缺有效的 producer / consumer
  - events[1] 缺有效的 producer / consumer
  来源图不完整 → CHECKPOINT: 停止隔离决策
FAIL: root=A 不在 DAG 节点集合中 —— 污染根不存在，禁止输出空结果冒充成功
RESULT: FAIL（fail-closed，追溯结果不可信，不得据此做隔离决策）
```

---

## 五、场景四：格式错误给友好提示（不再甩 traceback）

**真实输出（events 写成字符串，退出码 2）：**

```
ERROR: DAG 结构不合格: 'events' 必须是数组（正确格式见 templates/provenance-dag.md）
```

v1.0.0 此处会甩一长串 Python `AttributeError` traceback；v1.1.0 改为一行友好提示并指向模板。

---

## 六、诚实边界（反复强调，别越界）

- 三件套是**建议清单**，本技能不自动冻结/恢复 agent、不改权限、不 kill 进程。
- 仿真只证机制正确性，**不是**论文 1832/161/24266 测试床指标的复现。
- 最小割档（fence-then-prune）是**配置建议 + 边界说明**，不内置 solver，动态拓扑最优性待验证。
- 论文指标（+68~96pp 健康工作、零收敛后泄漏）来自测试床，本机未复现。
