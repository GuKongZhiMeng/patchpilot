# 最终交付索引

本页把课程清单逐项映射到可核验文件。`已完成`只表示仓库内证据已就绪；涉及学生身份、课程账号或个人观点的项目不会由自动化伪造完成。

| # | 交付项 | 状态 | 仓库证据 / 操作 |
|---|---|---|---|
| 1 | SPEC、PLAN、SPEC_PROCESS | 已完成 | `SPEC.md`、`PLAN.md`、`SPEC_PROCESS.md` |
| 2 | 完整源码与规范提交历史 | 已完成（本地） | `src/`、`tests/`、`deploy-web/`；`git log --oneline --all` |
| 3 | 分发产物 | 已完成 | `Dockerfile`、`pyproject.toml`；最终 wheel、源码 zip、Git bundle 输出到 `../outputs/` |
| 4 | README 必备章节 | 已完成 | `README.md`：项目简介、安装、运行、分发命令、目录结构、安全边界、已知限制 |
| 5 | Agent 日志 | 已完成 | `AGENT_LOG.md`，并由提交历史和 `docs/*_TDD.md` 交叉验证 |
| 6 | GitLab CI，含 unit-test job | 已完成 | `.gitlab-ci.yml`：`unit-test`、`web-unit-test`、`docker-build` |
| 7 | CI/CD 最终通过记录 | 待课程远端确认 | 本地结果见 `CI_CD_RECORD.md`；远端 pipeline URL/截图必须在 NJU Git 实际运行后补入 |
| 8 | 1500–2500 字反思 | 待学生本人完成 | `REFLECTION.md` 只提供证据索引和提纲，遵守“学生本人撰写”要求 |
| 9 | 线上部署 URL 与 WebUI | 已部署（owner-only） | <https://patchpilot-agent-harness.sturdy-angel-7006.chatgpt.site>；源码位于 `deploy-web/`，向评分者共享仍需学生明确批准 |
| A | 自实现 harness 内核 | 已完成 | `src/patchpilot/engine.py`、`models.py`、`tools.py`、`guardrails.py`、`feedback.py`、`memory.py` |
| A | mock-LLM 单元测试 | 已完成 | `tests/test_engine.py` 等离线确定性测试 |
| A | 机制演示 | 已完成 | `python -m patchpilot demo`；部署 WebUI 的交互式机制实验台 |

## 交付前只剩的账号/本人动作

1. 在 NJU Git 创建课程可见仓库并推送全部分支和标签。
2. 建立 MR/PR，保留 subagent 与人工修订说明。
3. 等待 `unit-test`、`web-unit-test`、`docker-build` 全部通过，将 pipeline URL 和截图补入 `CI_CD_RECORD.md`。
4. 学生本人完成并校对 `REFLECTION.md`，确保 1500–2500 字且观点真实。
5. 若课程明确要求 Superpowers 插件调用证据，在 Codex 插件市场安装后真实使用；当前仓库只陈述方法参考，不冒充插件证据。
6. 明确决定站点访问范围；当前为 owner-only，评分者无法以匿名身份访问。

提交前还应执行 `git grep` 与历史扫描，确认无真实 key、token、`.env` 或个人敏感信息。
