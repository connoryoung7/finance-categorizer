from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    ynab_access_key: str
    ynab_budget_id: str
    mistral_access_key: str
    nylas_api_key: str
    nylas_api_uri: str
    nylas_client_id: str
    nylas_grant_id: str

settings = Settings()
