"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { buildGuide } from "@/lib/api";

const STEPS = [
  { icon: "🌐", label: "Searching repair guides" },
  { icon: "📺", label: "Fetching video transcripts" },
  { icon: "💬", label: "Reading community tips" },
  { icon: "🤖", label: "Synthesizing with AI" },
  { icon: "✅", label: "Verifying specs" },
];

export default function BuildingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [vehicle, setVehicle] = useState("");
  const [repair, setRepair]   = useState("");
  const [error, setError]     = useState("");

  useEffect(() => {
    const raw = sessionStorage.getItem("vehicleState");
    if (!raw) { router.push("/"); return; }

    const state = JSON.parse(raw);
    setVehicle(state.desc);
    setRepair(state.repair);

    // Animate steps while building
    let i = 0;
    const interval = setInterval(() => {
      i++;
      if (i < STEPS.length) setStep(i);
    }, 7000);

    const timeout = setTimeout(() => {
      clearInterval(interval);
      setError("This is taking too long. Check that the server is running and try again.");
    }, 90000);

    buildGuide(state.make, state.model, state.year, state.repair, state.engine)
      .then(guide => {
        clearInterval(interval);
        clearTimeout(timeout);
        sessionStorage.setItem("guide", JSON.stringify(guide));
        router.push("/preflight");
      })
      .catch(() => {
        clearInterval(interval);
        clearTimeout(timeout);
        setError("Couldn't build the guide. Try again.");
      });

    return () => { clearInterval(interval); clearTimeout(timeout); };
  }, [router]);

  if (error) return (
    <main style={{ minHeight: "100dvh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ textAlign: "center" }}>
        <p style={{ color: "var(--red)", fontSize: 18, marginBottom: 24 }}>{error}</p>
        <button className="btn-ghost" onClick={() => router.push("/")}>← Try again</button>
      </div>
    </main>
  );

  return (
    <main style={{ minHeight: "100dvh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px 16px" }}>
      <div style={{ width: "100%", maxWidth: 420, textAlign: "center" }}>

        {/* Pulsing icon */}
        <div style={{ fontSize: 52, marginBottom: 32, animation: "pulse 2s infinite" }}>⚙️</div>

        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Building your guide</h2>
        {vehicle && (
          <p style={{ color: "var(--muted)", fontSize: 15, marginBottom: 8 }}>{vehicle}</p>
        )}
        {repair && (
          <p style={{ color: "var(--green)", fontSize: 14, fontWeight: 600, marginBottom: 40 }}>
            {repair}
          </p>
        )}

        {/* Steps */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, textAlign: "left" }}>
          {STEPS.map((s, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 14,
              padding: "14px 16px",
              background: i === step ? "var(--surface2)" : i < step ? "transparent" : "transparent",
              borderRadius: 12,
              border: i === step ? "1px solid var(--green-dim)" : "1px solid transparent",
              transition: "all 0.4s",
              opacity: i > step ? 0.3 : 1,
            }}>
              <span style={{ fontSize: 20 }}>{i < step ? "✓" : s.icon}</span>
              <span style={{
                fontSize: 15,
                fontWeight: i === step ? 600 : 400,
                color: i < step ? "var(--muted)" : i === step ? "var(--text)" : "var(--muted)",
              }}>
                {s.label}
                {i === step && <span style={{ color: "var(--green)" }}> ...</span>}
              </span>
            </div>
          ))}
        </div>

        <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 32 }}>
          Takes about 30–60 seconds on first build.
          <br />Cached guides load instantly.
        </p>
      </div>

      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }`}</style>
    </main>
  );
}
