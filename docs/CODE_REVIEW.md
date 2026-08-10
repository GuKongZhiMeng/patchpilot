# 两阶段最终审查

## 阶段 1：Spec 合规

独立 reviewer 确认主循环、mock LLM、工具、治理、反馈、记忆、配置、凭据、CI 与机制演示均有代码和测试。初审指出 HITL 未接主循环、WebUI 只有 raw demo 摘要；修订后主循环可进入 `awaiting_approval` 或通过 callback 发行/消费一次性 token，WebUI 展示临时工作区、安全状态、反馈状态与真实事件时间线。

## 阶段 2：代码质量与安全

- Critical：宿主默认允许 Python/Git，argv 白名单不是 OS 沙箱。修复：真实 CLI 默认只在容器 marker 下运行；宿主必须显式 `--unsafe-local-exec`；额外拒绝 Python `-c`/stdin/任意模块与 Git 外部工作树参数。
- Important：HITL 未真正暂停。修复：无 callback 立即以 `awaiting_approval` 停机；批准后 issue/consume 内容绑定、单次、过期 token。
- Minor：LLM 耗尽时复用上一轮 raw。修复：每轮将 raw 清空，只在当前轮有响应时追加 assistant message。
- Minor：README 的 HITL 限制已过时。修复：更新为当前交互行为。

复核时 33 tests 通过、2 项 Windows 条件跳过；页面结构修订后最终为 34 tests 通过、2 项 Windows 条件跳过。

