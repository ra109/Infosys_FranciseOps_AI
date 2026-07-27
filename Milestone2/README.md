# FranchiseOps AI — Milestone 2
### Full-Stack AI/ML Integration & Advanced Security Engine

Milestone 2 builds on top of the Milestone 1 Authentication module by unifying it with a multi-agent
ML core and a Generative AI Copilot, and adding three hardening layers on top of security:
progressive account lockout, real-time password strength checking, and a fully functional Admin Dashboard.

---

## 1. What Milestone 2 Adds Over Milestone 1

Milestone 1 delivered the User Authentication module — JWT sessions, Streamlit UI, SQLite-backed
credentials, and Gmail OTP verification.

Milestone 2 adds:
- **Progressive account lockout** — 3 failed logins locks the account for 5 minutes, 4 for 15 minutes,
  and a 5th failure locks it permanently until an Admin unlocks it.
- **OTP resend rate limiting** — cooldowns of 60s / 180s / 300s / 1 hour on repeated OTP requests,
  to stop OTP-spam abuse.
- **Real-time password strength checker** — a live 🔴/🟡/🟢 badge shown while typing, on both signup
  and password reset.
- **Three autonomous ML agents** — Workforce Attrition prediction, Outlet Clustering & Revenue
  Simulation, and Inventory & Weather Demand forecasting, each comparing 5+ algorithms before
  picking a champion model.
- **An LLM Copilot** (Qwen2.5-3B-Instruct, 4-bit quantized) that reads the 3 agents' numeric outputs
  and turns them into a plain-language retention plan plus a structured JSON ERP action.
- **A fully functional Admin Dashboard** — Add User, Delete User, Unlock Account, and an ML Model
  Card tab showing every agent's training metrics.

## 2. Features Built

| Feature | Description |
|---|---|
| Login / Signup / Forgot Password | Carried over from Milestone 1, now backed by bcrypt password hashing |
| Progressive Lockout | 5-min → 15-min → permanent lock, tracked in SQLite |
| OTP Cooldown | Escalating resend wait times to prevent spam |
| Password Strength Badge | Weak / Average / Good, real-time as the user types |
| Agent 1: Workforce Attrition | Classification model, ROC-AUC optimized, 5+ algorithms compared |
| Agent 2: Outlet Clustering & Revenue | Regression + KMeans tiering (Excellent/Good/Needs Attention/Critical) |
| Agent 3: Inventory & Weather Demand | Regression model, R² optimized, 5+ algorithms compared |
| AI Copilot | Qwen2.5-3B (4-bit) synthesizes agent outputs into an action plan + JSON |
| Weather Demo | Live weather lookup for 6 seeded Indian retail cities |
| Admin Dashboard | Add/Delete/Unlock users, view ML Model Card metrics |

## 3. Tech Stack

- **Frontend:** Streamlit
- **Auth & Sessions:** PyJWT, bcrypt, SQLite
- **Tunneling:** ngrok (public HTTPS URL from Colab)
- **Email:** Gmail SMTP (OTP delivery)
- **ML:** scikit-learn (Logistic/Random Forest/Gradient Boosting/SVC/Decision Tree/AdaBoost/KNN, etc.), KMeans, joblib
- **Data:** Kaggle datasets via `kagglehub`, pandas
- **LLM Copilot:** HuggingFace Transformers, Qwen2.5-3B-Instruct, bitsandbytes (4-bit quantization)
- **Runtime:** Google Colab, T4 GPU

## 4. System Architecture — 4 Phases

FranchiseOps AI is built as four layered phases, each gating access to the next.

| Phase | Module / Component | Responsibility & Workflow |
|-------|--------------------|-----------------------------|
| **Phase 1: Security Gateway** | Authentication & JWT (`auth.py`, `db.py`) | Enforces Login, Registration, and Forgot Password (Gmail OTP) before unlocking the UI. Stores hashed credentials and progressive lockout state in the SQLite `users` table. |
| **Phase 2: Domain Intelligence** | 3 Autonomous Agents (`train_m2_franchise.py`) | Once authenticated, unlocks Agent 1: Workforce Attrition, Agent 2: Outlets Clustering / Revenue, and Agent 3: Inventory & Weather Demand tabs. Each agent trains on 2 Kaggle datasets and compares 5+ algorithms before saving a champion model. |
| **Phase 3: Generative Advisory** | LLM Copilot & JSON (`llm_engine_franchise.py`) | Synthesizes the 3 agents' numerical outputs into executive HR retention plans and structured JSON ERP actions, powered by Qwen2.5-3B-Instruct (4-bit quantized). |
| **Phase 4: System Administration** | Admin Dashboard (`admin_dash.py`) | Dedicated administrative controls, restricted exclusively to `role = 'Admin'` accounts. |

Data flows one direction through the stack: a user clears Phase 1 (auth) before touching Phase 2
(the agents); Phase 2's numeric outputs feed Phase 3, where the LLM turns them into a readable
action plan; Phase 4 sits alongside the whole stack as an administrative overlay.

## 5. Localized Indian Retail Cities

The Weather Demo and outlet seeding are localized to 6 Indian metro markets:

| City | Region |
|---|---|
| Mumbai | Maharashtra |
| Delhi NCR | National Capital Region |
| Bengaluru | Karnataka |
| Hyderabad | Telangana |
| Chennai | Tamil Nadu |
| Pune | Maharashtra |

## 6. Colab Setup — Secrets & Kaggle API

### 6.1 Switch the runtime to GPU
- `Runtime → Change runtime type → T4 GPU → Save`
- Run `!nvidia-smi` as your first cell to confirm the GPU attached.

### 6.2 Create a Kaggle API Token (recommended, optional)
1. Log in at kaggle.com → profile picture → Settings → API → **Create New Token**.
2. This downloads `kaggle.json` (username + key).
3. Either add `KAGGLE_USERNAME` / `KAGGLE_KEY` as Colab Secrets, or upload the file to `~/.kaggle/kaggle.json`.
4. The notebook works without this too — it falls back to synthetic data.

### 6.3 Store all secrets in Colab (never hard-code them)
Click the key icon (Secrets) in the left sidebar, add each of these, and toggle notebook access ON:

| Secret Name | Used For |
|---|---|
| `JWT_SECRET_KEY` | Signs & verifies login session tokens |
| `ADMIN_EMAIL_ID` | Bootstraps the Admin account on first run |
| `ADMIN_PASSWORD` | Bootstraps the Admin account on first run |
| `NGROK_AUTHTOKEN` | Gives the Streamlit app a public HTTPS URL |
| `HF_TOKEN` | Authenticates HuggingFace inference for the LLM Copilot |
| `EMAIL_ID` | Sender address for OTP emails (optional — console fallback works without it) |
| `EMAIL_PASSWORD` | Gmail App Password, authenticates SMTP sending |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | Trains Agent 1 on real IBM HR data instead of synthetic |

## 7. How to Run the Notebook

1. Open `FranchiseOps_AI_Milestone2.ipynb` in Google Colab.
2. Confirm all secrets above are set (Section 6.3).
3. `Runtime → Change runtime type → T4 GPU`.
4. Run all cells top to bottom: installs → data/model setup → launch cell.
5. The launch cell starts Streamlit and opens an ngrok tunnel — open the printed public URL.
6. Log in with `ADMIN_EMAIL_ID` / `ADMIN_PASSWORD` to reach the Admin Dashboard, or sign up as a
   regular user to reach the agent tabs.

## 8. Screenshots

- Login / Signup (with password strength badge) <img width="727" height="641" alt="Screenshot 2026-07-27 232344" src="https://github.com/user-attachments/assets/53a8a905-9f7c-4bbf-a80d-5d7f65161696" />

- Forgot Password (Security Question + OTP routes)  <img width="642" height="252" alt="image" src="https://github.com/user-attachments/assets/93897c61-e274-4a43-ab59-3f76977d2fec" />

- Home page (KPI overview)
- AI Copilot (prompt + response) <img width="1782" height="550" alt="Screenshot 2026-07-27 233838" src="https://github.com/user-attachments/assets/50ded694-56c3-4810-a18d-cfb60acf28f0" />

- Weather Demo (city + result)
- Outlet Tiers page (4-tier chart)
- Admin Panel → ML Model Card tab <img width="1917" height="916" alt="Screenshot 2026-07-27 233612" src="https://github.com/user-attachments/assets/1a49013a-307f-4c20-a2eb-2dcc00453b32" />

<img width="1917" height="908" alt="Screenshot 2026-07-27 233554" src="https://github.com/user-attachments/assets/07ccf308-20a9-4953-a730-11e9fad8531b" />

- A triggered lockout message <img width="1917" height="905" alt="Screenshot 2026-07-27 233535" src="https://github.com/user-attachments/assets/569df567-034f-4f37-8c04-500160b9c8d6" />

<img width="1908" height="912" alt="Screenshot 2026-07-27 233511" src="https://github.com/user-attachments/assets/67c7f1cb-37d1-4eb7-b28f-e7628c4608f1" />
<img width="1917" height="907" alt="Screenshot 2026-07-27 233451" src="https://github.com/user-attachments/assets/e75a6982-0f0e-4bfe-8d49-fa59b2f48a9a" />
<img width="395" height="546" alt="Screenshot 2026-07-27 233418" src="https://github.com/user-attachments/assets/6afd8666-155e-4074-a1eb-e2b3b7d51cd2" />

<img width="315" height="325" alt="Screenshot 2026-07-27 233246" src="https://github.com/user-attachments/assets/c1cce1b2-30b8-42f6-bbf9-6cbdb4bb6ca4" />
<img width="1905" height="913" alt="Screenshot 2026-07-27 232911" src="https://github.com/user-attachments/assets/eac3308c-ea0c-43c5-a83a-89056828cbfe" />


