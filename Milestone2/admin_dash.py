"""
admin_dash.py — Admin Dashboard for FranchiseOps AI (Milestone 2, Section 9)

Call render_admin_dashboard() from your main app AFTER confirming
st.session_state.role == 'Admin'. This module owns all Add / Delete /
Unlock user lifecycle actions plus the ML Model Card transparency tab.
"""

import streamlit as st
import pandas as pd
import db
import auth


def render_admin_dashboard():
    st.title("🛡️ Admin Dashboard")

    tab_users, tab_add, tab_models = st.tabs(
        ["👥 Users", "➕ Add User", "📊 ML Model Card"]
    )

    # ---------------- USERS TAB (list, delete, unlock) ----------------
    with tab_users:
        users = db.get_all_users()
        if not users:
            st.info("No users yet.")
        for u in users:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{u['username']}**")
                    st.caption(u["email"])
                with col2:
                    st.write(u["role"])
                with col3:
                    status = u["account_status"]
                    if status == "locked":
                        st.error("🔒 Locked")
                    elif u["failed_attempts"] and u["failed_attempts"] >= 3:
                        st.warning(f"⚠️ {u['failed_attempts']} failed attempts")
                    else:
                        st.success("✅ Active")
                with col4:
                    needs_unlock = (status == "locked") or (
                        u["failed_attempts"] and u["failed_attempts"] >= 3
                    )
                    if needs_unlock:
                        if st.button("🔓 Unlock", key=f"unlock_{u['id']}"):
                            db.unlock_user(u["id"])
                            st.success("✅ User account unlocked successfully.")
                            st.rerun()
                    if st.button("🗑️ Delete", key=f"delete_{u['id']}"):
                        db.delete_user(u["id"])
                        st.success(f"Deleted {u['username']}.")
                        st.rerun()

    # ---------------- ADD USER TAB ----------------
    with tab_add:
        st.subheader("Create a new account")
        with st.form("add_user_form", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Initial Password", type="password")
            new_role = st.selectbox(
                "Role", ["Franchise Owner", "Store Manager", "Admin"]
            )
            submitted = st.form_submit_button("Create Account")

            if submitted:
                if not all([new_username, new_email, new_password]):
                    st.error("All fields are required.")
                else:
                    badge, msg, allowed = auth.check_password_strength(new_password)
                    st.write(msg)
                    if not allowed:
                        st.stop()
                    if db.get_user_by_username(new_username):
                        st.error("Username already taken.")
                    elif db.get_user_by_email(new_email):
                        st.error("Email already registered.")
                    else:
                        db.create_user(
                            username=new_username,
                            email=new_email,
                            plain_password=new_password,
                            sec_q="Set by Admin",
                            sec_a="n/a",
                            role=new_role,
                        )
                        st.success(f"Account '{new_username}' created with role {new_role}.")
                        st.rerun()

    # ---------------- ML MODEL CARD TAB ----------------
    with tab_models:
        st.subheader("Champion Models per Agent")
        rows = db.get_ml_model_metrics()
        if not rows:
            st.info(
                "No training runs logged yet. Run train_m2_franchise.py to populate this tab."
            )
        else:
            df = pd.DataFrame(
                [dict(r) for r in rows]
            )
            df["is_champion"] = df["is_champion"].map({1: "🏆 Champion", 0: ""})
            st.dataframe(df, use_container_width=True, hide_index=True)
