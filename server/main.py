"""
License server for Doc Converter.
Deploy on Railway/Render (free tier).
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import hashlib
import hmac
import os
import jwt
import datetime
from pathlib import Path

app = FastAPI(title="Doc Converter License Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DB_PATH = Path(os.getenv("DB_PATH", "licenses.db"))
JWT_SECRET = os.environ["JWT_SECRET"]          # set in Railway env vars
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]        # for key generation endpoint


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key         TEXT PRIMARY KEY,
            activated   INTEGER DEFAULT 0,
            fingerprint TEXT,
            activated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ActivateRequest(BaseModel):
    key: str
    fingerprint: str


class VerifyRequest(BaseModel):
    token: str
    fingerprint: str


class AddKeyRequest(BaseModel):
    key: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fp_hash(fingerprint: str) -> str:
    return hashlib.sha256(fingerprint.encode()).hexdigest()


def _make_token(key: str, fingerprint: str) -> str:
    payload = {
        "key": key,
        "fp": _fp_hash(fingerprint),
        "iat": datetime.datetime.utcnow(),
        "iss": "doc-converter",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/activate")
def activate(req: ActivateRequest):
    """
    Bind a license key to a machine fingerprint and return a JWT token.
    Called once on first launch.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM licenses WHERE key = ?", (req.key,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Ключ не найден")

    if row["activated"]:
        # Already activated — allow re-activation on same machine
        if row["fingerprint"] != _fp_hash(req.fingerprint):
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="Ключ уже активирован на другой машине"
            )
        # Same machine — just re-issue token
        token = _make_token(req.key, req.fingerprint)
        conn.close()
        return {"token": token}

    # First activation
    conn.execute(
        "UPDATE licenses SET activated=1, fingerprint=?, activated_at=? WHERE key=?",
        (_fp_hash(req.fingerprint), datetime.datetime.utcnow().isoformat(), req.key),
    )
    conn.commit()
    conn.close()

    token = _make_token(req.key, req.fingerprint)
    return {"token": token}


@app.post("/verify")
def verify(req: VerifyRequest):
    """
    Optional online token check. Client can call this periodically.
    """
    try:
        payload = jwt.decode(req.token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

    if payload.get("fp") != _fp_hash(req.fingerprint):
        raise HTTPException(status_code=403, detail="Токен привязан к другой машине")

    return {"valid": True}


@app.post("/admin/add-key")
def add_key(req: AddKeyRequest, x_admin_token: str = Header(...)):
    """
    Add a new license key to the database. Protected by admin token.
    """
    if not hmac.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=403, detail="Forbidden")

    conn = get_db()
    try:
        conn.execute("INSERT INTO licenses (key) VALUES (?)", (req.key,))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Ключ уже существует")
    conn.close()
    return {"added": req.key}


@app.get("/health")
def health():
    return {"status": "ok"}
