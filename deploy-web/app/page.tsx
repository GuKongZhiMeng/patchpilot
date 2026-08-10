"use client";

import { useState } from "react";

const delivery = [
  ["SPEC / PLAN / PROCESS", "complete"],
  ["Harness core + mock LLM", "complete"],
  ["Docker / wheel distribution", "complete"],
  ["README security boundary", "complete"],
  ["AGENT_LOG evidence", "complete"],
  ["GitLab unit-test job", "configured"],
  ["Remote CI pass record", "account action"],
  ["Personal reflection", "student action"],
  ["Public WebUI", "online"],
] as const;

const initialEvents = [
  { step: 1, label: "Guardrail", detail: "检测到 rm -rf /，策略代码拒绝执行", tone: "blocked" },
  { step: 2, label: "Validator", detail: "注入 AssertionError，归类为 test_assertion", tone: "failed" },
  { step: 3, label: "Feedback", detail: "压缩失败信息并回灌，下一动作发生改变", tone: "repair" },
  { step: 4, label: "Final check", detail: "验证通过，主循环以 completed 停机", tone: "passed" },
];

export default function Home() {
  const [task, setTask] = useState("修复一次失败的单元测试，并在验证通过后停止。");
  const [events, setEvents] = useState<typeof initialEvents>([]);
  const [status, setStatus] = useState("ready");

  function runDemo() {
    setStatus("running");
    setEvents(initialEvents);
    window.setTimeout(() => setStatus("completed"), 350);
  }

  return (
    <main>
      <nav><span className="brand">PATCHPILOT / A</span><span className="nav-note">AI4SE FINAL DELIVERY</span></nav>
      <section className="hero">
        <p className="eyebrow">Coding Agent Harness · deterministic by design</p>
        <h1>让 agent 的每一步<br/><em>都有边界与证据。</em></h1>
        <p className="lede">PatchPilot 自己实现决策循环、工具分发、治理、记忆与反馈闭环。移除真实 LLM 后，核心机制仍可被 34 项离线测试确定性验证。</p>
        <div className="metrics">
          <div><strong>6</strong><span>harness dimensions</span></div>
          <div><strong>34</strong><span>offline tests</span></div>
          <div><strong>10</strong><span>evidence commits</span></div>
          <div><strong>0</strong><span>real keys committed</span></div>
        </div>
      </section>

      <section className="lab" aria-labelledby="lab-title">
        <div className="section-head"><div><p className="kicker">01 / MECHANISM LAB</p><h2 id="lab-title">离线 mock 演示</h2></div><span className={`run-state ${status}`}>{status}</span></div>
        <label htmlFor="task">任务</label>
        <textarea id="task" value={task} onChange={(event) => setTask(event.target.value)} maxLength={500}/>
        <button onClick={runDemo} disabled={status === "running"}>运行确定性演示</button>
        <div className="lab-meta"><span><b>WORKSPACE</b>ephemeral-temp</span><span><b>POLICY</b>host execution denied</span><span><b>INPUT</b>{task.length}/500</span></div>
        <ol className="timeline" aria-live="polite">
          {events.length === 0 ? <li className="empty">等待运行。演示不访问网络、不调用真实 LLM。</li> : events.map((event) => (
            <li key={event.step}><span className={`dot ${event.tone}`}/><b>Step {event.step} · {event.label}</b><p>{event.detail}</p></li>
          ))}
        </ol>
      </section>

      <section className="delivery" aria-labelledby="delivery-title">
        <div className="section-head"><div><p className="kicker">02 / DELIVERY MATRIX</p><h2 id="delivery-title">最终交付物覆盖</h2></div><p>账号与个人写作项保持显式待办，不伪造证据。</p></div>
        <div className="matrix">{delivery.map(([name, state], index) => <div className="matrix-row" key={name}><span>{String(index + 1).padStart(2,"0")}</span><b>{name}</b><i className={state.replace(" ", "-")}>{state}</i></div>)}</div>
      </section>

      <section className="architecture" aria-labelledby="architecture-title">
        <div><p className="kicker">03 / ENGINEERING DEPTH</p><h2 id="architecture-title">LLM 之外，仍然成立</h2></div>
        <div className="flow"><span>Context</span><b>→</b><span>LLM Port</span><b>→</b><span>Action Parser</span><b>→</b><span>Guardrail</span><b>→</b><span>Tool</span><b>→</b><span>Validator</span></div>
        <div className="principles"><article><b>Governance in code</b><p>路径围栏、命令分类、一次性审批 token 与容器默认边界。</p></article><article><b>Feedback in code</b><p>失败分类、ANSI 清理、稳定指纹、修复预算与重复失败熔断。</p></article><article><b>Memory in code</b><p>SQLite 工作区隔离、敏感信息拒绝和有界相关性检索。</p></article></div>
      </section>
      <footer><span>PatchPilot 0.1.0</span><span>Spec-driven · mock-tested · human-owned</span></footer>
    </main>
  );
}
