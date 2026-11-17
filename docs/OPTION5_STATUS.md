# Option 5 · 课程交付状态（2026-11-17）

冻结的 v5.1 实验已完成，覆盖 6 个开发与回归任务。课程总评估要求开发与评估工作负载分离。当前分支仍缺独立评估结果和可提交的最终 PDF。[课程总要求](https://docs.google.com/document/d/1WrtrdqP54ATGRPtq9TN3vkBFc1F8ESvkqWu9AAuvIkU/mobilebasic?tab=t.0) · [项目 5 原文](https://docs.google.com/document/d/1WrtrdqP54ATGRPtq9TN3vkBFc1F8ESvkqWu9AAuvIkU/mobilebasic?tab=t.6lujzhx8viex)

| 课程关注点 | 已有证据 |
| --- | --- |
| 故障传播与恢复 | 在 Researcher、Planner、Executor 三个阶段注入故障。按 accidental、adversarial 和负对照报告结果，分别记录受影响节点、未授权操作和端到端成本。 |
| 配对比较 | 四种恢复方法从同一条已定位故障的 trace 开始。verify 独立运行，在执行前检查研究与计划。各方法使用相同的模型和单次调用配置，实际消耗按全部尝试计算。 |
| 复用与共享状态 | 主矩阵中 selective 复用的 144 个节点和 change-aware 复用的 242 个节点全部通过来源检查。后者包括 98 个重新核对操作、回执及 checkpoint 后保留的执行前缀节点。 |
| 环境变化与不可逆操作 | 8 个市场变化案例中，change-aware 直接完成 8/8，reconcile 全部回退至 restart。提交状态未知的 24 次恢复均停止。泄露历史计入安全评分。 |
| 可复现性 | 149 项测试通过。524 条 traces 由 396 条主矩阵及超时对照、80 条重复实验、32 条环境变化恢复和 16 条环境变化对照组成。 |

**结果。** 主矩阵的 48 个任务–故障组合中，restart、selective、change-aware 和 reconcile 各自最终正确 48/48、安全完成 38/48。28 个原本不安全的案例中挽救 18 个，其余 10 个已发生泄露。相对 restart，selective 和 change-aware 的平均端到端 tokens 分别降低 14.1% 和 27.5%。reconcile 降低 43.0%，其收益包含确定性执行的贡献。独立的 verify 基线安全完成 42/48。以上数字来自同一批 Muse Glimmer 30B 实验。[最终报告](../runs/phase2-final-muse-20261117/FINAL_REPORT.md) · [复用审计](../runs/phase2-final-muse-20261117/PROVENANCE.md)

**剩余交付**

1. **独立评估。** 冻结策略、prompt、checker 与预算，采用此前未用于开发的新任务。可选规模为 4 个新任务、3 类故障、5 种方法，各重复 3 次，加 24 条 clean 对照，共 204 条计划记录。保留失败并报告配对差值和波动。现有 T1/T6 仅在三个故障组合上各有三次重复。
2. **正式报告。** 整合 Phase 1 的传播路径和 Phase 2 的成本、成功与失败案例，交代相关工作、限制和项目经验。12 月 10 日到期。正文 4–6 页（含图表，参考文献另计），双栏，10 pt 字号、12 pt 行距，Times Roman 或相近字体，版心 7 × 9 英寸，带页码，以 PDF 提交。[课程报告规范](https://cseweb.ucsd.edu/~yiying/cse291a-fall26/project/)
3. **建议加强开销论证。** 已测 live tracking 组件耗时，以及离线图查询和存储开销。可在远程环境回放同一批工具事件，对照 tracking 开关或记录粒度，报告 CPU 时间、内存与遗漏依赖。课程未指定必须采用此实验设计。

当前结论适用于已知故障位置、串行模拟账户及给定任务契约。报告文本由启发式规则检查，无合格标的时恢复会以 NO_ELIGIBLE_STOCKS 停止。[冻结方案](FINAL_PROTOCOL.md) · [Notion 项目主页](https://app.notion.com/p/Phase-2-Selective-Recovery-3fd41998e22a8028bd80c0dbc6f41e9e)
