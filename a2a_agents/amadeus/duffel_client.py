import os
import httpx


class DuffelClient:
    """Minimal async client for Duffel Flights (offers search only).

    Docs: https://duffel.com/docs/api/air/offer-requests
    This client only performs a search for offers; it does not create orders.
    """

    def __init__(self) -> None:
        self.base_url = os.getenv("DUFFEL_BASE_URL", "https://api.duffel.com")
        self.access_token = os.getenv("DUFFEL_ACCESS_TOKEN")

        if not self.access_token:
            raise RuntimeError("Missing DUFFEL_ACCESS_TOKEN in environment or .env file")

    async def search_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None = None,
        cabin_class: str | None = None,
    ):
        """Create an offer request for 1 adult between origin and destination.

        origin, destination: IATA city/airport codes (e.g. NYC, ATL, MAA)
        departure_date, return_date: ISO YYYY-MM-DD strings
        cabin_class: 'economy' | 'premium_economy' | 'business' | 'first'
        """

        slices: list[dict] = [
            {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
            }
        ]

        if return_date:
            slices.append(
                {
                    "origin": destination,
                    "destination": origin,
                    "departure_date": return_date,
                }
            )

        payload: dict = {
            "slices": slices,
            "passengers": [
                {"type": "adult"},
            ],
        }

        if cabin_class:
            payload["cabin_class"] = cabin_class

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Explicit version header recommended by Duffel
            "Duffel-Version": os.getenv("DUFFEL_API_VERSION", "v1"),
        }

        url = f"{self.base_url}/air/offer_requests"

        # Duffel v2 expects the request body to be nested under a top-level
        # "data" key.
        body = {"data": payload}

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=body, headers=headers)

        if r.status_code >= 400:
            raise RuntimeError(f"Duffel offer request failed: {r.status_code} {r.text}")

        return r.json()
