from typing import Optional
import secrets
import warnings
from typing import Annotated, Any, Literal
from pathlib import Path

import yaml
from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from typing_extensions import Self
from loguru import logger


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class AppConfig(BaseModel):
    project_name: str = "TraceWeaver"
    environment: Literal["local", "staging", "production"] = "local"
    secret_key: str = "changethis"
    api_v1_str: str = "/api/v1"
    access_token_expire_minutes: int = 60 * 24 * 8
    frontend_host: str = "http://localhost:5173"
    cors_origins: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []
    log_level: str = "DEBUG"


class DatabaseConfig(BaseModel):
    server: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""
    name: str = "traceweaver"


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"


class CeleryConfig(BaseModel):
    worker_concurrency: int = 2
    tmp_data_dir: Optional[str] = None


class SmtpConfig(BaseModel):
    host: Optional[str] = None
    port: int = 587
    user: Optional[str] = None
    password: Optional[str] = None
    tls: bool = True
    ssl: bool = False
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None


class AuthConfig(BaseModel):
    email_reset_token_expire_hours: int = 48
    email_test_user: EmailStr = "test@example.com"
    first_superuser: EmailStr = "admin@example.com"
    first_superuser_password: str = "changethis"


class MonitoringConfig(BaseModel):
    sentry_dsn: Optional[HttpUrl] = None


class EmbedderConfig(BaseModel):
    provider: str = "ollama"
    model_name: str = "milkey/m3e:base-f16"
    dimensions: int = 768
    base_url: str = "http://192.168.177.20:11434"
    batch_size: int = 100
    enable_batch: bool = True
    api_key: Optional[str] = None
    api_base: Optional[str] = None


class DayflowConfig(BaseModel):
    db_path: str = "/Users/leo/Library/Application Support/Dayflow/backups/chunks-2026-01-10_010434.sqlite"
    enabled: bool = True


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """从 YAML 文件加载配置的自定义设置源"""

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # 不使用此方法，使用 __call__ 代替
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """加载 YAML 配置文件"""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return {}

        try:
            with open(config_path, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
            return yaml_config
        except Exception as e:
            warnings.warn(f"Failed to load YAML config: {e}", stacklevel=1)
            return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
        env_nested_delimiter="__",
    )

    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    celery: CeleryConfig = CeleryConfig()
    smtp: SmtpConfig = SmtpConfig()
    auth: AuthConfig = AuthConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    embedder: EmbedderConfig = EmbedderConfig()
    dayflow: DayflowConfig = DayflowConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """自定义配置源的优先级

        优先级（从高到低）：
        1. 初始化参数
        2. 环境变量
        3. YAML 配置文件
        4. .env 文件
        5. 文件密钥
        """
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.database.user,
            password=self.database.password,
            host=self.database.server,
            port=self.database.port,
            path=self.database.name,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.app.cors_origins] + [
            self.app.frontend_host
        ]

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.smtp.from_name:
            self.smtp.from_name = self.app.project_name
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.smtp.host and self.smtp.from_email)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.app.environment == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.app.secret_key)
        self._check_default_secret("POSTGRES_PASSWORD", self.database.password)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.auth.first_superuser_password
        )

        return self


settings = Settings()  # type: ignore
