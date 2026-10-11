import os
import httpx
from datetime import date

TEQUILA_BASE = "https://tequila-api.kiwi.com/v2/search"

# Airport priority scores (higher = better)
UAE_AIRPORT_SCORE = {"DXB": 1.0, "AUH": 0.7, "DWC": 0.3}
MSC_AIRPORT_SCORE = {"SVO": 1.0, "VKO": 0.7, "DME": 0.3}


async def fetch_flights(
    date_from: date,
    date_to: date,
    return_from: date,
    return_to: date,
) -> list[dict]:
    api_key = os.getenv("TEQUILA_API_KEY")
    if not api_key:
        raise RuntimeError("TEQUILA_API_KEY not set")

    params = {
        "fly_from": "DXB,AUH,DWC",
        "fly_to": "SVO,VKO,DME",
        "date_from": date_from.strftime("%d/%m/%Y"),
        "date_to": date_to.strftime("%d/%m/%Y"),
        "return_from": return_from.strftime("%d/%m/%Y"),
        "return_to": return_to.strftime("%d/%m/%Y"),
        "flight_type": "round",
        "adults": 1,
        "curr": "USD",
        "locale": "ru",
        "limit": 50,
        "sort": "quality",
    }

    headers = {"apikey": api_key}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(TEQUILA_BASE, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return [_parse_flight(f) for f in data.get("data", [])]


def _parse_flight(raw: dict) -> dict:
    departure_airport = raw.get("flyFrom", "")
    arrival_airport = raw.get("flyTo", "")
    departure_dt = raw.get("local_departure", "")  # ISO 8601

    return {
        "id": raw.get("id"),
        "price": raw.get("price"),
        "currency": "USD",
        "departure_airport": departure_airport,
        "arrival_airport": arrival_airport,
        "departure_at": departure_dt,
        "arrival_at": raw.get("local_arrival", ""),
        "return_departure_at": raw.get("route", [{}])[-1].get("local_departure", "") if raw.get("route") else "",
        "duration_outbound_min": raw.get("duration", {}).get("departure", 0) // 60,
        "duration_return_min": raw.get("duration", {}).get("return", 0) // 60,
        "stops_outbound": len([r for r in raw.get("route", []) if r.get("return") == 0]) - 1,
        "stops_return": len([r for r in raw.get("route", []) if r.get("return") == 1]) - 1,
        "airline": raw.get("airlines", [""])[0],
        "deep_link": raw.get("deep_link", ""),
        "bags_recheck_required": raw.get("bags_recheck_required", False),
        # Pre-computed for scoring
        "_uae_airport_score": UAE_AIRPORT_SCORE.get(departure_airport, 0.0),
        "_msc_airport_score": MSC_AIRPORT_SCORE.get(arrival_airport, 0.0),
    }
