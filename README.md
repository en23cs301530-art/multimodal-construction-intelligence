# Multimodal Construction Intelligence Platform
Skill Wallet Capstone Project 1

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Gemini API key
Enter a Google Gemini API key in the sidebar, or set `GOOGLE_API_KEY` in your environment.
Without a key, the app runs in demonstration mode. The app does not persist the key to disk.

## Streamlit Community Cloud
1. Push `app.py` and `requirements.txt` to a GitHub repository.
2. Create a Streamlit Community Cloud app pointing at `app.py`.
3. For key-based inference, add `GOOGLE_API_KEY` under app secrets, or use the in-app password field.

## Important notes
- Safety and defect assessments are visual triage only; image limitations and occlusion can cause false negatives.
- Crack widths and planning quantities are illustrative estimates, not surveyed measurements or a bill of quantities.
- Budget rates, material coefficients, and valuation multipliers are editable conceptual assumptions.
- OSHA / IS 456 references are context, not a compliance certificate. Have a competent professional validate decisions.
- No external database is required. Chat history is session-scoped.
