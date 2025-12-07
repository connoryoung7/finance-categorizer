from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    ynab_access_key: str
    mistral_access_key: str

settings = Settings()
