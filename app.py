import json
import os
import re
from datetime import datetime
from typing import Any

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

APP_TITLE = "Multimodal Construction Intelligence Platform"
MODEL_NAME = "gemini-2.5-flash"

st.set_page_config(page_title=APP_TITLE, page_icon="🏗️", layout="wide")

# --------------------------- Styling -----------------------------------------
st.markdown("""
<style>
:root { --brand:#e87924; --ink:#172033; --muted:#64748b; }
.block-container {padding-top:1.5rem; padding-bottom:2rem; max-width:1440px;}
.hero {padding:1.35rem 1.5rem; border-radius:18px; color:white;
background:linear-gradient(120deg,#172033 0%,#273b59 65%,#e87924 150%); margin-bottom:1rem;}
.hero h1 {font-size:2rem; margin:0 0 .3rem 0; color:white;}
.hero p {margin:0; opacity:.9;}
div[data-testid="stMetric"] {background:#f7f8fb; border:1px solid #e7eaf0;
padding:14px 16px; border-radius:14px;}
.status-pill {display:inline-block; padding:5px 11px; border-radius:999px;
font-weight:700; font-size:.85rem; background:#eef2ff; color:#3730a3;}
.status-good {background:#dcfce7;color:#166534;}
.status-warn {background:#fef3c7;color:#92400e;}
.status-bad {background:#fee2e2;color:#991b1b;}
div.stButton>button {border-radius:10px; font-weight:600;}
.small-note {font-size:.86rem;color:#64748b;}
</style>
""", unsafe_allow_html=True)

# --------------------------- Core helpers -----------------------------------
def demo_safety(filename: str) -> dict:
    return {
        "safety_score": 78,
        "overall_status": "Needs Improvement",
        "ppe_detection": {
            "helmet": {"observed": "Partially visible", "compliant": False, "confidence": 0.62},
            "high_visibility_vest": {"observed": "Visible on some workers", "compliant": False, "confidence": 0.71},
            "steel_toe_boots": {"observed": "Not verifiable from image", "compliant": None, "confidence": 0.30},
            "safety_harness": {"observed": "Not verifiable / not applicable unless elevated work", "compliant": None, "confidence": 0.38}
        },
        "hazards": [
            {"hazard": "Unprotected edge / fall exposure", "severity": "High",
             "remedy": "Install compliant guardrails or a verified fall-arrest system; restrict access until controlled."},
            {"hazard": "PPE visibility incomplete", "severity": "Medium",
             "remedy": "Verify each worker's helmet, high-visibility clothing and protective footwear during a site walk."}
        ],
        "limitations": "Demonstration result only; no image model was called."
    }

def demo_crack(filename: str) -> dict:
    return {
        "defect_type": "Hairline",
        "estimated_crack_width_mm": 0.3,
        "confidence": 0.48,
        "possible_root_causes": ["Drying shrinkage", "Thermal movement", "Surface finish / curing variation"],
        "recommended_repairs": [
            "Map and monitor the crack; confirm whether it is active.",
            "For a stable non-structural hairline crack, use a compatible surface sealant after substrate preparation.",
            "Escalate to a licensed structural engineer if the crack widens, leaks, or affects load-bearing elements."
        ],
        "urgency": "Routine monitoring",
        "limitations": "Demonstration result only; crack width cannot be reliably measured from an arbitrary photo."
    }

def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\\s*", "", text, flags=re.I)
    text = re.sub(r"\\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(text[start:end+1])

def gemini_json(api_key: str, image: Image.Image, prompt: str) -> dict:
    if genai is None:
        raise RuntimeError("Gemini SDK is not installed. Install requirements.txt.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, image],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return extract_json(response.text or "")

def safe_model_call(api_key: str, image: Image.Image, prompt: str, fallback):
    if not api_key:
        return fallback()
    try:
        return gemini_json(api_key, image, prompt)
    except Exception as exc:
        st.warning(f"Gemini request failed; showing demonstration output instead. Details: {exc}")
        return fallback()

def json_download(data: dict, name: str):
    raw = json.dumps(data, indent=2, ensure_ascii=False)
    st.download_button("⬇️ Download JSON report", raw, file_name=name,
                       mime="application/json", use_container_width=True)

def status_class(status: str) -> str:
    s = status.lower()
    if any(x in s for x in ["safe", "compliant", "routine", "low"]):
        return "status-good"
    if any(x in s for x in ["critical", "high", "unsafe", "immediate"]):
        return "status-bad"
    return "status-warn"

def show_status(status: str):
    st.markdown(f'<span class="status-pill {status_class(status)}">{status}</span>',
                unsafe_allow_html=True)

def image_uploader(label: str, key: str):
    file = st.file_uploader(label, type=["jpg", "jpeg", "png"], key=key)
    if file:
        try:
            img = Image.open(file).convert("RGB")
            st.image(img, caption=file.name, use_container_width=True)
            return img, file.name
        except Exception as exc:
            st.error(f"Could not read image: {exc}")
    return None, None

def format_inr(value: float) -> str:
    if value >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    if value >= 1_00_000:
        return f"₹{value/1_00_000:.2f} L"
    return f"₹{value:,.0f}"

# --------------------------- Sidebar -----------------------------------------
with st.sidebar:
    st.title("🏗️ Construction IQ")
    st.caption("Skill Wallet Capstone · Project 1")
    key_input = st.text_input("Google Gemini API key", type="password",
                              help="Used only for Gemini requests during this session.")
    api_key = key_input.strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    if api_key:
        st.success("Gemini mode enabled")
    else:
        st.info("Demonstration mode · no API key supplied")
    st.divider()
    st.subheader("Architecture overview")
    st.markdown("""
    **Streamlit UI** → Image / form inputs → **Gemini multimodal inference**

    JSON validation → Results & metrics → Downloadable reports

    Session state keeps chat context. No external database is used.
    """)
    st.divider()
    st.subheader("Feature navigation")
    st.markdown("1. Site Safety & PPE Audit\n2. Crack Diagnostics\n3. Planning & Valuation\n4. Daily Site Assistant")
    st.caption("AI outputs are advisory. Have qualified professionals validate safety and structural decisions.")

# --------------------------- Header ------------------------------------------
st.markdown(f"""<div class="hero"><h1>{APP_TITLE}</h1>
<p>Visual site intelligence · Defect diagnostics · Cost planning · Weather-aware decisions</p></div>""",
            unsafe_allow_html=True)
tabs = st.tabs(["🦺 Site Safety & PPE Audit", "🧱 Crack Diagnostics", "📐 Planning & Valuation", "🌦️ Daily Site Assistant"])

# --------------------------- Tab 1 -------------------------------------------
with tabs[0]:
    st.subheader("Epic 2 · Site Safety & PPE Audit")
    st.write("Upload a site photo to assess visible PPE and apparent hazards. The model must not infer hidden PPE.")
    img, filename = image_uploader("Construction site photo (JPG/PNG)", "safety_image")
    if img and st.button("Run PPE & hazard audit", type="primary", key="audit"):
        prompt = """Act as a cautious construction safety visual assistant. Analyze only what is visible in the image.
Use OSHA construction safety principles and relevant IS 456 context only as general references; do not claim certification
or definitive legal compliance. Return JSON only with keys:
safety_score (integer 0-100), overall_status (Safe / Needs Improvement / Unsafe),
ppe_detection object with helmet, high_visibility_vest, steel_toe_boots, safety_harness; each has observed (string),
compliant (true/false/null), confidence (0-1). Use null if not visible or applicability cannot be established.
hazards array of objects with hazard, severity (Low/Medium/High/Critical), remedy.
Include limitations string. Be conservative and avoid claiming boot or harness detection if not visible."""
        result = safe_model_call(api_key, img, prompt, lambda: demo_safety(filename))
        st.session_state["safety_result"] = result
    result = st.session_state.get("safety_result")
    if result:
        c1,c2,c3 = st.columns(3)
        c1.metric("Safety score", f"{result.get('safety_score','—')}/100")
        c2.metric("Findings", len(result.get("hazards", [])))
        with c3:
            st.markdown("**Overall status**")
            show_status(str(result.get("overall_status", "Not assessed")))
        st.markdown("#### PPE checklist")
        ppe = result.get("ppe_detection", {})
        for name, data in ppe.items():
            with st.container(border=True):
                cols = st.columns([2,2,1])
                cols[0].markdown(f"**{name.replace('_',' ').title()}**")
                cols[1].write(data.get("observed", "Not reported") if isinstance(data,dict) else str(data))
                compliant = data.get("compliant") if isinstance(data,dict) else None
                cols[2].write("✅ Yes" if compliant is True else ("❌ No" if compliant is False else "➖ Unknown"))
        st.markdown("#### Identified hazards")
        for h in result.get("hazards", []):
            with st.container(border=True):
                st.markdown(f"**{h.get('hazard','Hazard')}**")
                show_status(h.get("severity", "Unknown"))
                st.write(h.get("remedy", "Follow site-specific controls and competent-person review."))
        if result.get("limitations"):
            st.caption(result["limitations"])
        json_download(result, "site_safety_ppe_audit.json")

# --------------------------- Tab 2 -------------------------------------------
with tabs[1]:
    st.subheader("Epic 2 · Crack Diagnostics & Structural Integrity")
    st.write("AI-assisted visual classification. A photo alone cannot establish structural capacity or reliably measure width.")
    img, filename = image_uploader("Concrete / wall surface photo (JPG/PNG)", "crack_image")
    if img and st.button("Analyze surface defect", type="primary", key="crack"):
        prompt = """You are a cautious construction defect triage assistant. Inspect visible concrete/wall damage, return JSON only:
defect_type (one of Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling),
estimated_crack_width_mm (number or null; clearly label as visual estimate),
confidence (0-1), possible_root_causes (array of strings), recommended_repairs (array of strings),
urgency (Routine monitoring, Schedule inspection, Prompt engineering assessment, Immediate isolation and assessment),
limitations (string). Never diagnose structural safety from image alone. Include epoxy injection or structural re-grouting
only where appropriate and state that repair selection requires engineer review."""
        result = safe_model_call(api_key, img, prompt, lambda: demo_crack(filename))
        st.session_state["crack_result"] = result
    result = st.session_state.get("crack_result")
    if result:
        c1,c2,c3 = st.columns(3)
        c1.metric("Defect class", result.get("defect_type", "—"))
        width = result.get("estimated_crack_width_mm")
        c2.metric("Estimated width", f"{width} mm" if width is not None else "Not estimable")
        c3.markdown("**Urgency**")
        show_status(result.get("urgency", "Review required"))
        st.markdown("#### Possible root causes")
        for cause in result.get("possible_root_causes", []):
            st.markdown(f"- {cause}")
        st.markdown("#### Recommended engineering actions")
        for action in result.get("recommended_repairs", []):
            st.markdown(f"- {action}")
        if result.get("limitations"):
            st.caption(result["limitations"])
        json_download(result, "crack_diagnostics_report.json")

# --------------------------- Tab 3 -------------------------------------------
with tabs[2]:
    st.subheader("Epic 3 · Planning & Real Estate Valuation")
    st.write("Conceptual planning estimates; adjust local rates, specifications, and quantities before use.")
    with st.form("planning_form"):
        a,b = st.columns(2)
        structure = a.selectbox("Structure type", ["Residential RCC", "Commercial RCC", "Industrial", "Low-rise masonry"])
        area = b.number_input("Built-up area (sq ft)", min_value=100, max_value=2_000_000, value=2500, step=100)
        c,d = st.columns(2)
        tier = c.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
        completion = d.slider("Completion percentage", 0, 100, 35)
        submit_plan = st.form_submit_button("Calculate project estimates", type="primary")
    rates = {"Tier 1": 2600, "Tier 2": 2100, "Tier 3": 1750}
    structure_multiplier = {"Residential RCC":1.0, "Commercial RCC":1.18, "Industrial":1.25, "Low-rise masonry":0.82}
    if submit_plan:
        budget = float(area) * rates[tier] * structure_multiplier[structure]
        incurred = budget * completion / 100
        # Conceptual asset value premium over cost; intended as planning proxy, not appraisal.
        asset_value = budget * {"Tier 1":1.28, "Tier 2":1.16, "Tier 3":1.08}[tier]
        steel_kg = area * (3.8 if structure == "Low-rise masonry" else 4.2 if structure == "Industrial" else 4.0)
        cement_bags = area * (0.38 if structure == "Low-rise masonry" else 0.42)
        st.session_state["plan_result"] = {
            "structure_type":structure, "built_up_sqft":area, "location_tier":tier,
            "completion_percent":completion, "estimated_project_budget_inr":round(budget),
            "capital_expenditure_incurred_inr":round(incurred),
            "conceptual_market_asset_valuation_inr":round(asset_value),
            "estimated_steel_kg":round(steel_kg), "estimated_cement_bags":round(cement_bags),
            "assumptions":"Illustrative unit rates and quantity factors; not a bill of quantities, tender quote, or certified valuation."
        }
    plan = st.session_state.get("plan_result")
    if plan:
        c1,c2,c3 = st.columns(3)
        c1.metric("Total project budget", format_inr(plan["estimated_project_budget_inr"]))
        c2.metric("CapEx incurred", format_inr(plan["capital_expenditure_incurred_inr"]))
        c3.metric("Indicative asset valuation", format_inr(plan["conceptual_market_asset_valuation_inr"]))
        st.markdown("#### Material planning indicators")
        m1,m2 = st.columns(2)
        m1.metric("Estimated steel", f'{plan["estimated_steel_kg"]:,} kg')
        m2.metric("Estimated cement", f'{plan["estimated_cement_bags"]:,} bags')
        st.progress(plan["completion_percent"]/100, text=f'Milestone progress · {plan["completion_percent"]}% complete')
        st.caption(plan["assumptions"])
        json_download(plan, "planning_valuation_estimate.json")
    st.divider()
    st.markdown("#### Conceptual 3D rendering prompt")
    render_prompt = st.text_area("Describe the proposed building", "Modern 3-storey Indian urban residence, RCC frame, shaded balconies, sustainable landscaping, daylight architectural visualization", key="render_prompt")
    pollinations_url = "https://image.pollinations.ai/prompt/" + __import__("urllib.parse").parse.quote(render_prompt)
    st.markdown(f"[Generate conceptual rendering with Pollinations AI]({pollinations_url})")
    st.caption("This opens an external image-generation service. Do not include confidential project details.")

# --------------------------- Tab 4 -------------------------------------------
with tabs[3]:
    st.subheader("Epic 5 · Daily Site Assistant & Weather-Aware Advisory")
    weather = st.selectbox("Current / forecast condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"], key="weather")
    advisories = {
        "Normal": ("Routine controls", "Maintain toolbox talks, housekeeping, PPE checks, equipment inspections, and curing / access controls per method statement."),
        "High Wind": ("Wind alert", "Pause crane lifts and work at height when wind exceeds equipment or site limits. Secure loose materials; consult crane load charts and the lift supervisor."),
        "Heavy Rain": ("Rain alert", "Review excavation stability and drainage; protect electrical systems with suitable RCD/GFCI controls; stop work in flooded or unsafe areas. Protect fresh concrete and reassess curing."),
        "Extreme Heat": ("Heat stress alert", "Provide shade, hydration, acclimatization, work-rest cycles, and buddy monitoring. Schedule strenuous work during cooler hours; respond promptly to heat illness symptoms.")
    }
    title, message = advisories[weather]
    with st.container(border=True):
        st.markdown(f"### ⚠️ {title}")
        st.write(message)
    st.markdown("#### Construction engineering assistant")
    st.caption("Ask about methods, quality checks, sequencing, material estimates, or safe work practices.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    user_q = st.chat_input("Ask a construction engineering question…")
    if user_q:
        st.session_state.chat_history.append({"role":"user", "content":user_q})
        with st.chat_message("user"):
            st.markdown(user_q)
        if api_key and genai is not None:
            try:
                client = genai.Client(api_key=api_key)
                history = []
                for item in st.session_state.chat_history[-12:]:
                    role = "user" if item["role"] == "user" else "model"
                    history.append(types.Content(role=role, parts=[types.Part.from_text(text=item["content"])]))
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=history,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a practical construction engineering assistant. Prioritize safety, distinguish assumptions from codes, and advise qualified professional review for structural or high-risk decisions.",
                        temperature=0.35
                    )
                )
                answer = response.text or "I could not generate a response."
            except Exception as exc:
                answer = f"Gemini unavailable ({exc}). Demonstration response: Follow the approved method statement, applicable codes, and competent-person inspection. Share the structure, materials, and site conditions for a more specific explanation."
        else:
            answer = "Demonstration mode: Follow the approved method statement, applicable local codes, and competent-person inspection. For a specific recommendation, provide the structure type, materials, dimensions, and site conditions. This demo does not call an AI model."
        st.session_state.chat_history.append({"role":"assistant", "content":answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
    if st.session_state.chat_history and st.button("Clear chat history"):
        st.session_state.chat_history = []
        st.rerun()

st.divider()
st.caption("© Multimodal Construction Intelligence Platform · Capstone demonstration · Verify all outputs with qualified site and structural professionals.")
