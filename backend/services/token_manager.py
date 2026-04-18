import asyncio
import hashlib
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import find_dotenv, load_dotenv, set_key


load_dotenv()


class TokenManager:
    def __init__(self):
        self.api_key = os.getenv("GROWW_API_KEY", "")
        self.api_secret = os.getenv("GROWW_API_SECRET", "")
        self.base_url = os.getenv("GROWW_BASE_URL", "https://api.groww.in")
        self._token: str = os.getenv("GROWW_ACCESS_TOKEN", "")
        self._token_generated_at: datetime | None = None

        if self._token:
            self._token_generated_at = datetime.now(timezone.utc)

    def _generate_checksum(self) -> tuple[str, str]:
        timestamp = str(int(time.time()))
        input_str = self.api_secret + timestamp
        checksum = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
        return checksum, timestamp

    def _is_token_expired(self) -> bool:
        if self._token_generated_at is None:
            return True
        if not self._token:
            return True

        now = datetime.now(timezone.utc)
        generated = self._token_generated_at
        today_reset = datetime(now.year, now.month, now.day, 0, 30, 0, tzinfo=timezone.utc)

        if now < today_reset:
            reset_time = today_reset - timedelta(days=1)
        else:
            reset_time = today_reset

        return generated < reset_time

    async def get_token(self) -> str:
        if not self._is_token_expired() and self._token:
            return self._token

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "GROWW_API_KEY and GROWW_API_SECRET must be set in .env "
                "to generate tokens"
            )

        for attempt in range(3):
            try:
                checksum, timestamp = self._generate_checksum()

                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/token/api/access",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "key_type": "approval",
                            "checksum": checksum,
                            "timestamp": timestamp,
                        },
                    )

                if response.status_code == 200:
                    data = response.json()
                    self._token = data["token"]
                    self._token_generated_at = datetime.now(timezone.utc)

                    dotenv_path = find_dotenv()
                    if dotenv_path:
                        set_key(dotenv_path, "GROWW_ACCESS_TOKEN", self._token)

                    print(
                        "[TokenManager] New token generated at "
                        f"{datetime.now(timezone.utc).isoformat()}"
                    )
                    return self._token

                raise Exception(
                    f"Token generation failed: "
                    f"{response.status_code} {response.text}"
                )
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    async def invalidate(self):
        self._token = ""
        self._token_generated_at = None
        print(
            "[TokenManager] Token invalidated, "
            "will regenerate on next request"
        )

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_secret)


token_manager = TokenManager()
