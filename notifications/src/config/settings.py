"""
Notifications service configuration settings.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Notifications service configuration settings."""
    
    # Application settings
    app_name: str = "Event Contract Notifications Service"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Redis/Celery settings
    redis_url: str = Field("redis://localhost:6379/1", env="REDIS_URL")
    celery_broker_url: str = Field("redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")
    
    # Telegram Bot settings
    telegram_bot_token: Optional[SecretStr] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_ids: str = Field("", env="TELEGRAM_CHAT_IDS")
    telegram_enabled: bool = Field(False, env="TELEGRAM_ENABLED")
    
    # Feishu (Lark) settings
    feishu_app_id: Optional[str] = Field(None, env="FEISHU_APP_ID")
    feishu_app_secret: Optional[SecretStr] = Field(None, env="FEISHU_APP_SECRET")
    feishu_webhook_url: Optional[str] = Field(None, env="FEISHU_WEBHOOK_URL")
    feishu_enabled: bool = Field(False, env="FEISHU_ENABLED")
    
    # Email settings
    smtp_host: str = Field("localhost", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[SecretStr] = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    smtp_from_email: Optional[str] = Field(None, env="SMTP_FROM_EMAIL")
    email_recipients: str = Field("", env="EMAIL_RECIPIENTS")
    email_enabled: bool = Field(False, env="EMAIL_ENABLED")
    
    # Notification settings
    max_retry_attempts: int = Field(3, env="MAX_RETRY_ATTEMPTS")
    retry_delay: float = Field(5.0, env="RETRY_DELAY")  # seconds
    batch_size: int = Field(100, env="BATCH_SIZE")
    
    # Template settings
    template_dir: str = Field("templates", env="TEMPLATE_DIR")
    default_language: str = Field("en", env="DEFAULT_LANGUAGE")
    
    # Database settings (for notification history)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    # Monitoring
    metrics_enabled: bool = Field(True, env="METRICS_ENABLED")
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    @property
    def telegram_bot_token_str(self) -> Optional[str]:
        """Get Telegram bot token as string."""
        return self.telegram_bot_token.get_secret_value() if self.telegram_bot_token else None
    
    @property
    def feishu_app_secret_str(self) -> Optional[str]:
        """Get Feishu app secret as string."""
        return self.feishu_app_secret.get_secret_value() if self.feishu_app_secret else None
    
    @property
    def smtp_password_str(self) -> Optional[str]:
        """Get SMTP password as string."""
        return self.smtp_password.get_secret_value() if self.smtp_password else None
    
    def get_telegram_chat_ids_list(self) -> List[str]:
        """Parse telegram chat IDs from string to list."""
        if isinstance(self.telegram_chat_ids, str) and self.telegram_chat_ids.strip():
            if ',' in self.telegram_chat_ids:
                return [s.strip() for s in self.telegram_chat_ids.split(",") if s.strip()]
            else:
                return [self.telegram_chat_ids.strip()]
        return []
    
    def get_email_recipients_list(self) -> List[str]:
        """Parse email recipients from string to list."""
        if isinstance(self.email_recipients, str) and self.email_recipients.strip():
            if ',' in self.email_recipients:
                return [s.strip() for s in self.email_recipients.split(",") if s.strip()]
            else:
                return [self.email_recipients.strip()]
        return []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()