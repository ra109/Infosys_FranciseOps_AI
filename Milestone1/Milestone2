# FranchiseOps AI — Milestone 2
### Full-Stack AI/ML Integration & Advanced Security Engine

Milestone 2 builds on top of the Milestone 1 Authentication module by unifying it with a multi-agent
ML core and a Generative AI Copilot, and adding three hardening layers on top of security: progressive
account lockout, real-time password strength checking, and a fully functional Admin Dashboard.

---

## 1. What Milestone 2 Adds Over Milestone 1    


Milestone 1 delivered the User Authentication module — JWT sessions, Streamlit UI, SQLite-backed
credentials, and Gmail OTP verification.

Milestone 2 adds:

- **Progressive account lockout** on repeated failed logins (5 / 15 min, then permanent).
- **OTP resend rate limiting** with escalating cooldowns.
- **Real-time password strength checker** (Weak / Average / Good) on signup and reset.
- **Three autonomous ML agents** — Workforce Attrition, Outlet Clustering & Revenue Simulation,
  and Inventory & Weather Demand — each comparing 5+ algorithms before selecting a champion model.
- **Outlet Tiering**, clustering 10 seeded outlets into 4 performance tiers via KMeans.
- **LLM Copilot** powered by Qwen2.5-3B-Instruct (4-bit) that synthesizes the three agents' outputs
  into executive retention plans and structured JSON ERP actions.
- **Admin Dashboard** with Add / Delete / Unlock user lifecycle controls and an ML Model Card tab.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Auth & Sessions | JWT, SQLite, bcrypt |
| Email/OTP | Gmail SMTP |
| ML Agents | scikit-learn (5+ algorithms per agent), KMeans |
| Generative Layer | Qwen2.5-3B-Instruct (4-bit, bitsandbytes) via HuggingFace |
| Data Sourcing | Kaggle API (kagglehub) with synthetic fallback |
| Hosting (dev) | Google Colab (T4 GPU) + ngrok tunnel |

---

## 3. System Architecture

| Phase | Module / Component | Responsibility & Workflow |
|---|---|---|
| **Phase 1: Security Gateway** | Authentication & JWT | Enforces Login, Registration, and Forgot Password (Gmail OTP) before unlocking the UI. Stores hashed credentials and progressive lockout state in SQLite (`users` table). |
| **Phase 2: Domain Intelligence** | 3 Autonomous Agents | Once authenticated, unlocks Agent 1: Workforce Attrition, Agent 2: Outlet Clustering / Revenue, and Agent 3: Inventory & Weather Demand tabs. |
| **Phase 3: Generative Advisory** | LLM Copilot & JSON | Integrates HuggingFace LLM orchestration (`llm_engine_franchise.py`) to synthesize the 3 agents' numerical outputs into executive HR retention plans and structured JSON ERP actions. |
| **Phase 4: System Administration** | Admin Dashboard | Dedicated administrative controls (`admin_dash.py`) restricted exclusively to users authenticated with `role = 'Admin'`. |

---

## 4. Seeded Indian Retail Cities

The Outlet Tiering and Weather Demo pages are localized to 10 seeded outlets across these cities:

| City | Region |
|---|---|
| Mumbai | West |
| Delhi NCR | North |
| Bengaluru | South |
| Hyderabad | South |
| Chennai | South |
| Pune | West |

---

## 5. Repository Structure

```
Infosys Repository/
├── Milestone1/
└── Milestone2/
    ├── FranchiseOps_AI_Milestone2.ipynb
    ├── auth.py
    ├── db.py
    ├── ui_theme.py
    ├── admin_dash.py
    ├── train_m2_franchise.py
    ├── llm_engine_franchise.py
    ├── requirements.txt
    ├── screenshots/
    └── README.md
```

---

## 6. Setup — Colab Runtime, GPU & Secrets

### 6.1 Enable GPU

Qwen2.5-3B-Instruct (4-bit quantized) powers the AI Copilot page and needs a GPU runtime:

1. `Runtime → Change runtime type → T4 GPU → Save`
2. Run `!nvidia-smi` as the first cell to confirm the GPU is attached.
3. The model loads with `load_in_4bit=True` (bitsandbytes) to keep VRAM usage low.

### 6.2 Kaggle API Setup (Recommended)

Enables real HR data (IBM HR Attrition + HRDataset v14) instead of synthetic data. The notebook
still works without it.

1. Log in at [kaggle.com](https://kaggle.com) → profile picture → **Settings → API → Create New Token**.
2. This downloads `kaggle.json` (username + key).
3. Add both as Colab Secrets (below), or upload the file to `~/.kaggle/kaggle.json`.

### 6.3 Colab Secrets (never hard-code these)

Click the 🔑 **Secrets** icon in the left sidebar, add each below, and toggle notebook access **ON**.

| Secret Name | How to Get It | Used For |
|---|---|---|
| `JWT_SECRET_KEY` | Any long random string you make up | Signs & verifies login session tokens |
| `ADMIN_EMAIL_ID` | Any email you choose (fallback: `infosys@ai`) | Bootstraps the admin account |
| `ADMIN_PASSWORD` | Any password meeting the strength rule | Bootstraps the admin account |
| `NGROK_AUTHTOKEN` | Free account at ngrok.com → dashboard | Public HTTPS URL for the Streamlit app |
| `HF_TOKEN` | HuggingFace → Settings → Access Tokens | Authenticates Qwen2.5-3B (4-bit) inference |
| `EMAIL_ID` | Gmail address to send from | Sender for OTP/digest/alert emails (optional) |
| `EMAIL_PASSWORD` | Gmail → 2-Step Verification → App Passwords | Authenticates Gmail SMTP sender |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | From `kaggle.json` (Section 6.2) | Trains attrition model on real IBM HR data (optional) |

---

## 7. How to Run

1. Open `FranchiseOps_AI_Milestone2.ipynb` in Google Colab.
2. Set runtime to T4 GPU (Section 6.1) and configure all Colab Secrets (Section 6.3).
3. Run all cells top to bottom.
4. The launch cell starts Streamlit and opens an ngrok tunnel — open the printed HTTPS URL.
5. Log in with `ADMIN_EMAIL_ID` / `ADMIN_PASSWORD`.
6. Verify:
   - Home page KPI overview loads.
   - AI Copilot and Weather Demo pages respond.
   - Outlet Tiers page shows 10 outlets split into 4 tiers.
   - Admin Panel → ML Model Card tab shows metrics for all 3 agents + KMeans.
   - Lockout, OTP cooldown, and password strength badges behave as specified.

---

## 8. ML Agents

| Agent | Task | Metric | Algorithms Compared |
|---|---|---|---|
| Agent 1: Workforce Attrition | Classification | ROC-AUC | Logistic Regression, Random Forest, Gradient Boosting, SVC (RBF), + 1 more |
| Agent 2: Revenue Simulation / Outlet Tiering | Regression + Clustering | R² / KMeans | Random Forest, Gradient Boosting, Extra Trees, Ridge, + 1 more |
| Agent 3: Inventory Demand | Regression | R² | Gradient Boosting, Random Forest, Extra Trees, Ridge, + 1 more |

Each agent trains on 2 Kaggle datasets with a synthetic-data fallback, and the champion model is
saved to `joblib` with metrics logged to the `ml_models` table.

---

## 9. Security Features

- **Progressive lockout:** 3rd failed attempt → 5 min lock, 4th → 15 min lock, 5th → permanent
  (admin unlock required).
- **OTP resend cooldown:** 60s → 3 min → 5 min → 1 hour on successive resend requests.
- **Password strength:** <5 chars blocked, 5–9 chars Average, 10+ chars Good.

---

## 10. Screenshots

| Screenshot | Description |
|---|---| <img width="1247" height="616" alt="image" src="https://github.com/user-attachments/assets/e1d5d470-4417-408b-a85f-8e534b4f2d05" />

| `screenshots/home.png` | Home page KPI overview | <img width="1247" height="616" alt="image" src="https://github.com/user-attachments/assets/199c5458-8876-400c-bb31-de49b9bb1a5f" />

| `screenshots/ai_copilot.png` | AI Copilot prompt + response | <img width="1247" height="616" alt="image" src="https://github.com/user-attachments/assets/dc002ada-17a0-49f5-be0a-cc75ddda19e1" />

| `screenshots/weather_demo.png` | Weather Demo city + result |
| `screenshots/outlet_tiers.png` | Outlet Tiers page (4-tier chart) |
| `screenshots/admin_model_card.png` | Admin Panel → ML Model Card tab |
| `screenshots/admin_user_actions.png` | Admin Panel → Add / Delete / Unlock actions |
| `screenshots/lockout_otp.png` | Triggered lockout message + OTP cooldown message |

---

## 11. Notes

- All secrets are read exclusively from Colab Secrets — none are hard-coded in the notebook.
- The notebook was restarted and re-run top to bottom before upload, with all outputs cleared.
