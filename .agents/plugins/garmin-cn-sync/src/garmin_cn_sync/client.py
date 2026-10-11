from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .secrets import SecretStore


@dataclass
class GarminSession:
    api: object
    secrets: SecretStore

    def persist_tokens(self) -> None:
        self.secrets.save_tokens(self.api.client.dumps())


class GarminClientFactory:
    def __init__(self, secrets: SecretStore | None = None) -> None:
        self.secrets = secrets or SecretStore()

    def connect(self, prompt_mfa: Callable[[], str] | None = None) -> GarminSession:
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
