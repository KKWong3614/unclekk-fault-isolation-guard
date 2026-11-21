#!/usr/bin/env python3
"""
dag_trace.py — 来源 DAG 前向/后向追溯（unclekk-fault-isolation-guard）

用途：读取一个 append-only 来源 DAG（json），从污染根出发：
  - forward：沿 producer→consumer 找全部下游受污染节点
  - backward：逆向找全部上游根因候选

安全契约（对应 skills-security-check 审计）：
  - 只读一个本地 DAG json 文件；只向 stdout 打印结果，不写任何文件
  - 不联网、不 eval/exec、不 subprocess、不修改任何 agent 权限、不 kill 进程
  - 纯图遍历计算，是离线分析工具，非自动执行引擎

用法：
  python dag_trace.py --dag <dag.json> --root <agent_id> [--mode both|forward|backward]
退出码：0=成功；1=任一 fail-closed 检查未过；2=文件/格式错误

fail-closed 检查（v1.1.0 强化）：DAG 为空、事件格式异常、root 不在图中
→ 一律停下并明确报告，绝不返回"看似正常"的空结果。
"""

import argparse
import json
import sys
from pathlib import Path


def load_dag(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_events(dag):
    """校验并返回 (events, bad_events)。不合法抛出 ValueError 由 main 友好处理。"""
    if not isinstance(dag, dict):
        raise ValueError("DAG 顶层必须是 JSON 对象")
    events = dag.get("events")
    if not isinstance(events, list):
        raise ValueError("'events' 必须是数组")
    bad = []
    for i, e in enumerate(events):
        if not isinstance(e, dict):
            bad.append(f"events[{i}] 不是对象（实际 {type(e).__name__}）")
            continue
        p, c = e.get("producer"), e.get("consumer")
        if not isinstance(p, str) or not p.strip() or not isinstance(c, str) or not c.strip():
            bad.append(f"events[{i}] 缺有效的 producer / consumer")
    return events, bad


def build_graphs(events: list):
    """返回 (forward, backward)：forward[x]=x 的下游消费者集合；backward[x]=x 的上游生产者集合。"""
    forward, backward = {}, {}
    for e in events:
        p, c = e.get("producer"), e.get("consumer")
        if not isinstance(e, dict) or not p or not c:
            continue
        forward.setdefault(p, set()).add(c)
        backward.setdefault(c, set()).add(p)
    return forward, backward


def bfs(start: str, graph: dict) -> set:
    """从 start 出发沿 graph 边做可达性遍历（不含 start 自身）。"""
    seen, queue = set(), [start]
    while queue:
        cur = queue.pop(0)
        for nxt in graph.get(cur, ()):  # noqa: B007
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description="来源 DAG 前向/后向追溯（只读）")
    ap.add_argument("--dag", required=True, help="DAG json 文件路径")
    ap.add_argument("--root", required=True, help="污染根 agent_id")
    ap.add_argument("--mode", default="both", choices=["both", "forward", "backward"])
    args = ap.parse_args()

    path = Path(args.dag)
    if not path.is_file():
        print(f"ERROR: DAG 文件读不到: {path}", file=sys.stderr)
        return 2
    try:
        dag = load_dag(path)
    except (ValueError, OSError) as e:
        print(f"ERROR: DAG 解析失败: {e}", file=sys.stderr)
        return 2
    try:
        events, bad_events = validate_events(dag)
    except ValueError as e:
        print(f"ERROR: DAG 结构不合格: {e}（正确格式见 templates/provenance-dag.md）", file=sys.stderr)
        return 2

    forward, backward = build_graphs(events)
    print(f"DAG: {path.name} | events={len(events)} | root={args.root} | mode={args.mode}")

    failed = False
    if bad_events:
        print(f"WARN: {len(bad_events)} 个事件缺 producer/consumer，已从图中跳过：")
        for msg in bad_events:
            print(f"  - {msg}")
        print("  来源图不完整 → CHECKPOINT: 停止隔离决策")
        failed = True
    if not events:
        print("WARN: DAG 无消费事件，追溯结果不可信 —— CHECKPOINT: 停止隔离决策")
        failed = True

    all_nodes = set(forward) | set(backward)
    if args.root not in all_nodes:
        print(f"FAIL: root={args.root} 不在 DAG 节点集合中 —— 污染根不存在，禁止输出空结果冒充成功")
        failed = True
    else:
        if args.mode in ("both", "forward"):
            tainted = bfs(args.root, forward)
            print(f"[forward] 前向受污染节点（需隔离）: {sorted(tainted) if tainted else '（无下游）'}")

        if args.mode in ("both", "backward"):
            causes = bfs(args.root, backward)
            print(f"[backward] 后向根因候选: {sorted(causes) if causes else '（无上游，根即源头）'}")

    if failed:
        print("RESULT: FAIL（fail-closed，追溯结果不可信，不得据此做隔离决策）")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
