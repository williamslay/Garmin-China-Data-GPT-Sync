from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .config import KEYRING_SERVICE


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str


class SecretStore:
    """Store Garmin credentials and refresh tokens in the OS credential vault."""

    TOKEN_MARKER = "tokens-cn"
    TOKEN_CHUNK_SIZE = 900

    def __init__(self, service: str = KEYRING_SERVICE) -> None:
        self.service = service

    @staticmethod
    def _keyring():
        import keyring

        return keyring

    def save_credentials(self, email: str, password: str) -> None:
        email = email.strip()
        if not email or not password:
            raise ValueError("Email and password are required")
        keyring = self._keyring()
        keyring.set_password(self.service, "email", email)
        keyring.set_password(self.service, "password", password)

    def load_credentials(self) -> Credentials | None:
        keyring = self._keyring()
        email = keyring.get_password(self.service, "email")
        password = keyring.get_password(self.service, "password")
        if not email or not password:
            return None
        return Credentials(email=email, password=password)

    def save_personal_api_key(self, api_key: str) -> None:
        api_key = api_key.strip()
        if not api_key or any(ch.isspace() for ch in api_key):
            raise ValueError("A single nonempty Personal API key is required")
        self._keyring().set_password(self.service, "personal-api-key-cn", api_key)

    def load_personal_api_key(self) -> str | None:
        return self._keyring().get_password(self.service, "personal-api-key-cn")

    def save_personal_tokens(self, token_json: str) -> None:
        # A separate vault service keeps web-session and official bearer-token chunks isolated.
        SecretStore(self.service + ".PersonalApi.CN").save_tokens(token_json)

    def load_personal_tokens(self) -> str | None:
        return SecretStore(self.service + ".PersonalApi.CN").load_tokens()

    def save_tokens(self, token_json: str) -> None:
        if not token_json.strip().startswith("{"):
            raise ValueError("Refusing to store malformed Garmin token data")
        keyring = self._keyring()
        previous_marker = keyring.get_password(self.service, self.TOKEN_MARKER)
        digest = hashlib.sha256(token_json.encode("utf-8")).hexdigest()[:16]
        chunks = [
            token_json[index:index + self.TOKEN_CHUNK_SIZE]
            for index in range(0, len(token_json), self.TOKEN_CHUNK_SIZE)
        ]
        chunk_names = [f"tokens-cn-{digest}-{index:03d}" for index in range(len(chunks))]

        written: list[str] = []
        try:
            for name, chunk in zip(chunk_names, chunks, strict=True):
                keyring.set_password(self.service, name, chunk)
                written.append(name)
            keyring.set_password(
                self.service,
                self.TOKEN_MARKER,
                f"chunks-v1:{digest}:{len(chunks)}",
            )
        except Exception:
            for name in written:
                self._delete_password(keyring, name)
            raise

        for name in self._chunk_names(previous_marker):
            if name not in chunk_names:
                self._delete_password(keyring, name)

    def load_tokens(self) -> str | None:
        keyring = self._keyring()
        marker = keyring.get_password(self.service, self.TOKEN_MARKER)
        if marker is None or marker.startswith("{"):
            return marker
        names = self._chunk_names(marker)
        if not names:
            raise RuntimeError("Malformed Garmin token marker in Windows Credential Manager")
        chunks = [keyring.get_password(self.service, name) for name in names]
        if any(chunk is None for chunk in chunks):
            raise RuntimeError("Incomplete Garmin token set in Windows Credential Manager")
        return "".join(chunk for chunk in chunks if chunk is not None)

    def _delete_password(self, keyring: object, username: str) -> None:
        try:
            keyring.delete_password(self.service, username)
        except keyring.errors.PasswordDeleteError:
            pass

    @staticmethod
    def _chunk_names(marker: str | None) -> list[str]:
        if not marker or not marker.startswith("chunks-v1:"):
            return []
        try:
            _, digest, count_text = marker.split(":", 2)
            count = int(count_text)
        except (TypeError, ValueError):
            return []
        if not digest or count < 1 or count > 128:
            return []
        return [f"tokens-cn-{digest}-{index:03d}" for index in range(count)]

    def clear(self) -> None:
        keyring = self._keyring()
        marker = keyring.get_password(self.service, self.TOKEN_MARKER)
        for username in ("email", "password", self.TOKEN_MARKER, *self._chunk_names(marker)):
            self._delete_password(keyring, username)
