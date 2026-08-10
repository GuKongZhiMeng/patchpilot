# MR/PR 记录与完成路径

## 当前可核验证据

GitHub 主仓库：<https://github.com/GuKongZhiMeng/patchpilot>。历史 worktree 分支已推送；新增的 GitHub CI 通过 `feature-github-ci` 分支建立真实 PR。

- PR #1：<https://github.com/GuKongZhiMeng/patchpilot/pull/1>
- 分支：`feature-github-ci → master`
- 远端检查：3/3 passed（Python、WebUI、Docker）
- 人工审阅与合并：学生于 2026-08-10 确认；PR 已合并并关闭
- 合并提交：`623285f`

最终反思与交付整理使用独立分支和真实 PR：

- PR #2：<https://github.com/GuKongZhiMeng/patchpilot/pull/2>
- 分支：`student/reflection → master`
- 内容：学生原始反思回答、明确披露的 AI 事实校验/润色，以及最终交付文档一致性修订
- 检查与合并：以 PR 页面最新 head 的 3 项检查及最终合并状态为准

| 工作分支 | 原始提交 | 集成到 master 的提交 | 内容 |
|---|---|---|---|
| `coldstart-review` | `509ea98` | `b59c78a` | 冷启动规约与协议修订 |
| `feature-feedback` | `1c8e469` | `1002963` | 反馈分类、指纹与熔断 |
| `feature-governance` | `535ef8a` | `e5d5c1d` | 工作区、护栏、审批与工具分发 |

完整 refs 已保存在 `../outputs/PatchPilot-history.bundle`，代码审查结论见 `docs/CODE_REVIEW.md`。这些是过程证据，但不是远端 MR 页面。

## 早期 worktree 的流程说明

冷启动、T2 和 T3 worktree 在远端建立前已经完成，并通过独立集成提交进入 `master`，因此没有各自对应的真实 PR 页面。仓库保留了原始分支、commit、TDD 记录和人工修订映射。项目没有为了满足形式要求而事后创建虚假的回溯性 PR；如果重做，应在 `b59c78a` 后、T1 前建立远端，使每个 worktree 从一开始就走 PR 流程。
