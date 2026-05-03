"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { sendChat, nextStep } from "@/lib/api";
import type { Guide, Step } from "@/lib/types";

export default function SessionPage() {
  const router = useRouter();
  const [guide, setGuide]           = useState<Guide | null>(null);
  const [sessionId, setSessionId]   = useState("");
  const [vehicle, setVehicle]       = useState("");
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted]   = useState<number[]>([]);
  const [done, setDone]             = useState(false);
  const [chatOpen, setChatOpen]     = useState(false);
  const [messages, setMessages]     = useState<{ role: string; text: string }[]>([]);
  const [input, setInput]           = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [advancing, setAdvancing]   = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const g  = sessionStorage.getItem("guide");
    const v  = sessionStorage.getItem("vehicleState");
    const sid = sessionStorage.getItem("sessionId");
    if (!g || !v || !sid) { router.push("/"); return; }
    setGuide(JSON.parse(g));
    setVehicle(JSON.parse(v).desc);
    setSessionId(sid);
  }, [router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleNext() {
    if (!guide || advancing) return;
    setAdvancing(true);
    const res = await nextStep(sessionId);
    if (res.is_complete) {
      setDone(true);
    } else {
      setCompleted(prev => [...prev, currentStep]);
      setCurrentStep(res.current_step);
    }
    setAdvancing(false);
  }

  async function handleChat(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || chatLoading) return;
    const msg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: msg }]);
    setChatLoading(true);
    const res = await sendChat(sessionId, msg);
    setMessages(prev => [...prev, { role: "ai", text: res.message }]);
    setChatLoading(false);
  }

  if (!guide) return null;

  if (done) return (
    <main style={{ minHeight: "100dvh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24, textAlign: "center" }}>
      <div style={{ fontSize: 72, marginBottom: 24 }}>🎉</div>
      <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 12 }}>Repair complete!</h1>
      <p style={{ color: "var(--muted)", fontSize: 16, marginBottom: 40, maxWidth: 320, lineHeight: 1.6 }}>
        Great work. Monitor for the next few days and test the repair before driving normally.
      </p>
      <button className="btn-primary" style={{ maxWidth: 300 }} onClick={() => router.push("/")}>
        Start another repair
      </button>
    </main>
  );

  const step: Step = guide.steps[currentStep];
  const total = guide.steps.length;
  const progress = (currentStep / total) * 100;

  return (
    <main style={{ minHeight: "100dvh", display: "flex", flexDirection: "column", background: "var(--bg)" }}>

      {/* Top bar */}
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 16 }}>
        <button onClick={() => router.push("/")} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 20, padding: 4 }}>←</button>
        <div style={{ flex: 1 }}>
          <div style={{ height: 4, background: "var(--surface2)", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${progress}%`, background: "var(--green)", borderRadius: 4, transition: "width 0.4s ease" }} />
          </div>
        </div>
        <span style={{ fontSize: 13, color: "var(--muted)", whiteSpace: "nowrap" }}>
          {currentStep + 1} / {total}
        </span>
      </div>

      {/* Step content */}
      <div style={{ flex: 1, overflow: "auto", padding: "28px 20px 180px" }}>

        {/* Step label */}
        <p style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: "var(--green)", marginBottom: 10 }}>
          Step {step.step_number}
        </p>

        {/* Step title — the main action */}
        <h2 style={{ fontSize: 26, fontWeight: 800, lineHeight: 1.25, letterSpacing: "-0.5px", marginBottom: 16, color: "var(--text)" }}>
          {step.title}
        </h2>

        {/* Instruction */}
        <p style={{ fontSize: 16, lineHeight: 1.7, color: "#cbd5e1", marginBottom: 24 }}>
          {step.instruction}
        </p>

        {/* Torque spec — unmissable */}
        {step.torque_spec && (
          <div style={{ background: "#1c1a00", border: "1px solid #713f12", borderRadius: 12, padding: "14px 16px", marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
            <span style={{ fontSize: 20 }}>🔩</span>
            <div>
              <p style={{ fontSize: 12, fontWeight: 700, color: "#fcd34d", letterSpacing: 0.8, textTransform: "uppercase" }}>Torque spec</p>
              <p style={{ fontSize: 17, fontWeight: 700, color: "#fde68a" }}>{step.torque_spec}</p>
            </div>
          </div>
        )}

        {/* Warning — red banner */}
        {step.warning && (
          <div style={{ background: "#450a0a", border: "1px solid #7f1d1d", borderRadius: 12, padding: "14px 16px", marginBottom: 16, display: "flex", gap: 12, alignItems: "flex-start" }}>
            <span style={{ fontSize: 20 }}>⚠️</span>
            <p style={{ fontSize: 14, color: "#fca5a5", lineHeight: 1.5 }}>{step.warning}</p>
          </div>
        )}

        {/* Tool needed */}
        {step.tool_needed && (
          <p style={{ fontSize: 14, color: "var(--muted)", marginBottom: 16 }}>
            🔧 Tool: <span style={{ color: "var(--text)" }}>{step.tool_needed}</span>
          </p>
        )}

        {/* Why — collapsible */}
        {step.why && (
          <details style={{ marginBottom: 20 }}>
            <summary style={{ fontSize: 14, color: "var(--green)", cursor: "pointer", fontWeight: 600, listStyle: "none" }}>
              ↳ Why this step?
            </summary>
            <p style={{ fontSize: 14, color: "var(--muted)", lineHeight: 1.6, marginTop: 8, paddingLeft: 12 }}>
              {step.why}
            </p>
          </details>
        )}

        {/* Confidence indicator */}
        <p style={{ fontSize: 12, color: "var(--subtle)" }}>
          Step confidence: {Math.round(step.confidence * 100)}%
          {step.confidence < 0.65 && <span style={{ color: "var(--amber)" }}> — verify spec before applying</span>}
        </p>
      </div>

      {/* Fixed bottom — Done button + chat trigger */}
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, padding: "12px 16px 32px", background: "linear-gradient(transparent, var(--bg) 35%)" }}>
        <div style={{ maxWidth: 520, margin: "0 auto", display: "flex", gap: 12, alignItems: "center" }}>
          <button
            style={{ flex: "0 0 56px", height: 56, borderRadius: 16, background: "var(--surface2)", border: "1px solid var(--border)", fontSize: 24, cursor: "pointer" }}
            onClick={() => setChatOpen(true)}
            title="Ask AI mechanic"
          >
            💬
          </button>
          <button className="btn-primary" style={{ flex: 1, height: 56, borderRadius: 16, fontSize: 18 }} onClick={handleNext} disabled={advancing}>
            {advancing ? "..." : currentStep === total - 1 ? "Complete ✓" : "Done → Next step"}
          </button>
        </div>
      </div>

      {/* Chat sheet */}
      {chatOpen && (
        <div style={{ position: "fixed", inset: 0, zIndex: 100 }}>
          {/* Backdrop */}
          <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.7)" }} onClick={() => setChatOpen(false)} />

          {/* Sheet */}
          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "var(--surface)", borderRadius: "24px 24px 0 0", padding: "20px 16px 40px", maxHeight: "75dvh", display: "flex", flexDirection: "column" }}>
            {/* Handle */}
            <div style={{ width: 40, height: 4, background: "var(--border)", borderRadius: 4, margin: "0 auto 20px" }} />

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <p style={{ fontWeight: 700, fontSize: 16 }}>💬 Ask your AI mechanic</p>
              <button onClick={() => setChatOpen(false)} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 20 }}>✕</button>
            </div>

            <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 16 }}>
              Knows your {vehicle} and you're on Step {currentStep + 1}.
            </p>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
              {messages.length === 0 && (
                <p style={{ color: "var(--muted)", fontSize: 14, textAlign: "center", padding: "20px 0" }}>
                  Ask anything — what you see, what's confusing, which bolt to use.
                </p>
              )}
              {messages.map((m, i) => (
                <div key={i} style={{
                  padding: "12px 14px",
                  borderRadius: 14,
                  fontSize: 15,
                  lineHeight: 1.5,
                  background: m.role === "user" ? "var(--surface2)" : "#0f2318",
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "85%",
                  border: m.role === "ai" ? "1px solid var(--green-dim)" : "none",
                }}>
                  {m.text}
                </div>
              ))}
              {chatLoading && (
                <div style={{ padding: "12px 14px", borderRadius: 14, background: "#0f2318", alignSelf: "flex-start", color: "var(--muted)", fontSize: 15 }}>
                  ...
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleChat} style={{ display: "flex", gap: 10 }}>
              <input
                className="input"
                placeholder="Type your question..."
                value={input}
                onChange={e => setInput(e.target.value)}
                autoFocus
                style={{ flex: 1 }}
              />
              <button type="submit" disabled={chatLoading || !input.trim()} style={{ background: "var(--green)", color: "#000", border: "none", borderRadius: 12, width: 48, height: 48, fontSize: 20, cursor: "pointer", flexShrink: 0 }}>
                ↑
              </button>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
