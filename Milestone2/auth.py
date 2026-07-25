"""
auth.py — Security logic for FranchiseOps AI (Milestone 2)

Implements, on top of db.py:
  - Section 5   Progressive account lockout (3rd/4th/5th failed attempt)
  - Section 5.1 OTP resend rate limiting (60s / 180s / 300s / 3600s)
  - Section 6   Real-time password strength checker (Weak/Average/Good)
  - JWT session tokens (unchanged approach from Milestone 1)

This module has NO Streamlit imports — it's pure logic, so it's easy to
unit test and easy to call from any UI page (login tab, admin dash, etc).
"""

import datetime
import jwt
import db

# ---------------- JWT ----------------
def create_jwt(username, role, secret):
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=4),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------- PASSWORD STRENGTH (Section 6) ----------------
def check_password_strength(password: str):
    """
    Returns (badge, message, allowed) exactly per the Milestone 2 spec:
      < 5 chars   -> Weak,   BLOCKED
      5-9 chars   -> Average, ALLOWED
      10+ chars   -> Good,   ALLOWED
    """
    length = len(password)
    if length < 5:
        return ("Weak", "🔴 Password too weak (minimum 5 characters required).", False)
    elif length < 10:
        return ("Average", "🟡 Average strength (10+ characters recommended for enterprise security).", True)
    else:
        return ("Good", "🟢 Good password strength — proceed with bcrypt hashing.", True)


# ---------------- LOGIN + PROGRESSIVE LOCKOUT (Section 5) ----------------
class LoginResult:
    def __init__(self, success, message, user=None, token=None):
        self.success = success
        self.message = message
        self.user = user
        self.token = token


def attempt_login(identifier, plain_password, jwt_secret):
    """
    identifier: username or email
    Handles: permanent lock check, temporary lock check, failure counting,
    lockout escalation (3rd=5min, 4th=15min, 5th=permanent), and reset on success.
    """
    user = db.get_user_by_username_or_email(identifier)
    if not user:
        return LoginResult(False, "Invalid username or password.")

    now = datetime.datetime.utcnow()

    # Permanently locked — only an admin can unlock
    if user["account_status"] == "locked":
        return LoginResult(
            False,
            "❌ Account permanently locked due to 5 failed attempts. "
            "Only the System Administrator can unlock this account via the Admin Dashboard.",
        )

    # Temporarily locked — still within the lockout window
    if user["lock_until"]:
        lock_until_dt = datetime.datetime.fromisoformat(user["lock_until"])
        if now < lock_until_dt:
            remaining = int((lock_until_dt - now).total_seconds())
            mins = remaining // 60
            secs = remaining % 60
            return LoginResult(
                False,
                f"⏳ Account temporarily locked. Try again in {mins}m {secs}s.",
            )
        else:
            # Lock window has expired — clear it before evaluating this attempt
            db.reset_failed_attempts(user["id"])
            user = db.get_user_by_id(user["id"])

    # Check the password
    if db.verify_password(plain_password, user["password_hash"]):
        db.reset_failed_attempts(user["id"])
        token = create_jwt(user["username"], user["role"], jwt_secret)
        return LoginResult(True, f"Welcome, {user['username']}!", user=user, token=token)

    # Wrong password — escalate failure count
    new_count = user["failed_attempts"] + 1

    if new_count == 3:
        lock_until_dt = now + datetime.timedelta(seconds=300)
        db.record_failed_attempt(user["id"], new_count, lock_until_dt.isoformat(), "active")
        return LoginResult(False, "⏳ Account temporarily locked for 5 minutes due to 3 failed attempts.")

    elif new_count == 4:
        lock_until_dt = now + datetime.timedelta(seconds=900)
        db.record_failed_attempt(user["id"], new_count, lock_until_dt.isoformat(), "active")
        return LoginResult(False, "⏳ Account temporarily locked for 15 minutes due to 4 failed attempts.")

    elif new_count >= 5:
        db.record_failed_attempt(user["id"], new_count, None, "locked")
        return LoginResult(
            False,
            "❌ Account permanently locked due to 5 failed attempts. "
            "Only the System Administrator can unlock this account via the Admin Dashboard.",
        )

    else:
        # 1st or 2nd failure — just count it, no lock yet
        db.record_failed_attempt(user["id"], new_count, None, "active")
        remaining_before_lock = 3 - new_count
        return LoginResult(
            False,
            f"Invalid username or password. {remaining_before_lock} attempt(s) remaining before temporary lockout.",
        )


# ---------------- OTP RESEND RATE LIMITING (Section 5.1) ----------------
OTP_COOLDOWNS = {
    1: (60, "⏳ Please wait 60 seconds before requesting another OTP."),
    2: (180, "⏳ Please wait 3 minutes before requesting another OTP."),
    3: (300, "⏳ Please wait 5 minutes before requesting another OTP."),
}
OTP_COOLDOWN_DEFAULT = (3600, "⚠️ Too many OTP requests. Please wait 1 hour before trying again.")


class OtpGateResult:
    def __init__(self, allowed, message, wait_seconds=0):
        self.allowed = allowed
        self.message = message
        self.wait_seconds = wait_seconds


def can_send_otp(user_id):
    """Call this BEFORE sending an OTP. Returns whether sending is allowed right now."""
    state = db.get_otp_state(user_id)
    now = datetime.datetime.utcnow()

    if state["otp_next_allowed"]:
        next_allowed_dt = datetime.datetime.fromisoformat(state["otp_next_allowed"])
        if now < next_allowed_dt:
            wait = int((next_allowed_dt - now).total_seconds())
            # Re-derive the right message for however many resends have happened
            resend_count = state["otp_resend_count"]
            _, msg = OTP_COOLDOWNS.get(resend_count, OTP_COOLDOWN_DEFAULT)
            return OtpGateResult(False, msg, wait)

    return OtpGateResult(True, "OK")


def register_otp_send(user_id):
    """Call this AFTER an OTP is successfully sent, to set the next cooldown window."""
    state = db.get_otp_state(user_id)
    new_count = state["otp_resend_count"] + 1
    cooldown_seconds, _ = OTP_COOLDOWNS.get(new_count, OTP_COOLDOWN_DEFAULT)
    next_allowed_dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=cooldown_seconds)
    db.update_otp_state(user_id, new_count, next_allowed_dt.isoformat())


def reset_otp_cycle(user_id):
    """Call this once the OTP has been verified and the password reset is complete."""
    db.reset_otp_state(user_id)
