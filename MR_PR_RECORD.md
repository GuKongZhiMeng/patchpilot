# MR/PR 记录与完成路径

## 当前可核验证据

GitHub 主仓库：<https://github.com/GuKongZhiMeng/patchpilot>。历史 worktree 分支已推送；新增的 GitHub CI 通过 `feature-github-ci` 分支建立真实 PR。

- PR #1：<https://github.com/GuKongZhiMeng/patchpilot/pull/1>
- 分支：`feature-github-ci → master`
- 远端检查：3/3 passed（Python、WebUI、Docker）
- 人工审阅与合并：待学生确认

| 工作分支 | 原始提交 | 集成到 master 的提交 | 内容 |
|---|---|---|---|
| `coldstart-review` | `509ea98` | `b59c78a` | 冷启动规约与协议修订 |
| `feature-feedback` | `1c8e469` | `1002963` | 反馈分类、指纹与熔断 |
| `feature-governance` | `535ef8a` | `e5d5c1d` | 工作区、护栏、审批与工具分发 |

完整 refs 已保存在 `../outputs/PatchPilot-history.bundle`，代码审查结论见 `docs/CODE_REVIEW.md`。这些是过程证据，但不是远端 MR 页面。

## 推荐的真实 MR 路径

1. 学生本人从当前 `master` 创建 `student/reflection` 分支。
2. 只在该分支完成并校对 `REFLECTION.md`，提交信息注明“student-authored reflection”。
3. 若课程仍要求 MR/PR 与远端 CI，在教师认可的 GitLab 建立空项目，并推送 `master` 与 `student/reflection`。
4. 创建 `student/reflection → master` 的 MR；在描述中链接 `AGENT_LOG.md`、`REFLECTION_WORKSHEET.md` 和测试结果。
5. 等待 MR pipeline 全绿，完成人工 review 后合并。
6. 等待合并后 `master` 的最后一次 pipeline 全绿，把 URL、commit 和截图填入 `CI_CD_RECORD.md`。

若教师网页提交明确豁免远端仓库、MR/PR 或 GitLab pipeline，应保存教师说明；否则“网页可以上传文件”并不自动等于这些评分项被取消。
