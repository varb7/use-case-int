"""Windows credential storage and session-only settings for hosted Streamlit."""
from __future__ import annotations

import os
import sys

SERVICE = "QuestionnaireReviewApp"
API_KEY_ACCOUNT = "google_api_key"
MODEL_ACCOUNT = "gemini_generation_model"


def uses_windows_credentials() -> bool:
    return sys.platform == "win32"


def _session_settings():
    import streamlit as st
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    if get_script_run_ctx(suppress_warning=True) is None:
        raise RuntimeError("Open the Streamlit app to save session settings, or configure environment variables.")
    return st.session_state.setdefault("_google_settings", {})


def _keyring():
    import keyring
    return keyring


def _read(account: str) -> str | None:
    if not uses_windows_credentials():
        try:
            return _session_settings().get(account)
        except RuntimeError:
            return None
    try:
        value = _keyring().get_password(SERVICE, account)
    except Exception as exc:
        raise RuntimeError("Windows Credential Manager is unavailable") from exc
    return value.strip() if value and value.strip() else None


def _write(account: str, value: str) -> None:
    if not value.strip():
        raise ValueError("The saved value cannot be empty")
    if not uses_windows_credentials():
        _session_settings()[account] = value.strip()
        return
    try:
        _keyring().set_password(SERVICE, account, value.strip())
    except Exception as exc:
        raise RuntimeError("Could not save settings in Windows Credential Manager") from exc


def _delete(account: str) -> None:
    if not uses_windows_credentials():
        _session_settings().pop(account, None)
        return
    keyring = _keyring()
    try:
        keyring.delete_password(SERVICE, account)
    except keyring.errors.PasswordDeleteError:
        pass
    except Exception as exc:
        raise RuntimeError("Could not remove settings from Windows Credential Manager") from exc


def saved_api_key() -> str | None:
    return _read(API_KEY_ACCOUNT)


def saved_model() -> str | None:
    return _read(MODEL_ACCOUNT)


def resolve_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or saved_api_key()


def resolve_model() -> str | None:
    return os.getenv("GEMINI_MODEL") or saved_model()


def save_settings(api_key: str | None = None, model: str | None = None) -> None:
    if api_key and api_key.strip():
        _write(API_KEY_ACCOUNT, api_key)
    if model and model.strip():
        _write(MODEL_ACCOUNT, model)


def remove_settings() -> None:
    _delete(API_KEY_ACCOUNT)
    _delete(MODEL_ACCOUNT)


def settings_status() -> tuple[bool, bool, str]:
    try:
        key = resolve_api_key()
        model = resolve_model()
    except RuntimeError as exc:
        return False, False, str(exc)
    source = "environment" if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") else (
        "Windows Credential Manager" if uses_windows_credentials() else "this session")
    return bool(key), bool(model), source


def test_connection() -> str:
    key, model = resolve_api_key(), resolve_model()
    if not key or not model:
        raise RuntimeError("Save both a Google API key and generation model first")
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        timeout=30_000, retry_options=types.HttpRetryOptions(attempts=1)))
    found = client.models.get(model=model)
    return getattr(found, "name", None) or model
