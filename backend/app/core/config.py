from typing import Optional
import secrets
import warnings
from typing import Annotated, Any, Literal
from pathlib import Path

import yaml
from pydantic import (
    AnyUrl,
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


def flatten_yaml_config(config: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
    """将嵌套的 YAML 配置展平为环境变量风格的键值对
    
    例如: {"database": {"server": "localhost"}} -> {"POSTGRES_SERVER": "localhost"}
    """
    items: list[tuple[str, Any]] = []
    
    for k, v in config.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_yaml_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    # 将键转换为大写的环境变量风格
    result = {}
    for key, value in items:
        # 映射 YAML 键到环境变量键
        yaml_to_env_mapping = {
            "app_project_name": "PROJECT_NAME",
            "app_environment": "ENVIRONMENT",
            "app_secret_key": "SECRET_KEY",
            "app_api_v1_str": "API_V1_STR",
            "app_access_token_expire_minutes": "ACCESS_TOKEN_EXPIRE_MINUTES",
            "app_frontend_host": "FRONTEND_HOST",
            "app_cors_origins": "BACKEND_CORS_ORIGINS",
            "app_log_level": "LOG_LEVEL",
            "database_server": "POSTGRES_SERVER",
            "database_port": "POSTGRES_PORT",
            "database_user": "POSTGRES_USER",
            "database_password": "POSTGRES_PASSWORD",
            "database_name": "POSTGRES_DB",
            "redis_url": "REDIS_URL",
            "celery_worker_concurrency": "CELERY_WORKER_CONCURRENCY",
            "celery_tmp_data_dir": "CELERY_TMP_DATA_DIR",
            "smtp_host": "SMTP_HOST",
            "smtp_port": "SMTP_PORT",
            "smtp_user": "SMTP_USER",
            "smtp_password": "SMTP_PASSWORD",
            "smtp_tls": "SMTP_TLS",
            "smtp_ssl": "SMTP_SSL",
            "smtp_from_email": "EMAILS_FROM_EMAIL",
            "smtp_from_name": "EMAILS_FROM_NAME",
            "auth_email_reset_token_expire_hours": "EMAIL_RESET_TOKEN_EXPIRE_HOURS",
            "auth_email_test_user": "EMAIL_TEST_USER",
            "auth_first_superuser": "FIRST_SUPERUSER",
            "auth_first_superuser_password": "FIRST_SUPERUSER_PASSWORD",
            "monitoring_sentry_dsn": "SENTRY_DSN",
            "embedder_provider": "EMBEDDER_PROVIDER",
            "embedder_model_name": "EMBEDDER_MODEL_NAME",
            "embedder_dimensions": "EMBEDDER_DIMENSIONS",
            "embedder_base_url": "EMBEDDER_BASE_URL",
            "embedder_batch_size": "EMBEDDER_BATCH_SIZE",
            "embedder_enable_batch": "EMBEDDER_ENABLE_BATCH",
            "embedder_api_key": "EMBEDDER_API_KEY",
            "embedder_api_base": "EMBEDDER_API_BASE",
            "dayflow_local_db_path": "DAYFLOW_LOCAL_DB_PATH",
            "dayflow_local_enabled": "DAYFLOW_LOCAL_ENABLED",
        }
        
        env_key = yaml_to_env_mapping.get(key.lower())
        if env_key:
            result[env_key] = value
    
    return result


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """从 YAML 文件加载配置的自定义设置源"""
    
    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # 不使用此方法，使用 __call__ 代替
        return None, field_name, False
    
    def __call__(self) -> dict[str, Any]:
        """加载 YAML 配置文件"""
        # 尝试从 backend/config.yaml 加载
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
            
            # 展平配置
            flattened = flatten_yaml_config(yaml_config)
            return flattened
        except Exception as e:
            warnings.warn(f"Failed to load YAML config: {e}", stacklevel=1)
            return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
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
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    LOG_LEVEL: str = "DEBUG"

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # Redis configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery configuration
    CELERY_WORKER_CONCURRENCY: int = 2
    CELERY_TMP_DATA_DIR: Optional[str] = None

    # Embedder configuration
    EMBEDDER_PROVIDER: str = "ollama"
    EMBEDDER_MODEL_NAME: str = "milkey/m3e:base-f16"
    EMBEDDER_DIMENSIONS: int = 768
    EMBEDDER_BASE_URL: str = "http://192.168.177.20:11434"
    EMBEDDER_BATCH_SIZE: int = 100
    EMBEDDER_ENABLE_BATCH: bool = True
    EMBEDDER_API_KEY: Optional[str] = None
    EMBEDDER_API_BASE: Optional[str] = None

    # Dayflow local database configuration
    DAYFLOW_LOCAL_DB_PATH: str = "/Users/leo/Library/Application Support/Dayflow/backups/chunks-2026-01-10_010434.sqlite"
    DAYFLOW_LOCAL_ENABLED: bool = True

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
