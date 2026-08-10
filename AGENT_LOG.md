# Agent Log

> 时间为 Asia/Shanghai。只记录实际发生的工作，不补写不存在的会话或 PR。

| 时间 | Task | Superpowers 阶段/技能 | Prompt / context | 输出或 commit | 人工干预与教训 |
|---|---|---|---|---|---|
| 2026-07-29 | 需求核对 | brainstorming（方法参考） | 读取通用/A/B 三份要求，用户授权默认 A | 选择 A、主贡献定为反馈闭环 | 当前会话未安装 Superpowers 插件，未虚构插件调用 |
| 2026-08-10 | SPEC/PLAN | writing-plans（方法参考） | 先规约后代码；任务包含失败测试与验证命令 | `509ea98` | 用户未逐节签字，偏离已在 SPEC_PROCESS 记录 |
| 2026-08-10 | 冷启动 | subagent-driven-development | 无历史 gpt-5.6-terra，仅 SPEC+PLAN；不确定即停止 | 冷启动报告，`b59c78a` | 暴露 7 类协议歧义，补核心协议 v1 |
| 2026-08-10 | T1 | test-driven-development | 先写 action/config/LLM 测试 | Red import error → 8 Green；`3562163` | 用工作区 bundled Python 替代缺失 PATH 命令 |
| 2026-08-10 | T2 | worktree + subagent + TDD | 独立 governance worktree | 6 Green/1 Windows skip；`e5d5c1d` | 合并时修正测试应断言 error code 而非 message |
| 2026-08-10 | T3 | worktree + subagent + TDD | 独立 feedback worktree | 5 Green；`1002963` | 演示后发现耗时字段会破坏指纹，增加归一化回归测试 |
| 2026-08-10 | T4 | TDD | SQLite 隔离、检索、敏感数据拒绝 | 3 Green；`697aa21` | 清除误提交的 pycache 并加入 gitignore |
| 2026-08-10 | T5 | TDD | mock LLM 失败→修复→终检 | 4 Green；`d4f4387` | 同秒同大小 Python 重写触发 pyc 缓存，修正夹具 |
| 2026-08-10 | T6/T7 | TDD + finishing branch | credential/demo/Web/分发 | `0b0d413`、`246e3e2`、`71d512c` | 首版真实宿主执行、HITL 与 WebUI 存在评审缺口；根据 Critical/Important 结论修复，不以“测试已绿”替代安全审查 |
| 2026-08-10 | 两阶段 review | requesting-code-review | 独立 reviewer 先查 spec 再查安全/质量 | `docs/CODE_REVIEW.md` | 修复宿主执行 Critical、HITL/Web Important 与 raw 复用 Minor；34 tests Green |
| 2026-08-10 | 最终交付 | 分发 + Sites 托管 | 构建部署 WebUI、产出源码包/Git bundle/wheel | `19d5010`、`10aaf32`、`1f65783` | Windows 无 WSL、Node 不在 PATH、私有源码推送遇到 sandbox/ownership/过期 token；逐项定位后完成公开部署，未把环境失败误写成代码失败 |
| 2026-08-10 | 远端 CI/PR | finishing-a-development-branch（方法参考） | 公开 GitHub、feature 分支、三项 CI job | PR #1，merge `623285f`，记录 `16f2003` | 学生确认合并；最终 master 的 Python/WebUI/Docker 检查全绿 |
| 2026-08-10 | 个人反思 | 学生原创 + AI 辅助润色 | 学生先回答卡壳、评审、TDD、subagent 与重做问题 | `e24b215`，PR #2 | AI 只据学生原始回答和仓库证据校正事实、整理结构；正文及 PR 保留辅助声明 |

## 流程偏离

- Superpowers 插件在本次开发会话中未安装；项目如实记录对其七步方法的参考，不把普通工具调用冒充插件证据。这是相对课程强制流程的明确偏离。
- T2/T3 与冷启动 worktree 在远端建立之前完成，后来通过独立提交集成到 `master`，因此没有各自对应的真实 PR；分支、原始提交与人工修订映射保存在 `MR_PR_RECORD.md`。补建回溯性 PR 会制造虚假过程证据，所以未这样做。
- 真实远端流程从 `feature-github-ci` 的 PR #1 开始；学生完成人工确认后合并，GitHub Actions 三项检查通过。个人反思通过独立 `student/reflection` 分支提交。
