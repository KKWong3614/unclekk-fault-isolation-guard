# 树状权限边界模板（Trust Tree）

> 对应 Airlock 论文"tree-structured runtime ... narrows permissions vertically from parent to child agents to establish node boundaries and control switches"（三材料摘要一致）。
> 垂直维度：父→子权限收窄，建立节点边界与控制开关。

## 设计要点（溯源论文）
- **树结构**：agent 按父子关系组织，权限自根向叶逐级收窄（least privilege 沿树传递）。
- **节点边界**：每个 agent 节点有明确的权限集合。
- **控制开关（site switches）**：在隔离点可冻结/恢复分支——这是两档隔离的执行位置。

## YAML 模板（示例）

```yaml
trust_tree:
  root:
    id: "orchestrator"
    permissions: ["delegate", "read_all", "alert"]
    children:
      - id: "agent_A"
        permissions: ["read_a", "write_a"]
        site_switch: true          # 隔离点：可冻结此分支
        children:
          - id: "agent_C"
            permissions: ["read_c"]
            site_switch: true
      - id: "agent_B"
        permissions: ["read_b", "act_b"]
        site_switch: true
```

## 字段定义
| 字段 | 含义 |
|---|---|
| id | agent 节点唯一标识 |
| permissions | 该节点允许的权限集合（子 ⊊ 父）|
| site_switch | 是否为隔离点（可在告警后冻结/恢复）|
| children | 子节点列表（权限须为父的子集）|

## 校验规则
- 子节点权限必须是父节点权限的**真子集**（权限逐级收窄，论文 "narrows permissions vertically"）。
- 每个需要被隔离的分支应有 `site_switch: true`。
- 这是**配置模板**，描述期望的权限边界；本技能不自动向宿主 MAS 下发或强制这些权限（非自动执行）。

## 与来源 DAG 的关系
- 权限树（垂直）定义"谁能做什么"；来源 DAG（水平，见 provenance-dag.md）记录"谁实际消费了谁的输出"。
- 告警后隔离 = 在权限树的 site_switch 上，按来源 DAG 的前向污染范围执行冻结（见 isolation-config.md）。
