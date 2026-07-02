import os
import getpass
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

def is_running_in_docker() -> bool:
    return os.path.exists('/.dockerenv')

def _default_db_user() -> str:
    """Return the appropriate database user.
    Inside Docker the postgres image creates a 'postgres' superuser.
    Locally on macOS, Homebrew PostgreSQL uses the current OS username.
    """
    if is_running_in_docker():
        return "postgres"
    return getpass.getuser()

def _default_db_password() -> str:
    """Docker needs an explicit password; local macOS uses trust auth."""
    if is_running_in_docker():
        return "postgres"
    return ""

class Settings(BaseSettings):
    # --- API Keys ---
    FOOTBALL_DATA_API_KEY: str = Field(default="mock_football_data_key")
    ODDS_API_KEY: str = Field(default="")
    API_FOOTBALL_KEY: str = Field(default="")

    # --- Database ---
    DATABASE_HOST: str = Field(default_factory=lambda: "db" if is_running_in_docker() else "localhost")
    DATABASE_PORT: str = Field(default="5432")
    DATABASE_USER: str = Field(default_factory=_default_db_user)
    DATABASE_PASSWORD: str = Field(default_factory=_default_db_password)
    DATABASE_NAME: str = Field(default="prediction_db")

    # --- Runtime ---
    ENVIRONMENT: str = Field(default="development")

    @property
    def DATABASE_URL(self) -> str:
        env_url = os.environ.get("DATABASE_URL")
        if env_url:
            # Handle standard postgresql:// vs postgres:// URL scheme (Python's psycopg2 expects postgresql://)
            if env_url.startswith("postgres://"):
                env_url = env_url.replace("postgres://", "postgresql://", 1)
            return env_url
        if self.DATABASE_PASSWORD:
            return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        # macOS local trust auth — no password segment
        return f"postgresql://{self.DATABASE_USER}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
