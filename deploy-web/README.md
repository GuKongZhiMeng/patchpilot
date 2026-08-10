# PatchPilot Delivery WebUI

PatchPilot 的线上交付展示页和确定性机制实验台，基于官方 Sites vinext starter 构建。页面不接收 API key，也不会从浏览器执行真实仓库命令。

## 本地运行

要求 Node.js 22.13+ 与 pnpm 11.16：

```bash
pnpm install --frozen-lockfile
pnpm run dev
```

## 验证

```bash
pnpm run build
node --test tests/rendered-html.test.mjs
```

生产构建输出到 `dist/`。`tests/rendered-html.test.mjs` 会启动生产 SSR worker，检查交付内容可以真实渲染且 starter 占位内容已消失。

## 安全边界

- 所有交互仅在浏览器本地更新演示状态，不调用真实 LLM 或 subprocess。
- 页面不读取、不保存、不显示凭据。
- 真正的 harness 运行必须使用主项目 CLI，并遵守容器隔离与 HITL 审批边界。
- `.openai/hosting.json` 只保存非秘密的 Sites 项目 ID 与资源绑定；发布凭据不会写入仓库。
