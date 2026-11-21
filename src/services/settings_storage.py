import json
import logging
import os
from typing import Any, Dict

from src.config import DATA_DIR, GEMINI_API_KEY

logger = logging.getLogger(__name__)
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def _load_all_settings() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading settings file: {e}")
        return {}


def _save_all_settings(settings: Dict[str, Dict[str, Any]]) -> None:
    try:
        tmp_file = f"{SETTINGS_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, SETTINGS_FILE)
    except Exception as e:
        logger.error(f"Error saving settings file: {e}")


def get_user_settings(user_id: int) -> Dict[str, Any]:
    all_settings = _load_all_settings()
    user_str = str(user_id)
    default = {
        "ai_enabled": bool(GEMINI_API_KEY),
        "language": "uk",  # "uk" or "en"
    }
    if user_str not in all_settings:
        all_settings[user_str] = default
        _save_all_settings(all_settings)
        return default
    return all_settings[user_str]


def update_user_setting(user_id: int, key: str, value: Any) -> Dict[str, Any]:
    all_settings = _load_all_settings()
    user_str = str(user_id)
    if user_str not in all_settings:
        all_settings[user_str] = {
            "ai_enabled": bool(GEMINI_API_KEY),
            "language": "uk",
        }
    all_settings[user_str][key] = value
    _save_all_settings(all_settings)
    return all_settings[user_str]


def toggle_ai(user_id: int) -> bool:
    settings = get_user_settings(user_id)
    new_val = not settings.get("ai_enabled", True)
    update_user_setting(user_id, "ai_enabled", new_val)
    return new_val


def toggle_language(user_id: int) -> str:
    settings = get_user_settings(user_id)
    current = settings.get("language", "uk")
    new_lang = "en" if current == "uk" else "uk"
    update_user_setting(user_id, "language", new_lang)
    return new_lang
