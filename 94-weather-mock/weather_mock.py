#!/usr/bin/env python3
"""Deterministic, entirely fictional weather reports. No network access."""
import argparse
import hashlib
import json
import random
import sys

CONDITIONS = [
    "clear", "partly cloudy", "overcast", "light rain", "heavy rain",
    "thunderstorms", "fog", "snow", "windy", "hail",
]
WIND_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _rng(city: str) -> random.Random:
    digest = hashlib.sha256(city.strip().lower().encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def forecast(city: str, days: int = 3) -> dict:
    if not city.strip():
        raise ValueError("city must not be empty")
    if not 1 <= days <= 7:
        raise ValueError("days must be between 1 and 7")
    rng = _rng(city)
    reports = []
    for day in range(1, days + 1):
        temp_c = rng.randint(-8, 34)
        condition = rng.choice(CONDITIONS)
        reports.append({
            "day": day,
            "condition": condition,
            "temp_c": temp_c,
            "temp_f": round(temp_c * 9 / 5 + 32),
            "humidity": rng.randint(25, 98),
            "wind_kmh": rng.randint(2, 55),
            "wind_dir": rng.choice(WIND_DIRS),
        })
    return {"city": city.strip(), "mock": True, "days": reports}


def to_f(celsius: int) -> int:
    return round(celsius * 9 / 5 + 32)


def self_test() -> None:
    a = forecast("Lisbon", 3)
    b = forecast(" Lisbon ", 3)
    assert a == b, "forecast is not deterministic"
    assert a["mock"] is True and len(a["days"]) == 3
    for day in a["days"]:
        assert 1 <= day["day"] <= 3
        assert -8 <= day["temp_c"] <= 34
        assert to_f(day["temp_c"]) == day["temp_f"]
        assert 25 <= day["humidity"] <= 98
        assert 2 <= day["wind_kmh"] <= 55
    assert forecast("Oslo", 1)["days"][0]["day"] == 1
    assert forecast("Oslo", 7)["days"][-1]["day"] == 7
    try:
        forecast("", 3)
    except ValueError:
        pass
    else:
        raise AssertionError("empty city accepted")
    print("self-test: ok (deterministic mock forecast, no network)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Show fictional weather for a city (offline mock).")
    ap.add_argument("city", nargs="?", help="city name (any string; output is fake)")
    ap.add_argument("--days", type=int, default=3, help="forecast length, 1-7 (default: 3)")
    ap.add_argument("--units", choices=["c", "f"], default="c", help="display units (default: c)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.city:
        ap.error("a city name is required")
    try:
        report = forecast(args.city, args.days)
    except ValueError as exc:
        print(f"weather-mock: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print("MOCK WEATHER - FICTIONAL DATA, NO NETWORK USED")
    print(f"City: {report['city']}")
    for day in report["days"]:
        temp = f"{day['temp_c']}C" if args.units == "c" else f"{day['temp_f']}F"
        print(f"  Day {day['day']}: {day['condition']}, {temp}, "
              f"humidity {day['humidity']}%, wind {day['wind_kmh']} km/h {day['wind_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
