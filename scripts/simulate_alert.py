#!/usr/bin/env python3
"""
simulate_alert.py — 单 agent 错误注入的最小隔离仿真（unclekk-fault-isolation-guard）

用途：给定一棵 agent 树 + 一个错误注入点，仿真"告警后"的隔离效果：
  - 标出应冻结的受污染分支
  - 给出后向根因候选
  - 核验健康分支未被误冻

这是机制正确性仿真，不是复现 Airlock 论文的 1832/161/24266 测试床指标。

安全契约（对应 skills-security-check 审计）：
  - 只读一个本地 DAG json + 读取命令行参数；只向 stdout 打印，不写文件
  - 不联网、不 eval/exec、不 subprocess、不修改真实 agent 权限、不 kill 进程
  - 纯内存图计算

用法：
  python simulate_alert.py --dag <dag.json> --inject <agent_id> [--healthy <agent_id>]...
退出码：0=健康分支核验通过；1=fail-closed（注入点不在 DAG / 健康分支误冻 / DAG 异常）；2=参数/文件错误

fail-closed 检查（v1.1.0 强化）：注入点不在 DAG、声明的健康节点不在 DAG、
事件格式异常 → 一律停下并 FAIL，绝不以"无下游"冒充 PASS。
"""

import argparse
import json
import sys
from pathlib import Path


def build_forward(events):
    g = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        p, c = e.get("producer"), e.get("consumer")
        if p and c:
            g.setdefault(p, set()).add(c)
    return g


def reachable(start, graph):
    seen, q = set(), [start]
    while q:
        cur = q.pop(0)
        for nxt in graph.get(cur, ()):  # noqa: B007
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description="告警后隔离最小仿真（只读）")
    ap.add_argument("--dag", required=True, help="DAG json 文件路径")
    ap.add_argument("--inject", required=True, help="错误注入的 agent_id（污染根）")
    ap.add_argument("--healthy", action="append", default=[], help="声明应保留的健康 agent_id，可重复")
    args = ap.parse_args()

    path = Path(args.dag)
    if not path.is_file():
        print(f"ERROR: DAG 文件读不到: {path}", file=sys.stderr)
        return 2
    try:
        dag = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        print(f"ERROR: DAG 解析失败: {e}", file=sys.stderr)
        return 2

    if not isinstance(dag, dict):
        print("ERROR: DAG 结构不合格: 顶层必须是 JSON 对象（正确格式见 templates/provenance-dag.md）", file=sys.stderr)
        return 2
    events = dag.get("events")
    if not isinstance(events, list):
        print("ERROR: DAG 结构不合格: 'events' 必须是数组（正确格式见 templates/provenance-dag.md）", file=sys.stderr)
        return 2
    bad_events = [f"events[{i}] 非对象或缺 producer/consumer" for i, e in enumerate(events)
                  if not isinstance(e, dict) or not e.get("producer") or not e.get("consumer")]
    if not events:
        print("FAIL: DAG 无事件，无法仿真 —— CHECKPOINT 停止")
        return 1

    forward = build_forward(events)
    all_nodes = set(forward) | {c for e in events if isinstance(e, dict) for c in [e.get("consumer")] if c}

    print("=== 告警后隔离最小仿真（机制正确性，非论文指标复现）===")
    print(f"注入点（污染根）: {args.inject}")

    failed = False
    if bad_events:
        print(f"WARN: {len(bad_events)} 个事件格式异常，已从图中跳过：")
        for msg in bad_events[:10]:
            print(f"  - {msg}")
        print("  来源图不完整 → CHECKPOINT 停止")
        failed = True

    if args.inject not in all_nodes:
        print(f"FAIL: 注入点 {args.inject} 不在 DAG 节点集合中 —— 禁止以'无下游'冒充 PASS")
        failed = True

    if failed:
        print("RESULT: FAIL（fail-closed，仿真输入不可信，不得据此判断隔离策略）")
        return 1

    tainted = reachable(args.inject, forward)
    print(f"前向受污染分支（应冻结）: {sorted(tainted) if tainted else '（无下游）'}")

    ok = True
    if args.healthy:
        print("健康工作保留核验:")
        for h in args.healthy:
            if h not in all_nodes:
                print(f"  - {h}: WARN（该节点不在 DAG 中，KEEP 判定无意义）")
                ok = False
                continue
            conflict = h in tainted
            verdict = "误冻！" if conflict else "KEEP（未被污染）"
            print(f"  - {h}: {verdict}")
            if conflict:
                ok = False
    else:
        print("健康工作保留核验: 未指定 --healthy，跳过")

    print("约束: 本仿真只输出建议清单，不自动冻结/恢复任何真实 agent")
    if ok:
        print("RESULT: PASS（健康分支未被误冻）")
        return 0
    print("RESULT: FAIL（存在健康分支被误冻，或声明节点不在 DAG，需调整隔离策略）")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
