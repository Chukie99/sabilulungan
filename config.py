import os
from dotenv import load_dotenv

# Load .env in the same folder as this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_env(key, default=None, *, cast=None):
    value = os.getenv(key, default)
    if value is None:
        return default
    if cast == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    return value


def get_api_key():
    candidates = [
        get_env("OPENROUTER_API_KEY"),
        get_env("OPENROUTER_KEY"),
        get_env("API_KEY"),
        get_env("OPENAI_API_KEY"),
    ]
    for value in candidates:
        if value and value.strip() and value.strip() != "your-api-key-here" and value.strip() != "change-me":
            return value.strip()
    return "change-me"


PROVIDER = (get_env("PROVIDER", "9router") or "9router").lower()
DEFAULT_API_URL = (
    "http://localhost:20128/v1/chat/completions"
    if PROVIDER == "9router"
    else "https://openrouter.ai/api/v1/chat/completions"
)

CONFIG = {
    "PROVIDER": PROVIDER,
    "MODEL": get_env("MODEL", "anthropic/claude-3.5-sonnet"),
    "API_KEY": get_api_key(),
    "API_URL": get_env("API_URL", DEFAULT_API_URL),
}
