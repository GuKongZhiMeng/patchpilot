# PatchPilot

PatchPilot 是一个自己实现主循环的 Coding Agent Harness。它把动作解析、工作区工具、路径/命令护栏、HITL 令牌、SQLite 记忆、确定性验证、失败分类、重复失败熔断和停机判断写成可离线单测的 Python 代码；不依赖 LangChain、AutoGen 等 agent runner。

## 安装

要求 Python 3.11+。

```bash
python -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e ".[secure]"
```

`secure` extra 安装 OS keyring 支持。核心、mock 演示和 WebUI 只用标准库。

## 运行

一键测试（不联网、不需要 key）：

```bash
make test
python -m patchpilot demo
```

启动 WebUI：

```bash
patchpilot serve --host 127.0.0.1 --port 8765
```

浏览 `http://127.0.0.1:8765`。WebUI 是确定性机制实验台；真实 provider 运行从 CLI 发起：

```bash
patchpilot run "修复失败测试" --workspace ./target-repo --model YOUR_MODEL
```

真实运行默认要求 Docker 容器隔离。若在宿主机运行，必须显式加 `--unsafe-local-exec`；这表示你理解测试/构建会执行仓库代码，argv 白名单不是 OS 沙箱。

默认连接 OpenAI-compatible `https://api.openai.com/v1/chat/completions`；兼容供应商用 `--base-url` 指定。模型名必须由使用者显式给出，避免把会变化的默认模型写死。

## API key 安全配置

宿主机推荐 OS keyring。首次真实运行未找到 key 时，PatchPilot 用隐藏输入读取并存入 keyring；状态不回显明文：

```bash
patchpilot key set
patchpilot key status
patchpilot key clear
```

项目不会读取明文 key 环境变量，也不要把 key 写进参数、日志、Git 或 shell history。`.env` 已忽略，但仍是明文，不推荐。

容器使用只读 secret 文件：

```bash
docker run --rm -p 127.0.0.1:8765:8765 patchpilot:local
# 真实 CLI 示例（Linux/macOS）：
docker run --rm -it -v "$PWD:/workspace" -v "$HOME/.secrets/patchpilot:/run/secrets/api_key:ro" \
  patchpilot:local patchpilot run "修复测试" --workspace /workspace --model YOUR_MODEL --secret-file /run/secrets/api_key
```

secret 文件在 POSIX 上必须为 `0600`；Docker secret 通常满足只读挂载。Windows ACL 不等价于 POSIX mode，宿主机应优先 Windows Credential Manager（通过 keyring）。

## 分发

Docker/OCI：

```bash
docker build -t patchpilot:local .
docker run --rm -p 127.0.0.1:8765:8765 patchpilot:local
```

目标平台为 Linux amd64/arm64；多架构发布可用 `docker buildx build --platform linux/amd64,linux/arm64 ...`。镜像以非 root 用户运行。包管理器分发可用 `python -m build` 生成 wheel/sdist（仓库未声称已发布到 PyPI）。

## 目录结构

```text
src/patchpilot/
  engine.py       自实现 agent 主循环与停机
  models.py       严格 Action v1 协议
  tools.py        工具分发与受限 subprocess
  guardrails.py   风险分类与一次性审批
  workspace.py    realpath 路径围栏和原子写
  feedback.py     验证分类、指纹、熔断（主要贡献）
  memory.py       SQLite 记忆与事件
  llm.py          mock 与单次 HTTP 补全端口
  credentials.py  keyring/只读 secret
  web.py          本地 WebUI
tests/            全部离线确定性测试
docs/             TDD 与冷启动证据
```

## 安全边界

- `shell=False`、argv 白名单、路径 realpath 围栏、超时和输出截断降低风险，但只有容器/VM 才提供进程级隔离；真实运行因此默认拒绝宿主执行。
- 允许的 `python`/`git` 等程序自身仍可能执行复杂行为；不可信任务应在一次性容器/VM 中运行。
- WebUI 默认只绑定 loopback，没有多用户认证；若部署公网，必须在认证、TLS、限流的反向代理之后。
- LLM 输出、工具输出和网页输入都视为不可信；key 不进入模型上下文、事件或状态输出。

## 已知限制

- Windows 无管理员权限时无法创建符号链接，因此对应逃逸测试会跳过；绝对路径和 `..` 测试仍运行。
- 首版一次只运行一个 action，不支持并发 agent。
- HITL token 内核已实现和测试；真实 CLI 会显示精确 action 并等待一次性 `y/N` 批准，非交互调用则以 `awaiting_approval` 停机。
- WebUI 展示 mock 机制演示，不从浏览器触发真实代码修改。
- 公网 URL、NJU Git PR 与最终 CI pass 需要课程账号完成，见 `SUBMISSION_CHECKLIST.md`。
- 当前 Windows 验证环境未安装 Docker CLI，因此本地未执行镜像构建；GitLab CI 已配置 `docker-build`，必须在远端确认 pass 后再声称镜像可用。

## 第三方代码与许可

项目实现代码为原创；运行时核心仅用 Python 标准库。可选 `keyring` 遵循其上游许可。开发方法参考 [Superpowers](https://github.com/obra/superpowers)，它不是运行依赖。本项目采用 MIT License。
