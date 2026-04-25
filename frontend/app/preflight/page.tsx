"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { startSession } from "@/lib/api";
import type { Guide, Part } from "@/lib/types";

function Stars({ n }: { n: number }) {
  return <span style={{ letterSpacing: 2 }}>{"★".repeat(n)}{"☆".repeat(5 - n)}</span>;
}

function SafetyTag({ tier }: { tier: string }) {
  const map: Record<string, { cls: string; label: string }> = {
    green:  { cls: "tag-green", label: "🟢 Safe — Cosmetic" },
    yellow: { cls: "tag-amber", label: "🟡 Mechanical" },
    red:    { cls: "tag-red",   label: "🔴 Safety-Critical" },
  };
  const { cls, label } = map[tier] ?? map.yellow;
  return <span className={cls}>{label}</span>;
}

export default function PreflightPage() {
  const router = useRouter();
  const [guide, setGuide]       = useState<Guide | null>(null);
  const [vehicle, setVehicle]   = useState("");
  const [checkedTools, setCheckedTools] = useState<Set<number>>(new Set());
  const [checkedParts, setCheckedParts] = useState<Set<number>>(new Set());
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    const g = sessionStorage.getItem("guide");
    const v = sessionStorage.getItem("vehicleState");
    if (!g || !v) { router.push("/"); return; }
    setGuide(JSON.parse(g));
    setVehicle(JSON.parse(v).desc);
  }, [router]);

  async function handleStart() {
    if (!guide) return;
    setStarting(true);
    const sessionId = crypto.randomUUID();
    await startSession(sessionId, guide, vehicle);
    sessionStorage.setItem("sessionId", sessionId);
    router.push("/session");
  }

  if (!guide) return null;

  return (
    <main style={{ minHeight: "100dvh", padding: "24px 16px 120px", maxWidth: 520, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <button className="btn-ghost" style={{ width: "auto", marginBottom: 20, fontSize: 14 }} onClick={() => router.push("/")}>
          ← Back
        </button>
        <h1 style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.3, marginBottom: 12 }}>
          {guide.title}
        </h1>
        <p style={{ fontSize: 14, color: "var(--muted)", lineHeight: 1.6, marginBottom: 16 }}>
          {guide.summary}
        </p>

        {/* Metadata pills */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <SafetyTag tier={guide.safety_tier} />
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            <Stars n={guide.difficulty} /> difficulty
          </span>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            ~{guide.time_estimate_minutes} min
          </span>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>
            {guide.confidence_score >= 0.75 ? "✓" : "⚠"} {Math.round(guide.confidence_score * 100)}% confidence
          </span>
        </div>
      </div>

      {/* Safety warning for red tier */}
      {guide.safety_tier === "red" && (
        <div style={{ background: "#450a0a", border: "1px solid #7f1d1d", borderRadius: 14, padding: "16px 18px", marginBottom: 20 }}>
          <p style={{ fontWeight: 700, color: "#fca5a5", marginBottom: 6 }}>🔴 Safety-Critical Repair</p>
          <p style={{ fontSize: 14, color: "#fca5a5", opacity: 0.85, lineHeight: 1.5 }}>
            This repair directly affects your vehicle's ability to stop or steer.
            Follow every step exactly. If anything seems wrong, stop and see a professional.
          </p>
        </div>
      )}

      {/* Warnings */}
      {guide.warnings.length > 0 && (
        <div className="card" style={{ padding: 18, marginBottom: 16 }}>
          <p className="label">Before you start</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
            {guide.warnings.slice(0, 4).map((w, i) => (
              <p key={i} style={{ fontSize: 14, color: "#fcd34d", lineHeight: 1.5 }}>⚠ {w}</p>
            ))}
          </div>
        </div>
      )}

      {/* Tools checklist */}
      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <p className="label">Tools you'll need</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 8 }}>
          {guide.tools_required.map((tool, i) => (
            <label key={i} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 8px", cursor: "pointer", borderRadius: 10, background: checkedTools.has(i) ? "var(--surface2)" : "transparent" }}>
              <input
                type="checkbox"
                checked={checkedTools.has(i)}
                onChange={() => {
                  const s = new Set(checkedTools);
                  s.has(i) ? s.delete(i) : s.add(i);
                  setCheckedTools(s);
                }}
                style={{ width: 20, height: 20, accentColor: "var(--green)", cursor: "pointer" }}
              />
              <span style={{ fontSize: 15, color: checkedTools.has(i) ? "var(--muted)" : "var(--text)", textDecoration: checkedTools.has(i) ? "line-through" : "none" }}>
                {tool}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Parts checklist */}
      <div className="card" style={{ padding: 18, marginBottom: 28 }}>
        <p className="label">Parts you'll need</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 8 }}>
          {guide.parts_required.map((part: Part, i: number) => (
            <label key={i} style={{ display: "flex", alignItems: "flex-start", gap: 14, padding: "12px 8px", cursor: "pointer", borderRadius: 10, background: checkedParts.has(i) ? "var(--surface2)" : "transparent" }}>
              <input
                type="checkbox"
                checked={checkedParts.has(i)}
                onChange={() => {
                  const s = new Set(checkedParts);
                  s.has(i) ? s.delete(i) : s.add(i);
                  setCheckedParts(s);
                }}
                style={{ width: 20, height: 20, accentColor: "var(--green)", cursor: "pointer", marginTop: 2 }}
              />
              <div>
                <p style={{ fontSize: 15, color: checkedParts.has(i) ? "var(--muted)" : "var(--text)", textDecoration: checkedParts.has(i) ? "line-through" : "none" }}>
                  {part.quantity}× {part.name}
                  {part.consumable && <span style={{ color: "var(--muted)", fontSize: 13 }}> (consumable)</span>}
                </p>
                {part.notes && (
                  <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 2 }}>{part.notes}</p>
                )}
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Fixed CTA */}
      <div style={{ position: "fixed", bottom: 0, left: 0, right: 0, padding: "16px 16px 32px", background: "linear-gradient(transparent, var(--bg) 40%)" }}>
        <div style={{ maxWidth: 520, margin: "0 auto" }}>
          <button className="btn-primary" onClick={handleStart} disabled={starting}>
            {starting ? "Starting..." : "✅  I'm ready — start the repair"}
          </button>
        </div>
      </div>
    </main>
  );
}
