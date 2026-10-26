from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .secrets import SecretStore
from .config import selected_provider


@dataclass
class GarminSession:
    api: object
    secrets: SecretStore
    provider: str = "china-web"

    def persist_tokens(self) -> None:
        if self.provider == "china-web":
            self.secrets.save_tokens(self.api.client.dumps())

    def close(self) -> None:
        if self.provider == "personal-api":
            self.api.close()


class GarminClientFactory:
    def __init__(self, secrets: SecretStore | None = None) -> None:
        self.secrets = secrets or SecretStore()

    def connect(self, prompt_mfa: Callable[[], str] | None = None) -> GarminSession:
        if selected_provider(bool(self.secrets.load_personal_api_key())) == "personal-api":
            from .personal_api import PersonalApiClient
            if not self.secrets.load_personal_api_key():
                raise RuntimeError("Personal API key missing. Run scripts/authenticate-personal.ps1.")
            api = PersonalApiClient(self.secrets)
            try:
                api.authenticate()
            except Exception:
                api.close()
                raise
            return GarminSession(api=api, secrets=self.secrets, provider="personal-api")
        credentials = self.secrets.load_credentials()
        if credentials is None:
            raise RuntimeError("Garmin credentials missing. Run scripts/authenticate.ps1 first.")
        from garminconnect import Garmin

        api = Garmin(credentials.email, credentials.password, is_cn=True, prompt_mfa=prompt_mfa, retry_attempts=2)
        api.login(self.secrets.load_tokens())
        session = GarminSession(api=api, secrets=self.secrets)
        session.persist_tokens()
        return session


def authenticate(email: str, password: str, prompt_mfa: Callable[[], str]) -> GarminSession:
    from garminconnect import Garmin

    api = Garmin(email, password, is_cn=True, prompt_mfa=prompt_mfa, retry_attempts=2)
    api.login()
    store = SecretStore()
    store.save_credentials(email, password)
    session = GarminSession(api=api, secrets=store)
    session.persist_tokens()
    return session
