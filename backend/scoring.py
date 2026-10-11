from datetime import datetime

WEIGHTS = {
    "price": 0.35,
    "duration": 0.20,
    "reliability": 0.20,
    "comfort": 0.15,
    "time_of_day": 0.10,
}

# Airport score weights within time_of_day component
AIRPORT_WEIGHT = 0.4
DEPARTURE_TIME_WEIGHT = 0.6


def score_flights(flights: list[dict]) -> list[dict]:
    if not flights:
        return []

    prices = [f["price"] for f in flights]
    durations = [f["duration_outbound_min"] + f["duration_return_min"] for f in flights]

    min_price, max_price = min(prices), max(prices)
    min_dur, max_dur = min(durations), max(durations)

    for flight in flights:
        flight["score"] = _compute_score(flight, min_price, max_price, min_dur, max_dur)

    return sorted(flights, key=lambda f: f["score"], reverse=True)


def _compute_score(
    flight: dict,
    min_price: float,
    max_price: float,
    min_dur: int,
    max_dur: int,
) -> float:
    price_score = _normalize_inv(flight["price"], min_price, max_price)

    total_dur = flight["duration_outbound_min"] + flight["duration_return_min"]
    duration_score = _normalize_inv(total_dur, min_dur, max_dur)

    # No external reliability data yet — use stops as proxy (fewer = more reliable)
    stops = flight["stops_outbound"] + flight["stops_return"]
    reliability_score = max(0.0, 1.0 - stops * 0.3)

    # Comfort: direct flights score higher, bags recheck is a penalty
    comfort_score = reliability_score * (0.8 if flight["bags_recheck_required"] else 1.0)

    time_score = _time_of_day_score(
        flight["departure_at"],
        flight["_uae_airport_score"],
        flight["_msc_airport_score"],
    )

    return (
        WEIGHTS["price"] * price_score
        + WEIGHTS["duration"] * duration_score
        + WEIGHTS["reliability"] * reliability_score
        + WEIGHTS["comfort"] * comfort_score
        + WEIGHTS["time_of_day"] * time_score
    )


def _time_of_day_score(departure_at: str, uae_score: float, msc_score: float) -> float:
    airport_score = (uae_score + msc_score) / 2

    try:
        dt = datetime.fromisoformat(departure_at)
    except (ValueError, TypeError):
        return airport_score

    hour = dt.hour
    weekday = dt.weekday()  # 0=Mon, 6=Sun
    is_weekday = weekday < 5

    if is_weekday:
        # Prefer flights after 18:00 on weekdays
        departure_time_score = 1.0 if hour >= 18 else 0.3
    else:
        # Weekends: neutral, slight preference for daytime
        departure_time_score = 1.0 if 8 <= hour < 22 else 0.6

    return AIRPORT_WEIGHT * airport_score + DEPARTURE_TIME_WEIGHT * departure_time_score


def _normalize_inv(value: float, min_val: float, max_val: float) -> float:
    """Lower value → higher score (inverted normalization)."""
    if max_val == min_val:
        return 1.0
    return 1.0 - (value - min_val) / (max_val - min_val)
