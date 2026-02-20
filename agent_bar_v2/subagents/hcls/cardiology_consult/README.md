# Cardiology Consult Agent

A **cardiology consult agent** uses patient data fed by user to **predict and identify cardiac risks** for **early detection**.

## What it does

- **10-year ASCVD risk**: Estimates 10-year atherosclerotic cardiovascular disease risk from demographics and risk factors (age, sex, cholesterol, BP, smoking, diabetes) and returns a risk category (low / borderline / intermediate / high).
- **Risk factor assessment**: Takes vitals, labs, and lifestyle data (including partial data) and lists risk factors, modifiable vs non-modifiable, with brief recommendations.
- **Lab trend interpretation**: Compares current vs prior values for a lab or vital and flags improving or worsening trends.

The agent is designed to support **early** risk stratification and to encourage follow-up with a clinician and routine screening—**not** to replace clinical judgment or full ASCVD calculators.

## Repository

## Prerequisites

- Python 3.10+
- [pip](https://pip.pypa.io/) or [uv](https://docs.astral.sh/uv/)

## Setup

1. **Clone or copy** this project and go into the agent directory:

   ```bash
   cd cardiology-consult-agent
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install the agent and ADK** in editable mode:

   ```bash
   pip install -e .
   ```

   Or with uv:

   ```bash
   uv sync
   ```

4. **Configure credentials**

   - Copy `.env.example` to `.env`.
   - For **Vertex AI**: set `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION` in `.env` and run `gcloud auth application-default login`.

## Run the agent

From the **parent** of `cardiology-consult-agent` :

```bash
# CLI
adk run cardiology-consult-agent

# Web UI (e.g. http://localhost:8000)
adk web --port 8000
```

Then select **cardiology-consult-agent** (or the name shown in the UI) and chat. Example prompts:

- *“I’m 55, male, total cholesterol 220, HDL 45, systolic BP 142, on BP meds, non-smoker, no diabetes. What’s my 10-year cardiac risk?”*
- *“Assess my risk factors: age 52, BMI 31, BP 138/88, LDL 165, I smoke and don’t exercise.”*
- *“My LDL was 160 last year and is 148 now. Is that improving?”*


## Disclaimer

This agent is for **demonstration and risk stratification support** only. It is **not** a medical device and must **not** be used as the sole basis for clinical decisions. Always follow local guidelines and clinician judgment. The simplified ASCVD-style logic in the tools is illustrative.
