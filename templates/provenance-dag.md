# 来源 DAG schema（append-only 跨 agent 数据消费记录）

> 对应 Airlock 论文"an append-only provenance DAG records cross-agent data consumption horizontally"（三材料摘要一致）。
> 这是隔离追踪的基础数据：**谁在何时读了谁的输出**。只追加、不修改历史。

## 设计要点（溯源论文）
- **append-only**：事件一旦记录不可改，保证追溯可信（论文原话 "append-only"）。
- **水平维度**：跨越 agent 边界记录数据消费，补上单 agent harness 看不到的跨 agent 数据流。
- **节点 = 数据消费事件**；边 = 数据从 producer 流向 consumer。

## JSON schema（示例）

```json
{
  "dag_version": "1.0",
  "append_only": true,
  "events": [
    {
      "event_id": "e001",
      "ts": "2026-11-19T10:00:01Z",
      "producer": "agent_A",
      "consumer": "agent_B",
      "artifact": "design_v1.json",
      "action": "read",
      "alert_ref": null
    },
    {
      "event_id": "e002",
      "ts": "2026-11-19T10:02:13Z",
      "producer": "agent_B",
      "consumer": "agent_C",
      "artifact": "design_v2.json",
      "action": "read",
      "alert_ref": null
    }
  ]
}
```

## 字段定义
| 字段 | 含义 | 必填 |
|---|---|---|
| event_id | 事件唯一 ID | 是 |
| ts | 时间戳（UTC） | 是 |
| producer | 输出数据的 agent 节点 | 是 |
| consumer | 消费数据的 agent 节点 | 是 |
| artifact | 被消费的数据产物标识 | 是 |
| action | 消费动作（read/write/act 等） | 是 |
| alert_ref | 关联告警 ID（若该消费发生在告警后） | 否 |

## 前向 / 后向追踪语义（对应论文）
- **前向**（forward）：从被污染节点 F 出发，沿 `producer→consumer` 方向找出所有下游消费者与待定动作 → 这些是要隔离的对象。
- **后向**（backward）：从告警点逆向沿边找所有上游 producer → 缩小根因候选。

## 使用约束
- 本 schema 是记录格式模板，不是自动执行引擎。记录动作由宿主 MAS 按需埋点，本技能不自动改写 agent 行为。
- DAG 不完整时前向/后向追踪结果不可信 → CHECKPOINT 停下，不宣称隔离范围正确。
