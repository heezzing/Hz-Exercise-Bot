from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    database_url: str
    app_env: str = "development"
    secret_key: str = "change-me"

    # OpenRouter 모델 (Hermes 계열만 허용)
    hermes_heavy: str = "nousresearch/hermes-3-llama-3.1-70b"
    hermes_light: str = "nousresearch/hermes-3-llama-3.1-8b"
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"

    # 시설 검색 기본 반경 (미터)
    facility_search_radius_m: int = 5000

    model_config = {"env_file": ".env", "protected_namespaces": ()}


settings = Settings()
