# CI/CD 验证记录

## 本地可复现验证

验证日期：2026-08-10（Asia/Shanghai）

| 范围 | 命令 | 结果 |
|---|---|---|
| Python 单元测试 | `python -m unittest discover -s tests -v` | 34 passed，2 条 Windows 无符号链接权限条件跳过 |
| mock 机制演示 | `python -m patchpilot demo` | 通过，输出确定性 JSON 事件与安全状态 |
| WebUI 生产构建 | `cd deploy-web && pnpm run build` | 通过，vinext 生成生产 `dist/` |
| WebUI SSR 测试 | `node --test deploy-web/tests/rendered-html.test.mjs` | 1 passed |
| wheel 构建/隔离安装 | `python -m build --wheel` 后在临时 venv 安装并运行 demo | 通过（最终制品哈希在交付重制时更新） |

这些结果证明本机可复现；课程远端 CI 证据见下方 GitHub Actions 记录。

## GitLab 配置兼容性

- 仓库保留课程要求命名的 `.gitlab-ci.yml`。
- Jobs：`unit-test`、`web-unit-test`、`docker-build`。
- 本次课程仓库采用公开 GitHub，因此最终远端运行证据由下方等价 GitHub Actions workflow 提供。

## GitHub Actions 记录

- 仓库：<https://github.com/GuKongZhiMeng/patchpilot>
- 工作流：`.github/workflows/ci.yml`
- Jobs：`unit-test`、`web-unit-test`、`docker-build`
- PR URL：<https://github.com/GuKongZhiMeng/patchpilot/pull/1>
- PR CI 状态：`PASS`（commit `19d3328`，3/3 checks passed）
- 合并状态：`MERGED`（merge commit `623285f`，学生于 2026-08-10 确认合并）
- master workflow：<https://github.com/GuKongZhiMeng/patchpilot/actions/workflows/ci.yml>
- 最终状态：`PASS`（以 workflow 页面最新 `master` run 为准，3/3 jobs passed）

最终交付前已在 GitHub 页面复核最新 `master` workflow 全部通过。

## WebUI 部署记录

- 生产 URL：<https://patchpilot-agent-harness.sturdy-angel-7006.chatgpt.site>
- Sites 生产构建：通过
- 访问范围：public（学生于 2026-08-10 明确授权公开）
- 部署源码：`deploy-web/`，与仓库提交中的已验证源码一致
- 课程评分者访问：可直接使用生产 URL
