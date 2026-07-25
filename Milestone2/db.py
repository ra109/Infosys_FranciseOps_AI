"""
db.py — SQLite data layer for FranchiseOps AI (Milestone 2)

Extends the Milestone 1 users table with:
  - failed_attempts   : consecutive failed login count
  - lock_until        : timestamp until which the account is temporarily locked
  - account_status    : 'active' or 'locked' (permanent lock after 5th failure)
  - role              : 'Admin', 'Franchise Owner', 'Store Manager', etc.
  - otp_resend_count / otp_next_allowed : OTP resend rate limiting (per-user)

Passwords are stored as bcrypt hashes, never plaintext.
"""

import sqlite3
import datetime
import bcrypt

DB_PATH = "franchiseops.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'Franchise Owner',
                    security_question TEXT,
                    security_answer TEXT,
                    failed_attempts INTEGER DEFAULT 0,
                    lock_until TIMESTAMP DEFAULT NULL,
                    account_status TEXT DEFAULT 'active',
                    otp_resend_count INTEGER DEFAULT 0,
                    otp_next_allowed TIMESTAMP DEFAULT NULL
                )''')
    # Populated later by train_m2_franchise.py — created now so admin_dash.py
    # can safely query it even before any training run has happened.
    c.execute('''CREATE TABLE IF NOT EXISTS ml_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    is_champion INTEGER DEFAULT 0,
                    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()


# ---------------- PASSWORD HASHING ----------------
def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        # malformed hash (e.g. leftover plaintext from an old row)
        return False


# ---------------- USER LOOKUP ----------------
def get_user_by_username(username):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_username_or_email(identifier):
    return get_user_by_username(identifier) or get_user_by_email(identifier)


def get_all_users():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, username, email, role, account_status, failed_attempts, lock_until FROM users"
    ).fetchall()
    conn.close()
    return rows


# ---------------- USER CREATION / ADMIN LIFECYCLE ----------------
def create_user(username, email, plain_password, sec_q, sec_a, role="Franchise Owner"):
    conn = get_conn()
    conn.execute(
        """INSERT INTO users (username, email, password_hash, role, security_question, security_answer)
           VALUES (?,?,?,?,?,?)""",
        (username, email, hash_password(plain_password), role, sec_q, sec_a),
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def unlock_user(user_id):
    conn = get_conn()
    conn.execute(
        """UPDATE users SET failed_attempts=0, lock_until=NULL, account_status='active'
           WHERE id=?""",
        (user_id,),
    )
    conn.commit()
    conn.close()


def update_password(username, new_plain_password):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET password_hash=? WHERE username=?",
        (hash_password(new_plain_password), username),
    )
    conn.commit()
    conn.close()


# ---------------- LOGIN FAILURE / LOCKOUT STATE ----------------
def record_failed_attempt(user_id, new_failed_count, lock_until_dt, account_status):
    conn = get_conn()
    conn.execute(
        """UPDATE users SET failed_attempts=?, lock_until=?, account_status=?
           WHERE id=?""",
        (new_failed_count, lock_until_dt, account_status, user_id),
    )
    conn.commit()
    conn.close()


def reset_failed_attempts(user_id):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET failed_attempts=0, lock_until=NULL WHERE id=?",
        (user_id,),
    )
    conn.commit()
    conn.close()


# ---------------- OTP RESEND RATE LIMITING ----------------
def get_otp_state(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT otp_resend_count, otp_next_allowed FROM users WHERE id=?", (user_id,)
    ).fetchone()
    conn.close()
    return row


def update_otp_state(user_id, resend_count, next_allowed_dt):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET otp_resend_count=?, otp_next_allowed=? WHERE id=?",
        (resend_count, next_allowed_dt, user_id),
    )
    conn.commit()
    conn.close()


def reset_otp_state(user_id):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET otp_resend_count=0, otp_next_allowed=NULL WHERE id=?",
        (user_id,),
    )
    conn.commit()
    conn.close()


def get_ml_model_metrics():
    conn = get_conn()
    rows = conn.execute(
        """SELECT agent_name, algorithm, metric_name, metric_value, is_champion, trained_at
           FROM ml_models ORDER BY agent_name, is_champion DESC, metric_value DESC"""
    ).fetchall()
    conn.close()
    return rows


# ---------------- ADMIN BOOTSTRAP ----------------
def seed_admin(admin_email, admin_password, admin_username="admin"):
    """Creates the default Admin account on first run only, if it doesn't exist yet."""
    if get_user_by_email(admin_email):
        return
    create_user(
        username=admin_username,
        email=admin_email,
        plain_password=admin_password,
        sec_q="System bootstrap account",
        sec_a="n/a",
        role="Admin",
    )
