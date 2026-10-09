import os
from dotenv import load_dotenv

# Load .env di folder tempat config.py berada
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def get_env(key, default=None):
    return os.getenv(key, default)

# Logic to prioritize OPENROUTER_API_KEY over API_KEY
def get_api_key():
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY") or "hermes"

PROVIDER = get_env("PROVIDER", "9router")

CONFIG = {
    "PROVIDER": PROVIDER,
    "MODEL": get_env("MODEL", "anthropic/claude-3.5-sonnet"),
    "API_KEY": get_api_key(),
    "API_URL": "http://localhost:20128/v1/chat/completions" if PROVIDER == "9router" else "https://openrouter.ai/api/v1/chat/completions"
}
