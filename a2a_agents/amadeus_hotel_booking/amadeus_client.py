import os
import time
import httpx


class AmadeusClient:
    def __init__(self):
        self.base_url = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET in .env")

        self._token = None
        self._token_expiry = 0

    async def _get_token(self):
        if self._token and time.time() < self._token_expiry:
            return self._token

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if r.status_code != 200:
            raise RuntimeError(f"Amadeus auth failed: {r.status_code} {r.text}")

        data = r.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 1800))
        self._token_expiry = time.time() + (expires_in - 30)
        return self._token

    async def get(self, endpoint: str, params: dict):
        token = await self._get_token()

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(
                f"{self.base_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )

        if r.status_code >= 400:
            raise RuntimeError(f"Amadeus GET failed: {r.status_code} {r.text}")

        return r.json()
