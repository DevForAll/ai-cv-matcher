import logging
import os

from dotenv import load_dotenv

load_dotenv()


def _int_env(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _bool_env(key: str, default: bool) -> bool:
    val = os.getenv(key, "true" if default else "false").lower()
    return val in ("1", "true", "yes", "on")


class LoggingConfig:
    """
    Logging configuration resolved from environment variables.

    Variables:
        LOG_LEVEL           DEBUG | INFO | WARNING | ERROR | CRITICAL  (default: INFO)
        LOG_FORMAT          text | json                                 (default: text)
        LOG_FILE_ENABLED    true | false                               (default: false)
        LOG_FILE_PATH       Path to rotating log file                  (default: logs/app.log)
        LOG_FILE_MAX_MB     Max size per file in MB                    (default: 10)
        LOG_FILE_BACKUP_COUNT  Number of rotated files to keep         (default: 5)
        APP_NAME            Application identifier                     (default: ai-cv-matcher)
        APP_ENV             development | staging | production          (default: development)
    """

    def __init__(self) -> None:
        raw_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.level: int = getattr(logging, raw_level, logging.INFO)
        self.format: str = os.getenv("LOG_FORMAT", "text")
        self.file_enabled: bool = _bool_env("LOG_FILE_ENABLED", False)
        self.file_path: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
        self.file_max_bytes: int = _int_env("LOG_FILE_MAX_MB", 10) * 1024 * 1024
        self.file_backup_count: int = _int_env("LOG_FILE_BACKUP_COUNT", 5)
        self.app_name: str = os.getenv("APP_NAME", "ai-cv-matcher")
        self.app_env: str = os.getenv("APP_ENV", "development")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        return cls()
