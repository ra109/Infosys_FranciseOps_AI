"""
app.py — FranchiseOps AI, Milestone 2 main entrypoint.

Wires together:
  db.py         - SQLite schema, bcrypt storage, lockout/OTP state
  auth.py       - login lockout logic, OTP cooldown logic, password strength
  admin_dash.py - Add / Delete / Unlock user lifecycle + ML Model Card tab

Agent 1-3 pages, the AI Copilot, and the Weather Demo are built in a later
pass (train_m2_franchise.py / llm_engine_franchise.py) - this file has
placeholder tabs for them so the app structure and screenshots line up
with Section 11 today, and those tabs light up as soon as those modules
land.
"""

import streamlit as st
import random
import smtplib
from email.mime.text import MIMEText
from google.colab import userdata  # only works inside Google Colab

import db
import auth
import admin_dash

# ---------------- SECRETS ----------------
JWT_SECRET = userdata.get("JWT_SECRET_KEY")
ADMIN_EMAIL_ID = userdata.get("ADMIN_EMAIL_ID") or "infosys@ai"
ADMIN_PASSWORD = userdata.get("ADMIN_PASSWORD") or "admin@123"

try:
    EMAIL_ID = userdata.get("EMAIL_ID")
    EMAIL_PASSWORD = userdata.get("EMAIL_PASSWORD")
except Exception:
    EMAIL_ID = None
    EMAIL_PASSWORD = None

SECURITY_QUESTIONS = [
    "What was your childhood nickname?",
    "What is the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
]

# ---------------- APP SETUP ----------------
st.set_page_config(page_title="FranchiseOps AI", page_icon="\U0001F3EA", layout="wide")
db.init_db()
db.seed_admin(ADMIN_EMAIL_ID, ADMIN_PASSWORD, admin_username="admin")

for key, default in [
    ("page", "login"),
    ("jwt_token", None),
    ("role", None),
    ("username", None),
    ("otp_value", None),
    ("otp_target_user_id", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def go_to(page):
    st.session_state.page = page


def send_otp_email(to_email, otp):
    """Sends a real email if EMAIL_ID/EMAIL_PASSWORD are set, otherwise
    falls back to printing the OTP to the console/UI (Section 3.3 note)."""
    if not EMAIL_ID or not EMAIL_PASSWORD:
        st.info(f"(Console fallback - no EMAIL_ID configured) Your OTP is: {otp}")
        return
    msg = MIMEText(f"Your OTP code is: {otp}\nIt is valid for 5 minutes.")
    msg["Subject"] = "FranchiseOps AI - Password Reset OTP"
    msg["From"] = EMAIL_ID
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ID, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ID, to_email, msg.as_string())


# ---------------- LOGIN PAGE ----------------
def login_page():
    st.title("FranchiseOps AI - Login")
    identifier = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if not identifier or not password:
            st.error("Please fill in all fields.")
        else:
            result = auth.attempt_login(identifier, password, JWT_SECRET)
            if result.success:
                st.session_state.jwt_token = result.token
                st.session_state.role = result.user["role"]
                st.session_state.username = result.user["username"]
                go_to("admin" if result.user["role"] == "Admin" else "dashboard")
                st.rerun()
            else:
                st.error(result.message)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create an account"):
            go_to("signup")
            st.rerun()
    with col2:
        if st.button("Forgot Password?"):
            go_to("forgot")
            st.rerun()


# ---------------- SIGNUP PAGE (tab2) ----------------
def signup_page():
    st.title("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if password:
        badge, msg, allowed = auth.check_password_strength(password)
        st.write(msg)

    confirm = st.text_input("Confirm Password", type="password")
    sec_q = st.selectbox("Security Question", SECURITY_QUESTIONS)
    sec_a = st.text_input("Security Answer")

    if st.button("Sign Up", type="primary"):
        if not all([username, email, password, confirm, sec_q, sec_a]):
            st.error("All fields are required.")
            return
        badge, msg, allowed = auth.check_password_strength(password)
        if not allowed:
            st.error(msg)
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return
        if db.get_user_by_username(username):
            st.error("Username already taken.")
            return
        if db.get_user_by_email(email):
            st.error("Email already registered.")
            return
        db.create_user(username, email, password, sec_q, sec_a, role="Franchise Owner")
        st.success("Account created! Please log in.")
        go_to("login")
        st.rerun()

    if st.button("Back to Login"):
        go_to("login")
        st.rerun()


# ---------------- FORGOT PASSWORD PAGE (tab3) ----------------
def forgot_page():
    st.title("Forgot Password")
    method = st.radio("Choose recovery method", ["Security Question", "Email OTP"])

    if method == "Security Question":
        username = st.text_input("Username")
        user = db.get_user_by_username(username) if username else None
        if user:
            st.info(user["security_question"])
            answer = st.text_input("Answer")
            new_pass = st.text_input("New Password", type="password")
            if new_pass:
                badge, msg, allowed = auth.check_password_strength(new_pass)
                st.write(msg)
            confirm_pass = st.text_input("Confirm New Password", type="password")
            if st.button("Reset Password"):
                _, _, allowed = auth.check_password_strength(new_pass)
                if answer.strip().lower() != (user["security_answer"] or "").strip().lower():
                    st.error("Incorrect answer.")
                elif not allowed:
                    st.error("Password too weak (minimum 5 characters required).")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    db.update_password(username, new_pass)
                    st.success("Password reset! Please log in.")
                    go_to("login")
                    st.rerun()
        elif username:
            st.error("Username not found.")

    else:  # Email OTP route, with resend cooldown (Section 5.1)
        email = st.text_input("Registered Email")
        if st.button("Send OTP"):
            user = db.get_user_by_email(email)
            if not user:
                st.error("Email not found.")
            else:
                gate = auth.can_send_otp(user["id"])
                if not gate.allowed:
                    st.warning(gate.message)
                else:
                    otp = str(random.randint(100000, 999999))
                    st.session_state.otp_value = otp
                    st.session_state.otp_target_user_id = user["id"]
                    try:
                        send_otp_email(email, otp)
                        auth.register_otp_send(user["id"])
                        st.success("OTP sent.")
                    except Exception as e:
                        st.error(f"Failed to send OTP: {e}")

        if st.session_state.otp_value:
            entered_otp = st.text_input("Enter OTP")
            new_pass = st.text_input("New Password", type="password", key="otp_new_pass")
            if new_pass:
                badge, msg, allowed = auth.check_password_strength(new_pass)
                st.write(msg)
            confirm_pass = st.text_input("Confirm New Password", type="password", key="otp_confirm_pass")
            if st.button("Verify & Reset"):
                user = db.get_user_by_email(email)
                _, _, allowed = auth.check_password_strength(new_pass)
                if entered_otp != st.session_state.otp_value:
                    st.error("Incorrect OTP.")
                elif not allowed:
                    st.error("Password too weak (minimum 5 characters required).")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    db.update_password(user["username"], new_pass)
                    auth.reset_otp_cycle(user["id"])
                    st.session_state.otp_value = None
                    st.session_state.otp_target_user_id = None
                    st.success("Password reset! Please log in.")
                    go_to("login")
                    st.rerun()

    if st.button("Back to Login"):
        go_to("login")
        st.rerun()


# ---------------- USER DASHBOARD (Home + placeholder agent tabs) ----------------
def dashboard_page():
    payload = auth.decode_jwt(st.session_state.jwt_token, JWT_SECRET) if st.session_state.jwt_token else None
    if not payload:
        st.warning("Session expired. Please log in again.")
        go_to("login")
        st.rerun()
        return

    st.sidebar.write(f"{payload['username']} ({payload['role']})")
    if st.sidebar.button("Logout"):
        st.session_state.jwt_token = None
        go_to("login")
        st.rerun()

    tab_home, tab_attrition, tab_outlets, tab_inventory, tab_copilot, tab_weather = st.tabs(
        ["Home", "Workforce Attrition", "Outlet Tiers", "Inventory", "AI Copilot", "Weather Demo"]
    )

    with tab_home:
        st.title("Home")
        st.write(f"Welcome, **{payload['username']}**!")
        st.info("KPI overview will populate once train_m2_franchise.py has run.")

    for tab, label in [
        (tab_attrition, "Agent 1: Workforce Attrition"),
        (tab_outlets, "Agent 2: Outlet Tiering / Revenue"),
        (tab_inventory, "Agent 3: Inventory & Weather Demand"),
        (tab_copilot, "AI Copilot"),
        (tab_weather, "Weather Demo"),
    ]:
        with tab:
            st.info(f"{label} - coming online with train_m2_franchise.py / llm_engine_franchise.py.")


# ---------------- ADMIN ROUTER GUARD ----------------
def admin_page():
    payload = auth.decode_jwt(st.session_state.jwt_token, JWT_SECRET) if st.session_state.jwt_token else None
    if not payload or payload["role"] != "Admin":
        st.warning("Admin access only.")
        go_to("login")
        st.rerun()
        return
    st.sidebar.write(f"{payload['username']} (Admin)")
    if st.sidebar.button("Logout"):
        st.session_state.jwt_token = None
        go_to("login")
        st.rerun()
    admin_dash.render_admin_dashboard()


# ---------------- ROUTER ----------------
page = st.session_state.page
if page == "login":
    login_page()
elif page == "signup":
    signup_page()
elif page == "forgot":
    forgot_page()
elif page == "dashboard":
    dashboard_page()
elif page == "admin":
    admin_page()
