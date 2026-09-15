"""Password accounts and expiring opaque sessions. No default credentials."""
import argparse
import getpass
import hashlib
import hmac
import secrets
import time

from src.storage import store

ROLES = ("Loan Officer", "Risk Manager", "Committee Chair")
SESSION_SECONDS = 8 * 60 * 60


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"{salt}:{digest}"


def create_user(username, password, role, replace=False):
    if (role not in ROLES or not username.strip() or username != username.strip()
            or len(username) > 80 or not 12 <= len(password) <= 256):
        raise ValueError("Tên không trống, không có khoảng trắng ở hai đầu, tối đa 80 ký tự; mật khẩu 12–256 ký tự; vai trò phải hợp lệ.")
    with store.transaction() as db:
        if replace:
            db.execute("INSERT INTO users VALUES (?, ?, ?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash, role=excluded.role",
                       (username, password_hash(password), role))
            db.execute("DELETE FROM sessions WHERE username=?", (username,))
        else:
            db.execute("INSERT INTO users VALUES (?, ?, ?)", (username, password_hash(password), role))


def login(username, password, source):
    now = time.time()
    # Global per-source rate limit also covers attempts against nonexistent usernames.
    with store.transaction() as db:
        db.execute("DELETE FROM login_attempts WHERE since < ?", (now - 900,))
        row = db.execute("SELECT count FROM login_attempts WHERE source=?", (source,)).fetchone()
        if row and row[0] >= 10:
            return None, "limited"
        db.execute("INSERT INTO login_attempts VALUES (?,1,?) ON CONFLICT(source) DO UPDATE SET count=count+1", (source, now))
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    # Perform the expensive KDF outside the write transaction.
    stored = user["password_hash"] if user else "0" * 32 + ":" + "0" * 64
    valid = hmac.compare_digest(password_hash(password, stored.split(":")[0]), stored)
    if not user or not valid:
        return None, "invalid"
    token = secrets.token_urlsafe(32)
    with store.transaction() as db:
        # Re-read to reject a concurrent password/role change.
        current = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not current or current["password_hash"] != stored:
            return None, "invalid"
        db.execute("DELETE FROM sessions WHERE expires < ?", (now,))
        db.execute("DELETE FROM login_attempts WHERE source=?", (source,))
        db.execute("INSERT INTO sessions VALUES (?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), username, now + SESSION_SECONDS))
        db.execute("DELETE FROM sessions WHERE token_hash IN (SELECT token_hash FROM sessions WHERE username=? ORDER BY expires DESC LIMIT -1 OFFSET 10)", (username,))
    return token, None


def session_user(token):
    if not token:
        return None
    with store.transaction() as db:
        row = db.execute("""SELECT u.username, u.role FROM sessions s JOIN users u ON u.username=s.username
                            WHERE s.token_hash=? AND s.expires>?""",
                         (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
    return dict(row) if row else None


def logout(token):
    with store.transaction() as db:
        db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256((token or "").encode()).hexdigest(),))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo tài khoản nội bộ; mật khẩu không hiện trên màn hình.")
    parser.add_argument("username")
    parser.add_argument("--role", required=True, choices=ROLES)
    parser.add_argument("--replace", action="store_true", help="Đặt lại mật khẩu/quyền và thu hồi toàn bộ phiên cũ của tài khoản")
    args = parser.parse_args()
    password = getpass.getpass("Mật khẩu (ít nhất 12 ký tự): ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        raise SystemExit("Mật khẩu không khớp.")
    create_user(args.username, password, args.role, replace=args.replace)
    print("Đã tạo tài khoản.")
