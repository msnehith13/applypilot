from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    tinyfish_api_key: str = ""
    anthropic_api_key: str = ""   # put your GROQ_API_KEY value here

    # Portal Credentials
    internshala_email: str = ""
    internshala_password: str = ""
    linkedin_email: str = ""
    linkedin_password: str = ""
    naukri_email: str = ""
    naukri_password: str = ""

    # App Config
    database_url: str = "sqlite:///./applypilot.db"
    max_applications_per_run: int = 30
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Always read fresh from .env — no cache so key updates take effect immediately."""
    return Settings()