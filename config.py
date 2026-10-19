import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

def reload_config():
    """환경 변수 다시 로드"""
    global GEMINI_API_KEY, OPENAI_API_KEY, AI_PROVIDER, GEMINI_MODEL, OPENAI_MODEL
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)
    else:
        load_dotenv(override=True)

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o").strip()

reload_config()

def save_to_env(gemini_key: str = None, openai_key: str = None, provider: str = None, gemini_model: str = None):
    """설정 값을 .env 파일에 저장하고 런타임에 즉시 반영"""
    new_dict = {
        "AI_PROVIDER": provider if provider is not None else AI_PROVIDER,
        "GEMINI_API_KEY": gemini_key if gemini_key is not None else GEMINI_API_KEY,
        "GEMINI_MODEL": gemini_model if gemini_model is not None else GEMINI_MODEL,
        "OPENAI_API_KEY": openai_key if openai_key is not None else OPENAI_API_KEY,
        "OPENAI_MODEL": OPENAI_MODEL,
    }

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("# Idea-Tracer AI 설정 파일 (.env)\n")
        for k, v in new_dict.items():
            f.write(f"{k}={v}\n")

    reload_config()

def has_valid_api_key() -> bool:
    """사용 가능한 유효한 API 키가 존재하는지 확인"""
    if AI_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return bool(GEMINI_API_KEY)

def get_active_provider_name() -> str:
    """현재 활성화된 분석 엔진 이름 반환"""
    if AI_PROVIDER == "openai" and OPENAI_API_KEY:
        return f"OpenAI ({OPENAI_MODEL})"
    elif GEMINI_API_KEY:
        return f"Google Gemini ({GEMINI_MODEL})"
    return "스마트 로컬 분석 엔진 (오프라인/시뮬레이션 모드)"
