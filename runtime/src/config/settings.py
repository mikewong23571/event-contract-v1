"""
Runtime engine configuration settings.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime engine configuration settings."""
    
    # Application settings
    app_name: str = "Event Contract Runtime Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Binance API settings
    binance_api_key: Optional[str] = Field(None, env="BINANCE_API_KEY")
    binance_secret_key: Optional[str] = Field(None, env="BINANCE_SECRET_KEY")
    binance_testnet: bool = Field(True, env="BINANCE_TESTNET")
    
    # WebSocket settings
    websocket_host: str = Field("localhost", env="WEBSOCKET_HOST")
    websocket_port: int = Field(8001, env="WEBSOCKET_PORT")
    websocket_path: str = Field("/ws/runtime", env="WEBSOCKET_PATH")
    
    # Trading symbols to monitor
    trading_symbols: List[str] = Field(["BTCUSDT", "ETHUSDT"], env="TRADING_SYMBOLS")
    
    # Signal detection settings
    signal_interval: float = Field(1.0, env="SIGNAL_INTERVAL")  # seconds
    min_confidence: float = Field(0.6, env="MIN_CONFIDENCE")
    
    # Database settings
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    influxdb_url: str = Field("http://localhost:8086", env="INFLUXDB_URL")
    influxdb_token: Optional[str] = Field(None, env="INFLUXDB_TOKEN")
    influxdb_org: str = Field("trading", env="INFLUXDB_ORG")
    influxdb_bucket: str = Field("market_data", env="INFLUXDB_BUCKET")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    @validator("trading_symbols", pre=True)
    def parse_trading_symbols(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",")]
        return v
    
    @validator("min_confidence")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()