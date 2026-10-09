import os
from dotenv import load_dotenv

# Load .env di folder tempat config.py berada
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def get_env(key, default=None):
    return os.getenv(key, default)

CONFIG = {
    "PROVIDER": get_env("PROVIDER", "9router"),
    "MODEL": get_env("MODEL", "anthropic/claude-3.5-sonnet"),
    "API_KEY": get_env("API_KEY", "hermes"),
    "OPENROUTER_API_KEY": get_env("OPENROUTER_API_KEY", ""),
    "API_URL": "http://localhost:20128/v1/chat/completions" if get_env("PROVIDER", "9router") == "9router" else "https://openrouter.ai/api/v1/chat/completions"
}
