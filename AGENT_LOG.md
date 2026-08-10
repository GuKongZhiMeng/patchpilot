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
| 2026-08-10 | T6/T7 | TDD + finishing branch | credential/demo/Web/分发 | 待最终 commit | 不伪造公网部署、PR、CI pass 或学生个人反思 |
| 2026-08-10 | 两阶段 review | requesting-code-review | 独立 reviewer 先查 spec 再查安全/质量 | `docs/CODE_REVIEW.md` | 修复宿主执行 Critical、HITL/Web Important 与 raw 复用 Minor；34 tests Green |

## 流程偏离

- Superpowers 插件在当前 Codex 会话中不可调用；按其公开七步方法组织并留证，但不能声称“插件已触发”。学生应在自己的 Codex 插件市场安装后，把实际调用证据补入本日志。
- 当前环境只有本地仓库，没有 NJU Git 远端和账号，因此 worktree 分支在本地完成，未伪造 PR URL。
- 正式 code review 将以本地确定性测试、diff 自审与独立 subagent 任务审查完成；远端 MR 审查需学生补充。
