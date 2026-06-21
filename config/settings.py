"""全局配置管理 — 使用 pydantic-settings 从 .env 加载"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM — 通用配置，支持 DeepSeek / OpenAI 等
    llm_api_key: str = ""                          # API Key
    llm_base_url: str = "https://api.deepseek.com" # API 地址
    llm_model: str = "deepseek-chat"               # 模型名
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # 向下兼容：如果只填了 anthropic_api_key，自动映射
    anthropic_api_key: str = ""  # 废弃，兼容旧 .env 文件

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/life_rehearsal.db"

    # App
    app_name: str = "生活预演家"
    app_version: str = "0.1.0"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    streamlit_port: int = 8501

    # SMTP (email verification)
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""  # 授权码，不打印到日志
    smtp_from: str = ""

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = project_root / "data"

    def model_post_init(self, __context) -> None:
        """初始化后处理：去空格 + 兼容旧的 ANTHROPIC_API_KEY 配置"""
        self.llm_api_key = self.llm_api_key.strip()
        if not self.llm_api_key and self.anthropic_api_key:
            self.llm_api_key = self.anthropic_api_key.strip()
            self.llm_base_url = "https://api.anthropic.com"

    @property
    def has_api_key(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)
