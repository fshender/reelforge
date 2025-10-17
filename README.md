# ReelForge — Short-Form Content Generator

ReelForge turns any blog URL or pasted text into **3 video scripts**, **caption variants**, **hooks**, **CTAs**, and **hashtag sets** tailored to a niche. Perfect for creators, indie founders, agencies.

## One‑click deploy (Streamlit Cloud)
1) Fork/upload this project to GitHub *or* upload the zip directly to Streamlit Cloud.
2) Add the following **Secrets** in Streamlit Cloud:
   - `OPENAI_API_KEY = "sk-..."`
   - `STRIPE_CHECKOUT_URL = "https://buy.stripe.com/..."` (create a Product in Stripe → Pricing → Payment link)
   - Optional: `ADMIN_EMAIL = "you@yourdomain.com"` (for lead notifications)
3) Set app file to `app.py` and Python version 3.11+.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```
## Features
- URL scraping via `readability-lxml` + requests; or paste raw text.
- Presets for platforms: **TikTok, Reels, YT Shorts** (timed beats, hook-first).
- Exports: copy-to-clipboard + JSON download.
- Simple email capture for early users (CSV stored server-side; replace with Airtable/Zapier if you like).

---
**Note:** This app uses OpenAI's GPT models. Add your API key via Streamlit secrets.
