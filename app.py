import streamlit as st
import requests
from bs4 import BeautifulSoup
from readability import Document
import json, re, time
from typing import List, Dict, Any
import tiktoken
import os

# --- Config
st.set_page_config(page_title="ReelForge — Shorts Script Generator", page_icon="🎬", layout="wide")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
STRIPE_CHECKOUT_URL = st.secrets.get("STRIPE_CHECKOUT_URL", "")
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "")

# --- Helpers
def fetch_url_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        doc = Document(r.text)
        html = doc.summary()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")
        return re.sub(r"\n{2,}", "\n\n", text).strip()
    except Exception as e:
        return ""

def token_count(s: str) -> int:
    try:
        enc = tiktoken.encoding_for_model("gpt-4o-mini")
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(s or ""))

def call_openai(prompt: str, system: str = "You write viral, platform-specific short-form video scripts with clear beats.") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY or None)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1200,
        top_p=1.0,
        presence_penalty=0.2,
        frequency_penalty=0.2
    )
    return resp.choices[0].message.content

def make_prompt(content: str, niche: str, platform: str, tone: str, cta: str) -> str:
    return f"""
You are ReelForge. Turn the SOURCE into a pack for {platform} in the niche "{niche}".
Tone: {tone}. Audience: beginners to intermediates.
Deliver a compact JSON with keys:
- scripts: array of 3 items. Each has:
  - title
  - hook (<=12 words, punchy)
  - beats: array of steps with {platform}-style timing cues like (0-3s), (3-7s)
  - broll_prompts: array of 3–5 scene prompts
  - caption: 2–3 sentences, line-broken
  - hashtags: 10 niche tags
  - cta: end line; prefer this CTA: "{cta}"
- hooks_alt: 10 alternative hooks
- captions_alt: 5 alt captions
Keep it platform-native (avoid jargon). Avoid apologizing or disclaimers.
SOURCE:
{content[:6000]}
"""

def render_pack(data: Dict[str, Any]):
    st.subheader("Generated Pack")
    st.caption("Copy pieces, or download JSON at the bottom.")
    for i, sc in enumerate(data.get("scripts", []), 1):
        with st.expander(f"🎬 Script {i}: {sc.get('title','')}", expanded=(i==1)):
            st.markdown(f"**Hook:** {sc.get('hook','')}")
            st.markdown("**Beats**")
            for b in sc.get("beats", []):
                st.write("- " + b)
            st.markdown("**B‑roll Prompts**")
            st.write(", ".join(sc.get("broll_prompts", [])))
            st.markdown("**Caption**")
            st.write(sc.get("caption",""))
            st.markdown("**Hashtags**")
            st.write(" ".join("#"+h.strip("#") for h in sc.get("hashtags", [])))
            st.markdown("**CTA**")
            st.write(sc.get("cta",""))

    st.markdown("---")
    st.markdown("**Alt Hooks (10)**")
    st.write("\n".join([f"- {h}" for h in data.get("hooks_alt", [])]))
    st.markdown("**Alt Captions (5)**")
    st.write("\n\n".join([f"- {c}" for c in data.get("captions_alt", [])]))

# --- UI
st.title("🎬 ReelForge")
st.caption("Turn any article or idea into ready-to-post Shorts/Reels/TikTok content.")

colL, colR = st.columns([1.2, 0.8])

with colL:
    src_mode = st.radio("Source type", ["URL", "Paste text"], horizontal=True)
    source_text = ""
    if src_mode == "URL":
        url = st.text_input("Article URL")
        if url:
            with st.spinner("Fetching & extracting..."):
                source_text = fetch_url_text(url)
                if not source_text:
                    st.error("Could not parse that URL. Paste text instead?")
    else:
        source_text = st.text_area("Paste the source text", height=220, help="Paste 300–1500 words for best results.")

    niche = st.text_input("Niche (e.g., bootstrapped SaaS, fitness coaches, skincare)")
    platform = st.selectbox("Platform", ["TikTok", "Instagram Reels", "YouTube Shorts"])
    tone = st.selectbox("Tone", ["educational + punchy", "edgy + witty", "smooth and aspirational", "hype and fast-paced"])
    cta = st.text_input("Preferred CTA line", value="Follow for more breakdowns like this.")

    st.markdown("**Paywall**")
    st.caption("Preview generates 1 full script. Upgrade to unlock 3 scripts, exports, and alt packs.")
    if STRIPE_CHECKOUT_URL:
        st.link_button("💳 Upgrade — Unlock full pack", STRIPE_CHECKOUT_URL, use_container_width=True)
    else:
        st.info("Add STRIPE_CHECKOUT_URL in Streamlit secrets to enable the upgrade button.")

    go = st.button("Generate", type="primary")

with colR:
    st.markdown("### Lead Capture (optional)")
    email = st.text_input("Your email (for updates & freebies)")
    leads_file = "leads.csv"
    if st.button("Save email"):
        if email and "@" in email:
            with open(leads_file, "a") as f:
                f.write(email + "\n")
            st.success("Saved. Thanks!")
        else:
            st.error("Enter a valid email.")

    st.markdown("---")
    st.markdown("### Why this works")
    st.write("""
- Hook-first scripts tailored to platform pacing.
- Focus on teachable beats + B‑roll prompts, so editing is fast.
- Alt hooks/captions for A/B testing.
    """)

# --- Generation
if go:
    if not OPENAI_API_KEY:
        st.error("Add OPENAI_API_KEY in Streamlit secrets to generate.")
    elif not (source_text and niche):
        st.warning("Provide a source (URL or text) and a niche.")
    else:
        preview_mode = True  # default preview is 1 script
        prompt = make_prompt(source_text, niche, platform, tone, cta)
        with st.spinner("Generating..."):
            out = call_openai(prompt)
        try:
            data = json.loads(out)
        except Exception:
            # attempt to extract JSON
            match = re.search(r"\{.*\}", out, flags=re.S)
            data = json.loads(match.group(0)) if match else {"error": "Could not parse JSON", "raw": out}

        # If preview, cut down to 1 script
        if preview_mode and isinstance(data, dict) and "scripts" in data and len(data["scripts"]) > 1:
            data["scripts"] = data["scripts"][:1]

        render_pack(data)

        st.download_button("⬇️ Download JSON", data=json.dumps(data, ensure_ascii=False, indent=2), file_name="reelforge_pack.json", mime="application/json")
