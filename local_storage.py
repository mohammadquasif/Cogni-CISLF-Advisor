"""
local_storage.py — Encrypted Local Credential Manager
======================================================
Stores API keys and user preferences in an AES-256 encrypted SQLite
database on the user's machine. Credentials NEVER leave the device.

Storage location: ~/.cogni_cislf/cogni_data.db

Security model:
  - Encryption uses Fernet (AES-256-CBC + HMAC-SHA256)
  - Encryption key = SHA-256( MAC_address_bytes + APP_SALT )
  - Key is derived at runtime — never stored on disk
  - Credentials are machine-specific and non-portable

CISLF Framework — Developed by Mohammad Quasif, DBA Candidate
Kennedy University of Baptist, France
"""

import base64
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Local storage directory and database file
APP_DIR = Path.home() / ".cogni_cislf"
DB_PATH = APP_DIR / "cogni_data.db"

# App-specific salt prevents cross-application key reuse
APP_SALT = b"CogniCISLF_Quasif_DBA_2025_SecureKey"


# ---------------------------------------------------------------------------
# Key Derivation (Machine-Specific)
# ---------------------------------------------------------------------------

def _derive_encryption_key() -> bytes:
    """
    Derive a Fernet-compatible 32-byte key from the machine's hardware identity.

    Uses the MAC address (uuid.getnode()) combined with an app-specific salt,
    hashed with SHA-256. The result is base64url-encoded to form a valid
    Fernet key. This makes credentials machine-specific: they cannot be
    decrypted on a different device.

    Returns:
        32-byte base64url-encoded key suitable for Fernet.
    """
    # MAC address as bytes (unique per network interface card)
    machine_id_bytes = str(uuid.getnode()).encode("utf-8")
    # Combine with app salt and hash
    raw_key = hashlib.sha256(machine_id_bytes + APP_SALT).digest()
    # Fernet requires URL-safe base64-encoded 32-byte key
    return base64.urlsafe_b64encode(raw_key)


def _get_cipher() -> Fernet:
    """Return a Fernet cipher instance using the machine-derived key."""
    return Fernet(_derive_encryption_key())


# ---------------------------------------------------------------------------
# Database Initialisation
# ---------------------------------------------------------------------------

def _ensure_db() -> None:
    """
    Create the application directory and SQLite database tables if they
    do not already exist. Safe to call multiple times (idempotent).
    """
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # ── Credentials table (encrypted API keys, secrets) ──────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                key_name       TEXT PRIMARY KEY,
                encrypted_value BLOB NOT NULL,
                created_at     TEXT DEFAULT (datetime('now')),
                updated_at     TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── Preferences table (non-sensitive settings) ───────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                pref_key   TEXT PRIMARY KEY,
                pref_value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Credential Operations
# ---------------------------------------------------------------------------

def save_credential(key_name: str, value: str) -> bool:
    """
    Encrypt and persist a credential to the local database.

    Args:
        key_name: Unique identifier (e.g., "gemini_api_key", "openai_api_key").
        value:    Plaintext secret to encrypt and store.

    Returns:
        True on success, False on failure.
    """
    if not key_name or not value:
        return False
    try:
        _ensure_db()
        cipher = _get_cipher()
        encrypted = cipher.encrypt(value.encode("utf-8"))
        now = datetime.utcnow().isoformat()

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("""
                INSERT INTO credentials (key_name, encrypted_value, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key_name) DO UPDATE SET
                    encrypted_value = excluded.encrypted_value,
                    updated_at      = excluded.updated_at
            """, (key_name, encrypted, now, now))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False


def load_credential(key_name: str) -> Optional[str]:
    """
    Decrypt and return a stored credential.

    Args:
        key_name: Identifier used when the credential was saved.

    Returns:
        Decrypted plaintext string, or None if not found or decryption fails.
    """
    try:
        _ensure_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT encrypted_value FROM credentials WHERE key_name = ?",
                (key_name,)
            ).fetchone()
        finally:
            conn.close()

        if not row:
            return None

        cipher = _get_cipher()
        return cipher.decrypt(row[0]).decode("utf-8")

    except (InvalidToken, Exception):
        # InvalidToken = wrong machine / corrupted data
        return None


def delete_credential(key_name: str) -> bool:
    """
    Permanently remove a stored credential.

    Args:
        key_name: Identifier of the credential to remove.

    Returns:
        True on success, False on failure.
    """
    try:
        _ensure_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "DELETE FROM credentials WHERE key_name = ?", (key_name,)
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def list_stored_credentials() -> List[Tuple[str, str]]:
    """
    List all stored credential identifiers (NOT their values).

    Returns:
        List of (key_name, updated_at) tuples, most recent first.
    """
    try:
        _ensure_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute(
                "SELECT key_name, updated_at FROM credentials ORDER BY updated_at DESC"
            ).fetchall()
        finally:
            conn.close()
        return rows  # [(key_name, updated_at), ...]
    except Exception:
        return []


def credential_exists(key_name: str) -> bool:
    """Return True if a credential with the given key_name is stored."""
    try:
        _ensure_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT 1 FROM credentials WHERE key_name = ?", (key_name,)
            ).fetchone()
        finally:
            conn.close()
        return row is not None
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Preference Operations (non-encrypted, non-sensitive)
# ---------------------------------------------------------------------------

def save_preference(key: str, value: str) -> bool:
    """
    Store a non-sensitive user preference (e.g., last used provider, model).

    Args:
        key:   Preference key string.
        value: Preference value string.

    Returns:
        True on success.
    """
    try:
        _ensure_db()
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("""
                INSERT INTO preferences (pref_key, pref_value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(pref_key) DO UPDATE SET
                    pref_value = excluded.pref_value,
                    updated_at = excluded.updated_at
            """, (key, value, now))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def load_preference(key: str, default: str = "") -> str:
    """
    Load a stored preference.

    Args:
        key:     Preference key.
        default: Default value if key not found.

    Returns:
        Stored value string, or default.
    """
    try:
        _ensure_db()
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT pref_value FROM preferences WHERE pref_key = ?", (key,)
            ).fetchone()
        finally:
            conn.close()
        return row[0] if row else default
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_db_info() -> Dict[str, Any]:
    """
    Return metadata about the local database for display in the UI.

    Returns:
        Dict with 'path', 'exists', 'size_kb', 'credential_count'.
    """
    info: Dict[str, Any] = {
        "path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "size_kb": 0.0,
        "credential_count": 0,
    }
    if DB_PATH.exists():
        info["size_kb"] = round(DB_PATH.stat().st_size / 1024, 2)
        try:
            conn = sqlite3.connect(DB_PATH)
            try:
                row = conn.execute("SELECT COUNT(*) FROM credentials").fetchone()
                info["credential_count"] = row[0] if row else 0
            finally:
                conn.close()
        except Exception:
            pass
    return info
