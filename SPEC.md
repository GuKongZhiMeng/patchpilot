# PatchPilot 设计规格

## 1. 问题陈述

小型项目维护者需要一种可审计、可离线测试的 coding agent harness：它可以修改限定工作区内的文件、运行验证命令，并依据客观失败信号迭代修复；同时不能把安全寄托于提示词。PatchPilot 面向课程项目、教学仓库和小型内部工具，重点解决“LLM 会提出动作，但谁来确定性地限制、验证并停止它”的问题。

## 2. 用户故事

1. 作为维护者，我希望提交自然语言任务并看到逐步事件，以便理解 agent 做了什么。
2. 作为安全负责人，我希望越界路径和危险命令在执行前被代码拦截，以便避免破坏宿主机。
3. 作为开发者，我希望每次写文件后自动运行验证器，以便让下一轮决策基于客观反馈。
4. 作为评审者，我希望用 scripted mock LLM 重放完整循环，以便不依赖网络验证机制。
5. 作为长期用户，我希望保存项目约定与历史决策，并按任务相关性检索，而非全量塞入上下文。
6. 作为部署者，我希望用 Docker 或本地 Python 一键启动 WebUI，并安全提供自己的 API key。
7. 作为操作者，我希望危险但可批准的动作进入 HITL 状态，并通过一次性审批令牌继续。

## 3. 功能规格

### 3.0 核心协议 v1（规范性）

所有动作是 UTF-8 JSON 对象，统一形式为 `{"action":"名称","args":{...}}`，顶层和 `args` 均拒绝未知字段。`read_file` 参数为 `path:str`；`write_file` 为 `path:str, content:str`；`run_command` 为 `argv:list[str]`；`run_checks` 无参数；`remember` 为 `kind:"convention"|"decision"|"failure", text:str`；`finish` 为 `summary:str`。空 action、非对象、未知名称、缺字段和错误类型分别返回稳定机器码 `invalid_json`、`invalid_action`、`unknown_action`、`missing_argument`、`invalid_argument`。

Python 公共 API：`Action.from_json(text: str) -> Action`；`Config.from_mapping(data: Mapping) -> Config`；`LLMPort.complete(messages: list[dict[str,str]]) -> str`。协议错误统一抛 `PatchPilotError(code, message)`。`ScriptedLLM(responses: list[str])` 每次弹出一个原始响应，把 messages 深拷贝追加到 `calls`；耗尽抛 `llm_script_exhausted`，不可循环。

Config 顶级字段与默认值：`max_steps=12`（1..100）、`command_timeout_seconds=30`（1..300）、`max_output_bytes=16384`（1024..1048576）、`max_file_bytes=1048576`、`allowed_commands=["python","python3","pytest","git"]`（仅按 `Path(argv[0]).name.lower()` 精确匹配）、`check_commands=[["python","-m","unittest","discover","-s","tests"]]`、`repeat_failure_limit=2`、`repair_budget=4`、`memory_limit=5`、`bind_host="127.0.0.1"`、`bind_port=8765`。未知字段、错误类型、越界值均拒绝。

OpenAI-compatible adapter 构造参数为 `base_url, model, api_key, timeout_seconds`，固定 POST `{base_url}/chat/completions`，header 为 `Authorization: Bearer ...` 与 `Content-Type: application/json`，body 为 `{"model":...,"messages":...,"temperature":0}`。只接受 `choices` 为非空数组且 `choices[0].message.content` 为字符串；HTTP、网络、JSON、schema 错误分别映射 `llm_http_error`、`llm_network_error`、`llm_invalid_json`、`llm_invalid_response`；额外响应字段允许。

风险表：工作区越界、`rm -rf`/`rmdir /s`、磁盘格式化、提权和 shell 解释器 (`sh -c`/`cmd /c`/`powershell -Command`) 为 `deny`；`git push`、`git reset --hard`、`docker push`、发布命令为 `approval`；白名单内普通测试/构建为 `allow`；不在白名单为 `deny`。审批接口 `ApprovalStore.issue(action, ttl_seconds) -> token` 与 `consume(token, action) -> bool`；绑定内容是 action 的排序键 JSON SHA-256，token 60 秒过期、单次消费，错误为 `approval_required`、`approval_invalid`、`approval_expired`、`approval_replayed`。

路径仅接受相对路径，拒绝绝对路径和词法 `..`。解析后的父目录与目标（若存在）必须在工作区 realpath 内；Windows junction/reparse point 按解析后路径处理。读取/写入上限分别为 Config 限值；写入创建父目录，以同目录临时文件 + `os.replace` 原子覆盖，不保留旧 mode；拒绝目录和非 UTF-8 文本。

### 3.1 决策与主循环

- 输入：任务、工作区、声明式策略、LLM 实现。
- 行为：构造有限上下文，调用一次 LLM，解析单个 JSON 动作，依次执行“治理→工具→反馈→记忆”，直到 `finish`、预算耗尽、重复失败或等待审批。
- 输出：结构化运行结果和逐步事件。
- 边界：最多 `max_steps` 步；非法 JSON、未知动作、参数缺失均成为可回灌错误，不直接崩溃。

### 3.2 工具分发

- `read_file(path)`：只读工作区内 UTF-8 文本，限制字节数。
- `write_file(path, content)`：原子写入工作区内文件；拒绝符号链接逃逸。
- `run_command(argv)`：仅允许策略白名单中的可执行文件，使用 `shell=False`，限制超时和输出。
- `run_checks()`：执行配置的确定性验证器。
- `remember(kind, text)`：写入 SQLite 记忆。
- `finish(summary)`：请求停机；只有最后一次验证通过时才算成功。

### 3.3 治理与 HITL

- 路径围栏：解析后的路径必须位于工作区；拒绝绝对越界、`..` 逃逸和指向外部的符号链接。
- 命令护栏：命令必须是 argv 数组；禁止 shell 元字符语义；对删除、提权、网络发布、Git 历史改写等模式分类。
- `deny` 风险直接阻止；`approval` 风险产生带动作摘要、过期时间和随机 nonce 的一次性令牌；令牌仅能用于完全相同动作。
- 所有判定均由代码完成，提示词只解释协议。

### 3.4 反馈闭环（主要贡献）

- 每次写入后运行验证器；捕获退出码、超时、stdout/stderr。
- 将失败确定性分类为 `syntax`、`test_assertion`、`missing_dependency`、`timeout`、`policy`、`unknown`。
- 对输出去 ANSI、截断并生成稳定指纹；同一指纹连续出现达到阈值时停止，避免无效循环。
- 维护独立的修复预算；将紧凑反馈对象回灌给下一轮 LLM。验证通过后清零连续失败计数。
- `finish` 前强制终检；未通过则拒绝成功停机并继续（预算允许时）。

### 3.5 记忆与上下文

- SQLite 实体：`memory(id, workspace_id, kind, text, created_at)` 与 `run_event(id, run_id, step, type, payload, created_at)`。
- 按工作区隔离；检索使用分词重叠分数、类型权重与新近度的确定性排序，最多返回配置数量。
- 不保存 API key、完整环境或未经截断的命令输出。

### 3.6 配置、凭据与分发

- JSON 配置控制步数、超时、允许命令、验证命令、输出上限和绑定地址；未知字段报错。
- API key 优先从 OS keyring 获取；容器支持只读 secret 文件路径。首次真实 provider 运行时以隐藏输入引导录入；`key status/set/clear` 不回显明文。
- 环境变量只接受“secret 文件路径”，不接受 key 明文本身。secret 文件权限过宽时拒绝（Windows 上记录平台限制）。
- Docker 镜像和 Python 包两种分发；WebUI 默认仅绑定 `127.0.0.1`，容器由用户显式绑定端口。

### 3.7 WebUI

- 页面包含任务输入、工作区、运行按钮、事件时间线和安全状态。
- Web 服务只接受本机工作区根目录内的相对路径；HTML 转义所有输出；设置 CSP、禁止缓存和基本安全响应头。
- 首版同步执行单个运行，不提供多租户认证；公网部署必须置于认证反向代理后。

## 4. 非功能需求

- 性能：不含 LLM 和外部命令时，单步调度 <50ms；日志输出单项上限默认 16KiB。
- 安全威胁模型：恶意/被注入的 LLM 输出、路径穿越、shell 注入、凭据泄露、拒绝服务、审批重放。对策为结构化动作、路径 realpath 围栏、`shell=False`、白名单、secret store、预算/超时/截断、一次性令牌。
- 可用性：Windows/Linux、Python 3.11+；错误包含机器码和人类说明。
- 可观测性：JSONL 事件含 run/step/type，不记录 key；可由 WebUI 查看。
- 可测试性：核心逻辑只依赖标准库，mock LLM 下完全离线确定。

## 5. 系统架构与数据流

```text
CLI/Web -> RunService -> AgentLoop -> LLMPort
                         |  parse Action
                         v
                    Guardrail -> ApprovalStore
                         |
                    ToolRegistry -> Workspace / subprocess / MemoryStore
                         |
                    ValidatorPipeline -> FailureClassifier -> next context
```

外部依赖只有可选的 OpenAI-compatible HTTP API 和可选 `keyring` 包；不使用任何现成 agent runner。

## 6. 领域与机制设计

- 工具：文件读写、受限进程、验证器、记忆和停机。
- 客观反馈：进程退出码、超时和测试输出，由分类器编码分析。
- 危险动作：越界文件、删除/提权/发布/历史重写；由策略引擎与 HITL 状态机处理。
- 记忆：约定、决策、失败摘要；按相关性小规模检索。
- 重点：反馈闭环。其工程深度体现在自动验证、失败分类、稳定指纹、重复失败熔断、修复预算和成功终检，全部可由 mock LLM 单测。

## 7. 技术选型

- Python 3.11：标准库可实现循环、HTTP、SQLite、subprocess 与测试，跨平台且便于审阅。
- `unittest`：零网络、零额外依赖的一键测试。
- OpenAI-compatible Chat Completions：只作为单次补全端口，不使用 agent SDK。
- 原生 HTTP WebUI：降低供应链和容器体积；本项目不采用 Open Design，因为交付界面是纯运维控制台、无复杂设计系统需求，此偏离记录于日志。
- Docker OCI：最容易在全新机器复现；目标 `linux/amd64` 与 `linux/arm64`（由 buildx 构建）。

## 8. 验收标准

1. mock LLM 可驱动读写、验证、反馈、修复、停机全链路。
2. `rm -rf /`、越界路径和未批准发布动作被确定性拦截。
3. 注入一次测试失败后，下一次 LLM 输入包含分类后的反馈，且后续动作变化并最终通过。
4. 重复相同失败达到阈值后以 `stalled` 停机。
5. 记忆按工作区隔离并按相关性有界检索。
6. `python -m unittest discover -s tests -v` 一键通过且不访问网络。
7. `python -m patchpilot demo` 重放三项机制演示。
8. Docker build 成功，容器能启动 `/healthz` 与 WebUI。
9. key 状态不回显明文；日志中不出现测试 key。

## 9. 风险与未决问题

- 通用命令静态分类无法证明任意程序安全，因此采用“可执行文件白名单 + 工作区 + 超时”，不是通用沙箱；README 必须明确边界。
- Windows 文件权限检查语义不同；主机优先 OS keyring，容器优先 Docker secret。
- 真实 provider 的响应格式可能变化；适配器严格校验，课程测试只承诺 mock 的确定性。
- 公网 URL、NJU Git PR 和 CI pass 需要仓库账号，不能由本地构建替代。
