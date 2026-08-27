import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# LM Studio
LM_STUDIO_URL = os.getenv(
    "LM_STUDIO_URL", os.getenv("BASE_API_URL", "http://192.168.0.98:1234")
)
LM_STUDIO_AUTH = os.getenv("LM_STUDIO_AUTH", os.getenv("USER_NUM", "user_1"))

MODEL_PRIORITY = [
    {"key": "qwen/qwen3-vl-4b", "name": "QWEN"},
    {"key": "liquid/lfm2.5-1.2b", "name": "LFM"},
    {"key": "deepseek/deepseek-r1-0528-qwen3-8b", "name": "DS"},
    {"key": "meta-llama-3-8b-instruct", "name": "LLAMA"},
]
DEFAULT_CONTEXT_LENGTH = int(os.getenv("DEFAULT_CONTEXT_LENGTH", "8192"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "10"))

# Bionic
BIONIC_ENABLED = os.getenv("BIONIC_ENABLED", "true").lower() == "true"
BIONIC_URL = os.getenv("BIONIC_URL", "http://localhost:1234/v1")
BIONIC_API_KEY = os.getenv("BIONIC_API_KEY", "")
BIONIC_MODEL = os.getenv("BIONIC_MODEL", "bionic-agent")

# для обратной совместимости
BASE_API_URL = LM_STUDIO_URL
USER_NUM = LM_STUDIO_AUTH
