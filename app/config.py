"""
Configuração da aplicação via variáveis de ambiente.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_explanation_model: str = "gpt-4o-mini"
    app_env: str = "development"
    log_level: str = "INFO"
    eval_dataset_path: str = "data/processed/test.jsonl"

    @property
    def eval_dataset_path_resolved(self) -> Path:
        """Retorna o caminho absoluto do dataset de avaliação."""
        return Path(self.eval_dataset_path).resolve()


settings = Settings()
