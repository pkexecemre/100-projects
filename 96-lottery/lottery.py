#!/usr/bin/env python3
"""Draw lottery-style sets of unique numbers from a configurable range."""
import argparse
import json
import random
import sys


def draw(minimum: int, maximum: int, count: int, sets: int = 1,
         seed: int | None = None, sort: bool = True) -> list[list[int]]:
    if minimum >= maximum:
        raise ValueError("minimum must be less than maximum")
    size = maximum - minimum + 1
    if not 1 <= count <= size:
        raise ValueError(f"count must be between 1 and {size} for this range")
    if not 1 <= sets <= 100:
        raise ValueError("sets must be between 1 and 100")
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    tickets = []
    for _ in range(sets):
        numbers = rng.sample(range(minimum, maximum + 1), count)
        tickets.append(sorted(numbers) if sort else numbers)
    return tickets


def self_test() -> None:
    tickets = draw(1, 49, 6, sets=3, seed=1234)
    assert len(tickets) == 3
    for ticket in tickets:
        assert len(ticket) == 6 and len(set(ticket)) == 6
        assert all(1 <= n <= 49 for n in ticket)
        assert ticket == sorted(ticket)
    assert tickets == draw(1, 49, 6, sets=3, seed=1234), "seeded draws differ"
    assert draw(1, 10, 10, seed=5) == [list(range(1, 11))]
    unsorted = draw(1, 49, 6, seed=1, sort=False)
    assert len(set(unsorted[0])) == 6
    for bad in [(5, 5, 1), (1, 5, 6), (1, 10, 0)]:
        try:
            draw(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid arguments accepted: {bad}")
    print("self-test: ok (unique ranges, seeded determinism, validation)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Draw unique lottery numbers.")
    ap.add_argument("--min", type=int, default=1, help="lowest number (default: 1)")
    ap.add_argument("--max", type=int, default=49, help="highest number (default: 49)")
    ap.add_argument("--count", type=int, default=6, help="numbers per ticket (default: 6)")
    ap.add_argument("--sets", type=int, default=1, help="number of tickets (default: 1)")
    ap.add_argument("--seed", type=int, help="seed for reproducible draws")
    ap.add_argument("--no-sort", action="store_true", help="keep draw order instead of sorting")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    try:
        tickets = draw(args.min, args.max, args.count, args.sets, args.seed, not args.no_sort)
    except ValueError as exc:
        print(f"lottery: {exc}", file=sys.stderr)
        return 2
    if args.json:
        payload = {
            "min": args.min, "max": args.max, "count": args.count,
            "sets": args.sets, "seed": args.seed, "tickets": tickets,
        }
        print(json.dumps(payload, indent=2))
        return 0
    print(f"Lottery draw (range {args.min}-{args.max}, {args.count} unique numbers)")
    for i, ticket in enumerate(tickets, 1):
        print(f"Ticket {i}: " + "  ".join(f"{n:>2}" for n in ticket))
    return 0


if __name__ == "__main__":
    sys.exit(main())
