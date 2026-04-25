import streamlit as st
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app.services.knowledge_builder.agent import build_guide
from app.services.guide_session.intent import classify_intent, IntentType
from app.services.guide_session.session import SessionState, chat


# ── helpers ──────────────────────────────────────────────────────────────────

def run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def safety_color(tier: str) -> str:
    return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(tier, "⚪")


def stars(n: int) -> str:
    return "★" * n + "☆" * (5 - n)


# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Vehicle DIY Guide",
    page_icon="🔧",
    layout="wide",
)

st.markdown("""
<style>
.step-box {
    background:#1e1e2e;border-radius:10px;padding:16px;
    margin-bottom:10px;border-left:4px solid #7c3aed;
}
.step-active {
    border-left:4px solid #22c55e;background:#0f2318;
}
.step-done {
    border-left:4px solid #6b7280;opacity:0.6;
}
.chat-user {background:#1e293b;border-radius:8px;padding:10px;margin:4px 0;}
.chat-ai   {background:#0f2318;border-radius:8px;padding:10px;margin:4px 0;border-left:3px solid #22c55e;}
.warning-box {background:#3b1515;border-radius:8px;padding:12px;border-left:4px solid #ef4444;}
.metric-card {background:#1e1e2e;border-radius:8px;padding:12px;text-align:center;}
</style>
""", unsafe_allow_html=True)


# ── session state init ────────────────────────────────────────────────────────

for key, default in {
    "page": "home",
    "vehicle": None,
    "guide_result": None,
    "session": None,
    "chat_history": [],
    "user_input_key": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME — vehicle entry + intent
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.page == "home":
    st.title("🔧 Vehicle DIY Guide")
    st.caption("AI-powered repair guides built for your exact vehicle")

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Your Vehicle")
        year  = st.selectbox("Year",  list(range(2024, 1990, -1)), index=4)
        make  = st.selectbox("Make",  ["Toyota","Honda","Ford","Chevrolet","Nissan","Subaru","Jeep","BMW","Mercedes","Hyundai","Kia","Mazda"])
        model = st.text_input("Model", placeholder="e.g. Camry, Civic, F-150")
        engine = st.text_input("Engine (optional)", placeholder="e.g. 2.5L 4-cyl")

    with col2:
        st.subheader("What do you need?")
        user_query = st.text_area(
            "Describe your repair or problem",
            placeholder="e.g.  'replace brake pads'  or  'my brakes are squealing'",
            height=120,
        )

        skill = st.radio(
            "Your experience level",
            ["Never done this", "Done it before", "Do it regularly"],
            horizontal=True,
        )

    st.divider()

    if st.button("🔍 Build My Guide", type="primary", use_container_width=True):
        if not model:
            st.error("Please enter your vehicle model.")
        elif not user_query:
            st.error("Please describe what you need help with.")
        else:
            vehicle_desc = f"{year} {make} {model}" + (f" ({engine})" if engine else "")
            st.session_state.vehicle = {
                "make": make, "model": model, "year": year,
                "engine": engine or None, "desc": vehicle_desc, "skill": skill
            }

            with st.spinner("Understanding your request..."):
                intent = run(classify_intent(user_query, vehicle_desc))

            if intent.intent_type == IntentType.SYMPTOM and intent.follow_up_questions:
                st.session_state.page = "diagnose"
                st.session_state.intent = intent
                st.session_state.symptom_query = user_query
                st.rerun()
            else:
                repair = intent.repair_query or user_query
                st.session_state.page = "building"
                st.session_state.repair_query = repair
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DIAGNOSE — symptom follow-up
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "diagnose":
    v = st.session_state.vehicle
    intent = st.session_state.intent

    st.title("🔍 Let's Diagnose the Problem")
    st.write(f"**Vehicle:** {v['desc']}")
    st.write(f"**Symptom:** {st.session_state.symptom_query}")
    st.divider()
    st.write("A few quick questions to narrow it down:")

    answers = {}
    for i, q in enumerate(intent.follow_up_questions):
        answers[i] = st.text_input(q, key=f"diag_{i}")

    if st.button("Find the Repair →", type="primary"):
        repair = intent.repair_query or st.session_state.symptom_query
        st.session_state.repair_query = repair
        st.session_state.page = "building"
        st.rerun()

    if st.button("← Back"):
        st.session_state.page = "home"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BUILDING — knowledge builder running
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "building":
    v = st.session_state.vehicle
    repair = st.session_state.repair_query

    st.title("⚙️ Building Your Guide")
    st.write(f"**{v['desc']}** — {repair}")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.info("🌐 Searching repair guides...")
    col2.info("📺 Fetching video transcripts...")
    col3.info("🤖 Synthesizing with AI...")

    with st.spinner(f"Building your guide for the {v['desc']}... (~30-60 seconds)"):
        result = run(build_guide(
            make=v["make"], model=v["model"], year=v["year"],
            repair=repair, engine=v["engine"],
        ))

    if not result.guide:
        st.error("Could not build a guide for this repair. Try rephrasing or check a different repair.")
        if st.button("← Try Again"):
            st.session_state.page = "home"
            st.rerun()
    else:
        st.session_state.guide_result = result
        st.session_state.session = SessionState(
            guide=result.guide,
            vehicle_desc=v["desc"],
        )
        st.session_state.chat_history = []
        st.session_state.page = "preflight"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PRE-FLIGHT — tools, parts, warnings before starting
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "preflight":
    result = st.session_state.guide_result
    guide  = result.guide
    v      = st.session_state.vehicle

    st.title("📋 Pre-Flight Check")
    st.write(f"**{guide.title}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Difficulty",  stars(guide.difficulty))
    c2.metric("Time",        f"~{guide.time_estimate_minutes} min")
    c3.metric("Safety",      f"{safety_color(guide.safety_tier)} {guide.safety_tier.upper()}")
    c4.metric("Confidence",  f"{guide.confidence_score:.0%}")

    st.divider()

    if guide.safety_tier == "red":
        st.markdown(f"""<div class="warning-box">
        🔴 <strong>SAFETY-CRITICAL REPAIR</strong><br>
        This repair directly affects your vehicle's ability to stop or steer safely.
        Follow every step carefully. If anything seems wrong, stop and consult a professional.
        </div>""", unsafe_allow_html=True)
        st.write("")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Tools You'll Need")
        for tool in guide.tools_required:
            st.checkbox(tool, key=f"tool_{tool}")

    with col2:
        st.subheader("🛒 Parts You'll Need")
        for part in guide.parts_required:
            qty = part.get("quantity", 1)
            label = f"{qty}x {part['name']}"
            if part.get("consumable"):
                label += " *(consumable)*"
            st.checkbox(label, key=f"part_{part['name']}")
            if part.get("notes"):
                st.caption(f"  ↳ {part['notes']}")

    st.divider()

    if guide.warnings:
        st.subheader("⚠️ Before You Start")
        for w in guide.warnings[:4]:
            st.warning(w)

    st.divider()

    if st.button("✅ I'm Ready — Start the Repair", type="primary", use_container_width=True):
        st.session_state.page = "session"
        st.rerun()

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SESSION — step-by-step guided repair with chat
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state.page == "session":
    session = st.session_state.session
    guide   = session.guide

    if session.is_complete:
        st.balloons()
        st.title("✅ Repair Complete!")
        st.write(f"You finished: **{guide.title}**")
        st.success("Log this repair to your maintenance history and monitor for the next few days.")
        if st.button("🏠 Back to Home", type="primary"):
            for k in ["guide_result","session","chat_history","vehicle"]:
                st.session_state[k] = None
            st.session_state.chat_history = []
            st.session_state.page = "home"
            st.rerun()
        st.stop()

    # ── layout ────────────────────────────────────────────────────────────────
    left, right = st.columns([1, 1])

    # ── LEFT: current step ────────────────────────────────────────────────────
    with left:
        current_step = guide.steps[session.current_step]
        total = len(guide.steps)

        # Progress bar
        st.progress(session.current_step / total)
        st.caption(f"Step {session.current_step + 1} of {total} — {guide.title}")

        # THE ONE THING TO DO — big, bold, unmissable
        st.markdown(f"""
<div style="background:#0f2318;border-left:6px solid #22c55e;border-radius:10px;
padding:24px 20px;margin:12px 0;">
<div style="color:#86efac;font-size:13px;font-weight:600;letter-spacing:1px;
text-transform:uppercase;margin-bottom:8px;">Step {current_step['step_number']}</div>
<div style="font-size:22px;font-weight:700;line-height:1.4;color:#f1f5f9;">
{current_step['title']}</div>
<div style="font-size:15px;color:#cbd5e1;margin-top:12px;line-height:1.6;">
{current_step['instruction']}</div>
</div>""", unsafe_allow_html=True)

        # Critical info only — inline, compact
        if current_step.get("warning"):
            st.error(f"⚠️ {current_step['warning']}")
        if current_step.get("torque_spec"):
            st.warning(f"🔩 Torque: **{current_step['torque_spec']}**")

        # Step image
        images = current_step.get("images", [])
        if images:
            valid = [i for i in images if i.get("url", "").startswith("http")]
            if valid:
                st.image(valid[0]["url"], use_container_width=True)
                if len(valid) > 1:
                    with st.expander("More photos"):
                        for img in valid[1:]:
                            st.image(img["url"], use_container_width=True)

        # Optional detail collapsed
        with st.expander("Why this step?"):
            st.write(current_step.get("why", "—"))
        if current_step.get("tool_needed"):
            st.caption(f"🔧 {current_step['tool_needed']}")

        st.write("")
        if st.button("✅  Done — Next Step", type="primary", use_container_width=True):
            if session.current_step < total - 1:
                session.completed_steps.append(session.current_step)
                session.current_step += 1
                st.rerun()
            else:
                session.is_complete = True
                st.rerun()

        # Step progress dots
        st.write("")
        dots = ""
        for i in range(total):
            if i in session.completed_steps:
                dots += "🟢"
            elif i == session.current_step:
                dots += "🔵"
            else:
                dots += "⚪"
        st.caption(dots)

    # ── RIGHT: AI chat ────────────────────────────────────────────────────────
    with right:
        st.subheader("💬 Ask Your AI Mechanic")
        st.caption(f"Knows your exact vehicle and current step. Ask anything.")

        chat_container = st.container(height=480)
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown(
                    f'<div class="chat-ai">👋 I\'m here to help with your <strong>{guide.title}</strong>. '
                    f'We\'re on Step {session.current_step + 1}: <em>{current_step["title"]}</em>. '
                    f'Ask me anything — what you see, what\'s confusing, what tool to use.</div>',
                    unsafe_allow_html=True
                )
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

        user_msg = st.chat_input("Ask something mid-repair...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.spinner("..."):
                response = run(chat(session, user_msg))
            st.session_state.chat_history.append({"role": "assistant", "content": response.message})
            if response.safety_flag:
                st.error("⚠️ Safety flag raised — read the AI response carefully before continuing.")
            st.rerun()
