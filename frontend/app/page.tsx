"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { detectIntent } from "@/lib/api";

/* ── Vehicle text parser ─────────────────────────────
   Accepts "2019 Toyota Camry" or "2015 Honda Civic EX 1.5T"
   Returns structured fields the backend expects.           */
function parseVehicleText(text: string): { year: number; make: string; model: string; engine?: string } | null {
  const m = text.trim().match(/^(\d{4})\s+([A-Za-z]+)\s+(.+)/);
  if (!m) return null;
  const year = parseInt(m[1]);
  if (year < 1985 || year > 2027) return null;
  const rest = m[3].trim().split(/\s+/);
  const model = rest[0];
  const engine = rest.length > 1 ? rest.slice(1).join(" ") : undefined;
  return { year, make: m[2], model, engine };
}

const HOW_STEPS = [
  { n: "01", icon: "🔍", title: "You describe it", body: "Tell us your vehicle and what's wrong — symptoms, sounds, error codes. The more specific, the sharper the guide." },
  { n: "02", icon: "🤖", title: "AI cross-references", body: "We pull YouTube repair transcripts, forum threads, and repair manuals to find the most reliable, commonly recommended fixes." },
  { n: "03", icon: "📋", title: "Step-by-step guide", body: "Get an ordered guide with tools, parts, safety warnings, torque specs, and source citations — written for your exact vehicle." },
];

const SAMPLE_STEPS = [
  { n: "01", title: "Loosen lug nuts on the ground", body: "Crack each front lug nut a half-turn while the wheels are still on the ground. Much easier than fighting a spinning wheel." },
  { n: "02", title: "Jack up & secure on stands", body: "Place the floor jack under the manufacturer's jack point. Raise until the wheel clears, then set jack stands — never work under a car on just a jack." },
  { n: "03", title: "Remove caliper & hang it", body: "Remove the two caliper slide bolts (12mm). Slide the caliper off the rotor and hang it with a wire hook — never let it dangle by the brake hose." },
  { n: "04", title: "Compress the caliper piston", body: "Use a C-clamp or piston wind-back tool to push the piston back into the bore. Place an old pad against the piston as a buffer." },
  { n: "05", title: "Install new pads & torque to spec", body: "Slide new pads into the bracket. Reinstall the caliper and torque slide bolts to 25 ft-lbs. Reinstall wheel and torque lug nuts to 80 ft-lbs in a star pattern." },
];

const C = {
  cream: "#F9F7F3",
  white: "#FFFFFF",
  navy: "#1B2A4A",
  navy80: "#2d4068",
  orange: "#E8703A",
  orangeDark: "#c85e2a",
  orangeBg: "#FEF3ED",
  border: "#E8E3DA",
  muted: "#6B7280",
  body: "#374151",
  lightGray: "#F0EDE8",
};

export default function Home() {
  const router = useRouter();
  const [vehicle, setVehicle] = useState("");
  const [problem, setProblem] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = parseVehicleText(vehicle);
    if (!parsed) {
      setError('Include year, make, and model — e.g. "2019 Toyota Camry"');
      return;
    }
    if (!problem.trim()) {
      setError("Describe the problem or repair needed");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const vehicleDesc = `${parsed.year} ${parsed.make} ${parsed.model}${parsed.engine ? ` (${parsed.engine})` : ""}`;
      const intent = await detectIntent(problem.trim(), vehicleDesc);
      const repair = intent.repair_query || problem.trim();
      sessionStorage.setItem("vehicleState", JSON.stringify({ ...parsed, desc: vehicleDesc, repair }));
      router.push("/building");
    } catch {
      setError("Something went wrong. Check that the server is running.");
    } finally {
      setLoading(false);
    }
  }

  function fillExample() {
    setVehicle("2015 Honda Civic EX");
    setProblem("Squeaky brakes when stopping at low speed");
    document.getElementById("hero-form")?.scrollIntoView({ behavior: "smooth" });
  }

  const inputStyle = (focused: boolean): React.CSSProperties => ({
    width: "100%",
    background: C.cream,
    border: `1px solid ${focused ? C.orange : C.border}`,
    borderRadius: 10,
    padding: "14px 16px",
    fontSize: 15,
    color: C.navy,
    outline: "none",
    fontFamily: "var(--font-mono, monospace)",
    transition: "border-color 0.15s",
  });

  const [vFocus, setVFocus] = useState(false);
  const [pFocus, setPFocus] = useState(false);

  return (
    <div style={{ fontFamily: "var(--font-inter, sans-serif)", background: C.cream, minHeight: "100dvh", color: C.navy }}>

      {/* ── NAV ──────────────────────────────────────────── */}
      <nav style={{ position: "sticky", top: 0, zIndex: 50, background: "rgba(249,247,243,0.96)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 64, display: "flex", alignItems: "center", justifyContent: "space-between" }}>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, background: C.orange, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>🔧</div>
            <span style={{ fontWeight: 800, fontSize: 18, letterSpacing: "-0.5px" }}>WrenchAI</span>
          </div>

          <div className="lp-nav-links">
            {[["How it works", "#how-it-works"], ["Sample", "#sample"], ["Sources", "#sources"]].map(([label, href]) => (
              <a key={href} href={href}
                style={{ fontSize: 14, fontWeight: 500, color: C.navy80, textDecoration: "none", transition: "color 0.15s" }}
                onMouseEnter={e => (e.currentTarget.style.color = C.orange)}
                onMouseLeave={e => (e.currentTarget.style.color = C.navy80)}>
                {label}
              </a>
            ))}
          </div>

          <button
            onClick={() => document.getElementById("hero-form")?.scrollIntoView({ behavior: "smooth" })}
            style={{ background: C.orange, color: "#fff", fontWeight: 700, fontSize: 13, letterSpacing: 0.8, padding: "10px 18px", borderRadius: 8, border: "none", cursor: "pointer", textTransform: "uppercase" as const, transition: "background 0.15s" }}
            onMouseEnter={e => (e.currentTarget.style.background = C.orangeDark)}
            onMouseLeave={e => (e.currentTarget.style.background = C.orange)}>
            Get Guide
          </button>
        </div>
      </nav>

      {/* ── HERO ─────────────────────────────────────────── */}
      <section style={{ padding: "72px 24px 88px", maxWidth: 1200, margin: "0 auto" }}>

        {/* Pill badge */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: C.white, border: `1px solid ${C.border}`, borderRadius: 100, padding: "6px 14px", marginBottom: 36, fontSize: 12, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase" as const, color: C.navy }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: C.orange, display: "inline-block", flexShrink: 0 }} />
          AI Mechanic, On Call
        </div>

        {/* Headline */}
        <h1 style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: "clamp(52px, 9vw, 96px)", fontWeight: 800, lineHeight: 1.0, letterSpacing: "-2px", marginBottom: 28, maxWidth: 920 }}>
          Fix it yourself.<br />
          Get a guide built{" "}
          <span style={{ color: C.orange }}>just for your car.</span>
        </h1>

        {/* Subtitle */}
        <p style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 16, lineHeight: 1.75, color: C.muted, marginBottom: 52, maxWidth: 580 }}>
          WrenchAI scans YouTube repair transcripts and active car forum
          threads, then assembles a clear, step-by-step DIY guide for
          your exact vehicle and problem.
        </p>

        {/* Form card */}
        <form id="hero-form" onSubmit={handleSubmit}>
          <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 18, padding: "24px 24px 20px", boxShadow: "0 4px 32px rgba(0,0,0,0.07)", maxWidth: 880 }}>
            <div className="lp-form-grid">
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.muted, marginBottom: 8 }}>Your Vehicle</label>
                <input
                  value={vehicle}
                  onChange={e => setVehicle(e.target.value)}
                  placeholder="2015 Honda Civic EX"
                  style={inputStyle(vFocus)}
                  onFocus={() => setVFocus(true)}
                  onBlur={() => setVFocus(false)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.muted, marginBottom: 8 }}>The Problem</label>
                <input
                  value={problem}
                  onChange={e => setProblem(e.target.value)}
                  placeholder="Squeaky brakes when stopping at low speed"
                  style={inputStyle(pFocus)}
                  onFocus={() => setPFocus(true)}
                  onBlur={() => setPFocus(false)}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{ background: loading ? "#c0a090" : C.orange, color: "#fff", fontWeight: 700, fontSize: 14, letterSpacing: 0.8, padding: "14px 22px", borderRadius: 10, border: "none", cursor: loading ? "not-allowed" : "pointer", whiteSpace: "nowrap" as const, textTransform: "uppercase" as const, transition: "background 0.15s" }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.background = C.orangeDark; }}
                onMouseLeave={e => { if (!loading) e.currentTarget.style.background = C.orange; }}>
                {loading ? "Building..." : "🔍 Generate"}
              </button>
            </div>
            {error && <p style={{ fontSize: 13, color: "#dc2626", marginTop: 12, fontFamily: "var(--font-mono, monospace)" }}>{error}</p>}
            <p style={{ fontSize: 12, color: C.muted, marginTop: 14, fontFamily: "var(--font-mono, monospace)" }}>
              Tip: include trim & engine if you know it (e.g. "2018 F-150 5.0L") for sharper results.
            </p>
          </div>
        </form>

        {/* Stats bar */}
        <div className="lp-stats" style={{ marginTop: 52 }}>
          {[["50+", "vehicle makes"], ["500+", "guides built"], ["3", "knowledge sources"], ["< 60s", "first build time"]].map(([n, label]) => (
            <div key={label}>
              <div style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: 28, fontWeight: 800, color: C.navy, letterSpacing: "-1px" }}>{n}</div>
              <div style={{ fontSize: 12, color: C.muted, marginTop: 2, fontFamily: "var(--font-mono, monospace)" }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────── */}
      <section id="how-it-works" style={{ background: C.white, padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase" as const, color: C.orange, marginBottom: 12 }}>The Process</p>
          <h2 style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: "clamp(32px, 5vw, 48px)", fontWeight: 800, letterSpacing: "-1px", marginBottom: 48 }}>How a guide gets built</h2>
          <div className="lp-grid-3">
            {HOW_STEPS.map(s => (
              <div key={s.n} style={{ background: C.cream, border: `1px solid ${C.border}`, borderRadius: 18, padding: 28 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: C.muted, letterSpacing: 1 }}>{s.n}</span>
                  <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 10, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>{s.icon}</div>
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: C.orange, marginBottom: 10 }}>{s.title}</h3>
                <p style={{ fontSize: 14, color: C.muted, lineHeight: 1.65, fontFamily: "var(--font-mono, monospace)" }}>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SOURCES ──────────────────────────────────────── */}
      <section id="sources" style={{ background: C.lightGray, padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div className="lp-grid-2">
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase" as const, color: C.orange, marginBottom: 12 }}>Sourced from Real Mechanics</p>
              <h2 style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: "clamp(30px, 4vw, 44px)", fontWeight: 800, letterSpacing: "-1px", lineHeight: 1.1, marginBottom: 20 }}>
                Trusted YouTube channels & forums — distilled.
              </h2>
              <p style={{ fontSize: 15, color: C.muted, lineHeight: 1.75, fontFamily: "var(--font-mono, monospace)" }}>
                Every guide is grounded in two pillars of grassroots automotive knowledge: hours of recorded repair videos and decades of forum wisdom from people who actually own your car.
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {[
                { icon: "📺", title: "YouTube transcripts", body: "ChrisFix, Scotty Kilmer, South Main Auto, ETCG, model-specific channels" },
                { icon: "💬", title: "Car forums", body: "Model owner forums, r/MechanicAdvice, BobIsTheOilGuy, 9thCivic, TacomaWorld" },
              ].map(src => (
                <div key={src.title} style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 16, padding: 24 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                    <div style={{ background: "#FEF3ED", borderRadius: 10, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>{src.icon}</div>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: C.orange }}>{src.title}</h3>
                  </div>
                  <p style={{ fontSize: 14, color: C.muted, fontFamily: "var(--font-mono, monospace)", lineHeight: 1.55 }}>{src.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── SAMPLE OUTPUT ────────────────────────────────── */}
      <section id="sample" style={{ background: C.cream, padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 40, flexWrap: "wrap", gap: 16 }}>
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.8, textTransform: "uppercase" as const, color: C.orange, marginBottom: 12 }}>Sample Output</p>
              <h2 style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: "clamp(30px, 4vw, 44px)", fontWeight: 800, letterSpacing: "-1px" }}>What you'll get back</h2>
            </div>
            <button onClick={fillExample}
              style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 20px", fontSize: 14, fontWeight: 600, color: C.navy, cursor: "pointer", transition: "background 0.15s" }}
              onMouseEnter={e => (e.currentTarget.style.background = C.cream)}
              onMouseLeave={e => (e.currentTarget.style.background = C.white)}>
              Try this example →
            </button>
          </div>

          <div style={{ background: C.white, border: `1px solid ${C.border}`, borderRadius: 20, overflow: "hidden", boxShadow: "0 8px 48px rgba(0,0,0,0.07)" }}>

            {/* Guide header */}
            <div style={{ padding: "28px 32px", borderBottom: `1px solid ${C.border}` }}>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.orange, marginBottom: 10 }}>Example Guide</p>
              <h3 style={{ fontFamily: "var(--font-display, sans-serif)", fontSize: "clamp(20px, 3vw, 28px)", fontWeight: 800, color: C.navy, marginBottom: 16, letterSpacing: "-0.5px", lineHeight: 1.2 }}>
                Front Brake Pad Replacement — 2015 Honda Civic EX
              </h3>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {[["Moderate", "#F3F4F6", C.body], ["⏱ 1.5 – 2 hours", "#F3F4F6", C.body], ["💰 $45 – $90 (parts)", "#F3F4F6", C.body]].map(([label, bg, color]) => (
                  <span key={label} style={{ background: bg, color, fontSize: 13, fontWeight: 500, padding: "6px 12px", borderRadius: 8, border: `1px solid ${C.border}`, fontFamily: "var(--font-mono, monospace)" }}>{label}</span>
                ))}
              </div>
            </div>

            {/* Safety */}
            <div style={{ padding: "20px 32px", borderBottom: `1px solid ${C.border}`, background: "#FFF8F8" }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: "#dc2626", marginBottom: 12, display: "flex", alignItems: "center", gap: 8, letterSpacing: 0.5, textTransform: "uppercase" as const }}>
                ⚠ Safety First
              </p>
              <ul style={{ listStyle: "disc", paddingLeft: 20, display: "flex", flexDirection: "column", gap: 8 }}>
                {["Always use jack stands — never rely on a hydraulic jack alone.", "Brake dust is harmful — avoid inhaling it and wash hands after.", "Bed in new pads gradually; avoid hard stops for the first 200 miles."].map(w => (
                  <li key={w} style={{ fontSize: 14, color: C.body, lineHeight: 1.5, fontFamily: "var(--font-mono, monospace)" }}>{w}</li>
                ))}
              </ul>
            </div>

            {/* Tools + Parts */}
            <div className="lp-tools-grid" style={{ borderBottom: `1px solid ${C.border}` }}>
              <div style={{ padding: "22px 32px", borderRight: `1px solid ${C.border}` }}>
                <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.muted, marginBottom: 14 }}>Tools</p>
                {["Floor jack", "Jack stands (x2)", "19mm lug socket", "12mm & 14mm sockets", "C-clamp or caliper piston tool", "Torque wrench", "Wire brush"].map(t => (
                  <div key={t} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                    <span style={{ color: C.orange, fontSize: 11, flexShrink: 0 }}>▶</span>
                    <span style={{ fontSize: 14, color: C.body, fontFamily: "var(--font-mono, monospace)" }}>{t}</span>
                  </div>
                ))}
              </div>
              <div style={{ padding: "22px 32px" }}>
                <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.muted, marginBottom: 14 }}>Parts</p>
                {["Front brake pads (semi-metallic or ceramic)", "Brake cleaner spray", "Caliper grease packet"].map(t => (
                  <div key={t} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                    <span style={{ color: C.orange, fontSize: 11, flexShrink: 0 }}>▶</span>
                    <span style={{ fontSize: 14, color: C.body, fontFamily: "var(--font-mono, monospace)" }}>{t}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Steps */}
            {SAMPLE_STEPS.map(s => (
              <div key={s.n} style={{ padding: "22px 32px", borderBottom: `1px solid ${C.border}`, display: "flex", gap: 20, alignItems: "flex-start" }}>
                <div style={{ background: C.navy, color: "#fff", fontWeight: 700, fontSize: 14, borderRadius: 10, width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, letterSpacing: 0.5 }}>{s.n}</div>
                <div>
                  <h4 style={{ fontSize: 16, fontWeight: 700, color: C.orange, marginBottom: 6 }}>{s.title}</h4>
                  <p style={{ fontSize: 14, color: C.body, lineHeight: 1.65, fontFamily: "var(--font-mono, monospace)" }}>{s.body}</p>
                </div>
              </div>
            ))}

            {/* Sources */}
            <div style={{ padding: "22px 32px" }}>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.4, textTransform: "uppercase" as const, color: C.muted, marginBottom: 14 }}>Sources</p>
              <div className="lp-sources-grid">
                {[
                  { icon: "📺", text: "ChrisFix — How to Change Brake Pads (Front)" },
                  { icon: "📺", text: "EricTheCarGuy — Brake Job Basics" },
                  { icon: "💬", text: "9thCivic.com — 9th Gen Front Brake Pad DIY Thread" },
                  { icon: "💬", text: "r/MechanicAdvice — Civic squeaking after pad swap" },
                ].map(src => (
                  <div key={src.text} style={{ background: C.cream, border: `1px solid ${C.border}`, borderRadius: 10, padding: "10px 14px", display: "flex", gap: 10, alignItems: "center" }}>
                    <span style={{ fontSize: 14, flexShrink: 0 }}>{src.icon}</span>
                    <span style={{ fontSize: 13, color: C.body, fontFamily: "var(--font-mono, monospace)", lineHeight: 1.4 }}>{src.text}</span>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: 12, color: C.muted, textAlign: "center", marginTop: 24, fontFamily: "var(--font-mono, monospace)", lineHeight: 1.6 }}>
                Sample guide for illustration. AI-generated guides are informational;<br />always verify torque specs against your vehicle's service manual.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────── */}
      <footer style={{ background: C.navy, padding: "40px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{ width: 36, height: 36, background: C.orange, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>🔧</div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginRight: 24 }}>
            <span style={{ fontWeight: 800, fontSize: 16, color: "#fff", letterSpacing: "-0.3px" }}>WrenchAI</span>
          </div>
          <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6, fontFamily: "var(--font-mono, monospace)", maxWidth: 680 }}>
            Guides are AI-generated and informational. Always follow your vehicle service manual and consult a professional for safety-critical repairs.
          </p>
        </div>
      </footer>

    </div>
  );
}
