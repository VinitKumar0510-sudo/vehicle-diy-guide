const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function detectIntent(query: string, vehicleDesc: string) {
  const res = await fetch(`${BASE}/api/guides/intent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, vehicle_desc: vehicleDesc }),
  });
  return res.json();
}

export async function buildGuide(make: string, model: string, year: number, repair: string, engine?: string) {
  const res = await fetch(`${BASE}/api/guides/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ make, model, year, repair, engine }),
  });
  if (!res.ok) throw new Error("Failed to build guide");
  return res.json();
}

export async function startSession(sessionId: string, guide: object, vehicleDesc: string) {
  const res = await fetch(`${BASE}/api/session/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, guide, vehicle_desc: vehicleDesc }),
  });
  return res.json();
}

export async function sendChat(sessionId: string, message: string) {
  const res = await fetch(`${BASE}/api/session/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return res.json();
}

export async function nextStep(sessionId: string) {
  const res = await fetch(`${BASE}/api/session/next`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return res.json();
}
