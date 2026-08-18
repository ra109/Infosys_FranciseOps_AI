# Agentic AI for Franchise Management System with Performance Monitoring Assistance
### Codename: FranchiseOps AI

**An agentic decision-support copilot for multi-outlet franchise networks — grounded, never fabricated.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/streamlit-app-red) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents
1. [Program & Team Context](#program--team-context)
2. [Project Explanation](#project-explanation)
3. [Architecture](#architecture)
4. [Specialised Agents](#specialised-agents)
5. [Authentication, OTP & Security](#authentication-otp--security)
6. [Admin Dashboard](#admin-dashboard)
7. [Screenshots](#screenshots)
8. [Installation & Run Instructions](#installation--run-instructions)
9. [requirements.txt](#requirementstxt)
10. [Demo Video](#demo-video)
11. [Known Limitations & Future Scope](#known-limitations--future-scope)
12. [Acknowledgements](#acknowledgements)

---

## Program & Team Context

- **Program:** Infosys Springboard Internship — Batch 1
- **Mentor:** `[MOHAMEDSIPLI M and Project Mentor]`

| Name | Role / What They Built | GitHub Handle |
|---|---|---|
| Raghuvansh Pandey | Full-stack + ML — auth, DB, ML agents, LLM/RAG layer, admin dashboard | [@ra109](https://github.com/ra109) |
| `[FILL IN]` | `[FILL IN]` | `[FILL IN]` |

---

## Project Explanation

**Problem statement:** Franchise networks generate data across HR, sales, inventory, marketing, and compliance at every outlet, but managers rarely get a single grounded view of what's happening across the network — decisions are made on gut feel or scattered spreadsheets. FranchiseOps AI gives franchise owners, regional managers, and store staff a single conversational copilot backed by real SQL data and trained ML models, instead of a hallucinating chatbot.

**Solution summary:** FranchiseOps AI is a multi-agent analytics platform where each agent owns one business domain (workforce, outlets, inventory) and combines SQL aggregation with a benchmarked ML model. A LangChain + ChromaDB RAG layer grounds free-text questions in real documents and data, and a quantized Qwen2.5-3B-Instruct LLM generates the final answer — constrained to retrieved facts only, with a 1.5B fallback if VRAM is tight. Everything sits behind JWT/bcrypt authentication with email OTP recovery, and an admin dashboard gives visibility into users, model performance, and system health.

**Key differentiators:**
- Grounded generation — no hallucinated numbers, answers are constrained to retrieved SQL/RAG facts
- Transparent ML — multiple models benchmarked per agent, not a single black box
- Role-aware access (RBAC)
- Fail-soft LLM degrade path (3B → 1.5B) if GPU memory is insufficient

---

## Architecture

![Architecture](docs/architecture-diagram.png)

**1. Data Layer** — `seed_data.py` populates SQLite (`db.py`) with outlet, staff, inventory, and related records.

**2. Reasoning Tools Layer** — Each agent module combines SQL aggregation with a benchmarked ML model and Plotly visualisations.

**3. Orchestration Layer** — Routes each question to the right agent, pulls grounded SQL facts, and falls back to ChromaDB/RAG retrieval for document or policy questions.

**4. Generation Layer** — `llm_engine_franchise.py` runs Qwen2.5-3B-Instruct (4-bit quantized), strictly constrained to retrieved facts, with automatic fallback to a smaller model under VRAM pressure.

### Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend / App | Streamlit | UI, session state, chat interface |
| Database | SQLite (`db.py`) | Outlets, staff, inventory, audit records |
| Auth | JWT + bcrypt | Session tokens, password hashing |
| OTP / Recovery | Gmail SMTP | OTP delivery, progressive lockout, resend rate limiting |
| ML | scikit-learn | Attrition prediction, outlet clustering, demand forecasting |
| LLM | Qwen2.5-3B-Instruct (4-bit, bitsandbytes) | Grounded answer generation |
| RAG | LangChain + ChromaDB | Document/policy retrieval |
| Deployment | ngrok | Public tunnel from Google Colab |
| Compute | Google Colab (Tesla T4, 15GB VRAM) | Training + hosting |

---

## Specialised Agents

| # | Agent | Business Function | ML Models Benchmarked | Output |
|---|---|---|---|---|
| 1 | Workforce & Retention Intelligence | Predicts which employees are at risk of leaving | `[FILL IN — models tried]` (best model selected after fixing a data-leakage bug: `Termd`/`EmploymentStatus` columns were leaking the target label and were removed) | Risk score, segmentation chart |
| 2 | Outlet Intelligence & Revenue Analytics | Clusters outlets and simulates revenue scenarios | `[FILL IN — models tried]` | Cluster chart, revenue simulation |
| 3 | Inventory Intelligence & Demand Forecasting | Forecasts SKU demand, flags stock-out risk | `[FILL IN — models tried]` | Demand forecast chart, alerts |

Each agent reads from the relevant SQLite tables seeded by `seed_data.py` and surfaces its output inline in the Streamlit UI via Plotly.

> The full spec calls for 9 agents (adding Marketing ROI, Sentiment, Audit & Compliance, Executive Digest, SOP Translation, and Document RAG Studio). These are documented under [Future Scope](#known-limitations--future-scope) — the RAG/document Q&A capability is already partially covered by the LangChain + ChromaDB layer powering the copilot.

---

## Authentication, OTP & Security

**Flow:** signup → login → JWT session → forgot password → OTP (email) → security question fallback → reset. OTP requests are rate-limited on resend, with progressive lockout after repeated failed attempts.

All credentials and secrets are configured via environment variables and are never committed to the repo — see the Security Checklist below.

| Role | Typical Access |
|---|---|
| Admin | All tabs, including the Admin Dashboard and full agent suite |
| Franchise Owner / Regional Ops Manager | All agents and the AI Copilot, excluding the Admin Dashboard |
| Store Manager | AI Copilot + a subset of operational agents |
| Staff | AI Copilot plus one or two directly relevant agents only |

---

## Admin Dashboard

`admin_dash.py` provides:
- User management & role assignment
- System health (DB / LLM / translation engine status)
- ML model performance ledger (accuracy/F1/R² per agent)
- Chat history & audit trail across users

`[FILL IN — add admin dashboard screenshot]`

---

## Screenshots

`[FILL IN — add 3–6 screenshots: login, main dashboard, one agent tab, chat copilot answering a grounded question, admin dashboard]`

---

## Installation & Run Instructions

### Run locally

```bash
# 1. Clone the repository
git clone https://github.com/ra109/Infosys_FranciseOps_AI.git
cd Infosys_FranciseOps_AI

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then open .env and fill in YOUR OWN values — see Security Checklist below

# 5. Seed the database (first run only)
python seed_data.py

# 6. Run the app
streamlit run app.py
```

### Run on Google Colab

The project was primarily developed and run on Google Colab (Tesla T4 GPU).

1. Open the notebook: `[FILL IN — Colab notebook link]`
2. Add the following as Colab **Secrets** (key icon in left sidebar): `JWT_SECRET_KEY`, `ADMIN_EMAIL_ID`, `ADMIN_PASSWORD`, `NGROK_AUTHTOKEN`, `HF_TOKEN`, `EMAIL_ID`, `EMAIL_PASSWORD`, `KAGGLE_USERNAME`, `KAGGLE_KEY`
3. Run cells in order: install dependencies → export secrets to `os.environ` (required — `google.colab.userdata.get()` cannot be called from inside the `streamlit run` subprocess) → seed database → launch Streamlit via ngrok tunnel.

**Minimum requirements:** Python 3.10+, ~15GB VRAM for Qwen2.5-3B (4-bit quantized); auto-degrades to a 1.5B model if VRAM is insufficient.

---

## requirements.txt

Generate from a clean virtual environment after a full successful run:

```bash
pip freeze > requirements.txt
```

Group with comments for readability, e.g.:

```
# Core
streamlit==1.37.0

# ML
scikit-learn==1.5.1

# LLM & NLP
transformers==4.44.0
bitsandbytes==0.43.1
langchain==0.2.11
chromadb==0.5.5

# Auth
bcrypt==4.2.0
pyjwt==2.9.0

# Reporting / Visualization
plotly==5.23.0
```

Expected install time: `[FILL IN]` | Disk space: `[FILL IN — LLM weights can be several GB]`

Test in a brand-new empty venv before submitting.

---

## Demo Video

`docs/demo/demo.mp4` — `[FILL IN — or Google Drive/YouTube unlisted link if too large for GitHub]`

Silent screen recording, 2–5 minutes, 720p, recorded with a **dummy account** (no real Gmail credentials or real OTP inbox on screen). Shows: login → OTP forgot-password flow → a core agent → the chat copilot → the admin dashboard.

---

## Known Limitations & Future Scope

**Limitations:**
- Synthetic/seeded data only, not connected to a live franchise's real data
- Single-tenant — one deployment per franchise network
- SQLite instead of a production-grade database (e.g. PostgreSQL)
- Currently 3 of the 9 planned specialised agents are implemented

**Future Scope:**
- Marketing ROI Intelligence agent (campaign ROI, CAC analytics)
- Customer Sentiment & Feedback Analytics agent
- Audit & Compliance Intelligence agent (FSSAI checklist, violation tracking)
- Executive Franchise Intelligence Digest (network-wide rollup)
- Multilingual SOP Translation (NLLB-200)
- Dedicated PDF SOP & Franchise Agreement RAG Studio (upload-your-own-document workbench)

---

## Acknowledgements

Built as part of the **Infosys Springboard Internship — Batch 1**. Thanks to `[FILL IN — mentor name]` for guidance throughout.

---

## Security Checklist (read before pushing)

**Environment variables required** (names only — never commit real values):

| Variable | Purpose | Where to get it |
|---|---|---|
| `HF_TOKEN` | Hugging Face token to download Qwen2.5 model weights | huggingface.co → Settings → Access Tokens |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | Kaggle API credentials for dataset pulls | kaggle.com → Account → Create New API Token |
| `EMAIL_ID` | Sending mailbox for OTP emails | A dedicated project mailbox, not personal |
| `EMAIL_PASSWORD` | Gmail App Password (NOT the real account password) for SMTP | Google Account → Security → App Passwords (2FA required) |
| `JWT_SECRET_KEY` | Signing key for session tokens | `python -c "import secrets;print(secrets.token_hex(32))"` |
| `ADMIN_EMAIL_ID` / `ADMIN_PASSWORD` | Seed admin account credentials | Set locally, never commit |
| `NGROK_AUTHTOKEN` | Tunnel auth for Colab deployment | ngrok.com dashboard |

**Never commit:** real HF/Kaggle tokens, a real Gmail password, any `.env` with real values, or database dumps with real personal data. If a secret is ever accidentally committed, **revoke and rotate it immediately** — deleting the line in a later commit is not enough, it stays in git history.

Add `.env` to `.gitignore` before your first commit, and verify with:
```bash
git check-ignore -v .env
```
