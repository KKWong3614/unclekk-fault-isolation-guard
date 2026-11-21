# 仓库与论文对应存疑点（repo-discrepancy）

> fail-closed 纪律：核验发现的事实不一致必须单列成档，不粉饰、不调和。

## 存疑事实
- 论文 Airlock (arXiv:2611.06727) 在摘要中给出的代码仓库为 `https://github.com/EdgeCitadelTeam/EdgeCitadel`，论文描述的机制包括：树状运行时 EdgeCitadel、append-only 来源 DAG、告警后前向/后向追踪、全隔离档与 fence-then-prune 最小割档。
- 2026-11-19 实测该仓库真实存在（默认分支 main，Python，低星），但其 README 描述的是 **Core + Edge 的 Agent 连接 CLI 运行时**：`uv tool install edgecitadel`、`edgecitadel install/create/invite/join`、NATS 消息、Plugin（codex/claude-code/pi）、Agent Packages（Gemma / Home Assistant）等。
- README 中**未直接出现**论文所述"来源 DAG / 告警后隔离 / fence-then-prune 最小割"等机制字样。

## 处置（本技能采用的纪律）
1. 本 SKILL 的**全部能力主张以三份论文材料（raw/wiki/译稿）为准**，它们彼此一致。
2. EdgeCitadel 仓库仅作"论文声称的代码地址"旁证，**不引用其 README 作为任何机制证据**。
3. 不宣称"本技能实现/复现了该仓库"，也不宣称"该仓库就是论文完整实现"——对应关系存疑，如实标注。
4. 若未来需要落地具体 solver，须重新核验仓库代码与论文机制的对应关系（当前未做，标"待验证"）。

## 为何单列
任务书三铁律要求"诚实披露"与"fail-closed"：仓库与论文机制对不上是可核验的事实差异，不能为了让技能显得"有真实代码支撑"而含糊带过。单列此档，让复审者与使用者都能看到这个边界。
