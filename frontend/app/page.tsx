"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { detectIntent } from "@/lib/api";

const MAKES = ["Toyota","Honda","Ford","Chevrolet","Nissan","Subaru","Jeep","BMW","Mercedes","Hyundai","Kia","Mazda","Ram","GMC","Dodge","Volkswagen","Audi"];
const YEARS = Array.from({ length: 35 }, (_, i) => 2024 - i);

export default function Home() {
  const router = useRouter();
  const [year,   setYear]   = useState(2019);
  const [make,   setMake]   = useState("Toyota");
  const [model,  setModel]  = useState("");
  const [engine, setEngine] = useState("");
  const [query,  setQuery]  = useState("");
  const [loading, setLoading] = useState(false);
  const [error,  setError]  = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!model.trim()) { setError("Enter your vehicle model"); return; }
    if (!query.trim()) { setError("Describe what you need help with"); return; }
    setError("");
    setLoading(true);

    try {
      const vehicleDesc = `${year} ${make} ${model}${engine ? ` (${engine})` : ""}`;
      const intent = await detectIntent(query, vehicleDesc);
      const repair = intent.repair_query || query;

      const state = { make, model, year, engine, desc: vehicleDesc, repair };
      sessionStorage.setItem("vehicleState", JSON.stringify(state));
      router.push("/building");
    } catch {
      setError("Something went wrong. Check that the server is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ minHeight: "100dvh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px 16px" }}>
      <div style={{ width: "100%", maxWidth: 480 }}>

        {/* Logo / wordmark */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>🔧</div>
          <h1 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.8px", color: "var(--text)" }}>
            Fix it yourself.
          </h1>
          <p style={{ fontSize: 16, color: "var(--muted)", marginTop: 8, lineHeight: 1.5 }}>
            AI walks you through any repair, step by step.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Vehicle row */}
          <div className="card" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
            <span className="label">Your vehicle</span>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <select className="input" value={year} onChange={e => setYear(Number(e.target.value))}>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <select className="input" value={make} onChange={e => setMake(e.target.value)}>
                  {MAKES.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
            </div>
            <input
              className="input"
              placeholder="Model — e.g. Camry, F-150, Civic"
              value={model}
              onChange={e => setModel(e.target.value)}
            />
            <input
              className="input"
              placeholder="Engine (optional) — e.g. 2.5L 4-cyl"
              value={engine}
              onChange={e => setEngine(e.target.value)}
            />
          </div>

          {/* Query */}
          <div className="card" style={{ padding: 20 }}>
            <span className="label">What do you need?</span>
            <textarea
              className="input"
              rows={3}
              placeholder={"\"replace brake pads\"  or  \"my brakes are squealing\""}
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
          </div>

          {error && (
            <p style={{ color: "var(--red)", fontSize: 14, textAlign: "center" }}>{error}</p>
          )}

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "One moment..." : "Let's Go →"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: 12, color: "var(--muted)", marginTop: 24 }}>
          Guides built from real repair manuals, YouTube, and community knowledge.
        </p>
      </div>
    </main>
  );
}
