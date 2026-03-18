"""
License client: fingerprint generation, activation, token storage and validation.
"""

import hashlib
import hmac
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import jwt
import requests

# ---------------------------------------------------------------------------
# Configuration — update SERVER_URL after deploying to Railway
# ---------------------------------------------------------------------------
SERVER_URL = os.getenv("LICENSE_SERVER", "https://doc-converter-license-production.up.railway.app")
JWT_SECRET = "c499469ef8a6150565cedfcdd6f20ca9c6f9bab09bbbcdd8c0f93e1c4715d813"

def _app_data_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", Path.home())) / "DocConverter"
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "DocConverter"
    else:
        return Path.home() / ".config" / "DocConverter"

TOKEN_FILE = _app_data_dir() / "license.json"

TIMEOUT = 8  # seconds


# ---------------------------------------------------------------------------
# Machine fingerprint
# ---------------------------------------------------------------------------

def _get_machine_id() -> str:
    """Get stable machine ID cross-platform."""
    sys_name = platform.system()
    if sys_name == "Windows":
        try:
            result = subprocess.check_output(
                ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"],
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in result.splitlines():
                if "MachineGuid" in line:
                    return line.split()[-1]
        except Exception:
            pass
    elif sys_name == "Darwin":
        try:
            result = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL,
            ).decode()
            for line in result.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        except Exception:
            pass
    else:
        for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            try:
                return Path(path).read_text().strip()
            except Exception:
                pass
    return ""


def _get_mac() -> str:
    import uuid
    return str(uuid.getnode())


def get_fingerprint() -> str:
    """
    Returns a stable machine fingerprint as a hex string.
    Cross-platform: Windows MachineGuid / macOS IOPlatformUUID / Linux machine-id.
    """
    parts = [
        _get_machine_id(),
        _get_mac(),
        platform.node(),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Token storage
# ---------------------------------------------------------------------------

def _load_token() -> str | None:
    try:
        data = json.loads(TOKEN_FILE.read_text())
        return data.get("token")
    except Exception:
        return None


def _save_token(token: str) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"token": token}))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_token_offline(token: str, fingerprint: str) -> bool:
    """Validate JWT signature and fingerprint match without network."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        expected_fp = hashlib.sha256(fingerprint.encode()).hexdigest()
        return payload.get("fp") == expected_fp and payload.get("iss") == "doc-converter"
    except jwt.InvalidTokenError:
        return False


def check_license() -> bool:
    """
    Returns True if the machine has a valid license.
    Validates offline (JWT signature + fingerprint).
    """
    token = _load_token()
    if not token:
        return False
    return _validate_token_offline(token, get_fingerprint())


# ---------------------------------------------------------------------------
# Activation
# ---------------------------------------------------------------------------

class ActivationError(Exception):
    pass


def activate(key: str) -> None:
    """
    Send activation request to server.
    On success, saves the token locally.
    Raises ActivationError with a human-readable message on failure.
    """
    fp = get_fingerprint()
    try:
        resp = requests.post(
            f"{SERVER_URL}/activate",
            json={"key": key.strip(), "fingerprint": fp},
            timeout=TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        raise ActivationError("Не удалось подключиться к серверу активации.\nПроверьте подключение к интернету.")
    except requests.exceptions.Timeout:
        raise ActivationError("Сервер не отвечает. Попробуйте позже.")

    if resp.status_code == 200:
        token = resp.json()["token"]
        _save_token(token)
        return

    detail = resp.json().get("detail", "Неизвестная ошибка")
    raise ActivationError(detail)
