from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    role: str
    authenticated: bool = True


class AuthManager:
    """
    Lightweight backend authentication layer.

    Production deployment should place this behind the application's
    identity provider/JWT issuer. API keys are also supported for
    internal service-to-service communication.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("BACKEND_API_KEY", "")
        self.admin_api_key = os.getenv("ADMIN_API_KEY", "")
        self.jwt_secret = os.getenv("JWT_SECRET", "")

    # ------------------------------------------------------------------
    # API KEY
    # ------------------------------------------------------------------

    def authenticate_api_key(
        self,
        provided_key: str,
    ) -> AuthenticatedUser | None:
        if not provided_key:
            return None

        if self.admin_api_key and hmac.compare_digest(
            provided_key,
            self.admin_api_key,
        ):
            return AuthenticatedUser(
                user_id="admin",
                role="admin",
            )

        if self.api_key and hmac.compare_digest(
            provided_key,
            self.api_key,
        ):
            return AuthenticatedUser(
                user_id="service",
                role="service",
            )

        return None

    # ------------------------------------------------------------------
    # TOKEN
    # ------------------------------------------------------------------

    def generate_service_token(
        self,
        user_id: str,
        role: str = "service",
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a signed internal token.

        Format:
            user_id.role.expiry.signature
        """

        if not self.jwt_secret:
            raise RuntimeError(
                "JWT_SECRET is not configured."
            )

        expires_at = int(time.time()) + expires_in

        payload = (
            f"{user_id}.{role}.{expires_at}"
        )

        signature = hmac.new(
            self.jwt_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"{payload}.{signature}"

    # ------------------------------------------------------------------
    # VERIFY TOKEN
    # ------------------------------------------------------------------

    def verify_service_token(
        self,
        token: str,
    ) -> AuthenticatedUser | None:
        if not token or not self.jwt_secret:
            return None

        parts = token.split(".")

        if len(parts) != 4:
            return None

        user_id, role, expiry, signature = parts

        try:
            expires_at = int(expiry)
        except ValueError:
            return None

        if expires_at < int(time.time()):
            return None

        payload = (
            f"{user_id}.{role}.{expiry}"
        )

        expected_signature = hmac.new(
            self.jwt_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            return None

        return AuthenticatedUser(
            user_id=user_id,
            role=role,
        )

    # ------------------------------------------------------------------
    # REQUEST TOKEN
    # ------------------------------------------------------------------

    def authenticate(
        self,
        *,
        api_key: str | None = None,
        token: str | None = None,
    ) -> AuthenticatedUser | None:
        """
        Authenticate using either a service token or API key.
        """

        if token:
            user = self.verify_service_token(
                token
            )

            if user:
                return user

        if api_key:
            user = self.authenticate_api_key(
                api_key
            )

            if user:
                return user

        return None

    # ------------------------------------------------------------------
    # NONCE
    # ------------------------------------------------------------------

    @staticmethod
    def generate_nonce() -> str:
        """
        Generate a cryptographically secure request nonce.
        """

        return secrets.token_urlsafe(32)

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(self) -> dict[str, bool]:
        return {
            "api_key_configured": bool(
                self.api_key
            ),
            "admin_key_configured": bool(
                self.admin_api_key
            ),
            "jwt_secret_configured": bool(
                self.jwt_secret
            ),
            "ready": bool(
                self.api_key
                or self.admin_api_key
                or self.jwt_secret
            ),
        }


auth_manager = AuthManager()