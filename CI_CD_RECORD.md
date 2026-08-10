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

这些结果只能证明本机可复现，不能替代课程远端 CI 的绿色状态。

## GitLab 最终记录（推送 NJU Git 后由学生补全）

- 仓库 URL：`PENDING_NJU_GIT_URL`
- 最终 commit：`PENDING_FINAL_COMMIT`
- Pipeline URL：`PENDING_PIPELINE_URL`
- Pipeline 状态：`PENDING`（必须确认 `unit-test`、`web-unit-test`、`docker-build` 全部 pass）
- 容器镜像 tag：`PENDING_REGISTRY_TAG`
- 容器镜像 digest：`PENDING_IMAGE_DIGEST`
- 证据截图：`PENDING_SCREENSHOT_PATH_OR_LINK`

禁止把本地通过或占位符改写为“远端已通过”。只有 NJU Git 实际 pipeline 的页面和 job 日志可以关闭这一项。
