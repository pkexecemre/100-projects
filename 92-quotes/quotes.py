#!/usr/bin/env python3
"""Pick a random quote from a small embedded collection, with tag filtering."""
import argparse
import json
import random
import sys

QUOTES = [
    ("The only way out is through.", "Robert Frost", ["wisdom", "life"]),
    ("Simplicity is the soul of efficiency.", "Austin Freeman", ["tech", "wisdom"]),
    ("Talk is cheap. Show me the code.", "Linus Torvalds", ["tech", "humor"]),
    ("Premature optimization is the root of all evil.", "Donald Knuth", ["tech", "wisdom"]),
    ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke", ["tech", "wisdom"]),
    ("I have not failed. I've just found 10,000 ways that won't work.", "Thomas Edison", ["courage", "tech"]),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese proverb", ["wisdom", "life"]),
    ("It always seems impossible until it's done.", "Nelson Mandela", ["courage", "life"]),
    ("Do or do not. There is no try.", "Yoda", ["courage", "humor"]),
    ("Good judgment comes from experience, and experience comes from bad judgment.", "Rita Mae Brown", ["wisdom", "humor"]),
    ("A ship in harbor is safe, but that is not what ships are built for.", "John A. Shedd", ["courage", "life"]),
    ("The computer was born to solve problems that did not exist before.", "Bill Gates", ["tech", "humor"]),
    ("Measure twice, cut once.", "Proverb", ["wisdom", "life"]),
    ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan", ["tech", "wisdom"]),
    ("Life is what happens when you're busy making other plans.", "John Lennon", ["life", "wisdom"]),
    ("If you can't explain it simply, you don't understand it well enough.", "Albert Einstein", ["wisdom", "tech"]),
    ("The journey of a thousand miles begins with a single step.", "Lao Tzu", ["life", "courage"]),
    ("Programs must be written for people to read.", "Harold Abelson", ["tech", "wisdom"]),
]


def tags() -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, _, quote_tags in QUOTES:
        for tag in quote_tags:
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items()))


def pick(tag: str | None, rng: random.Random) -> tuple[str, str, list[str]]:
    pool = [q for q in QUOTES if tag is None or tag in q[2]]
    if not pool:
        raise KeyError(tag)
    return rng.choice(pool)


def as_dict(quote: tuple[str, str, list[str]]) -> dict:
    text, author, quote_tags = quote
    return {"text": text, "author": author, "tags": quote_tags}


def self_test() -> None:
    assert len(QUOTES) >= 10
    known = tags()
    assert "tech" in known and "life" in known
    for text, author, quote_tags in QUOTES:
        assert text and author and quote_tags
        assert all(tag in known for tag in quote_tags)
    a = pick("tech", random.Random(7))
    b = pick("tech", random.Random(7))
    assert a == b and "tech" in a[2]
    assert as_dict(a)["text"] == a[0]
    print(f"self-test: ok ({len(QUOTES)} quotes, {len(known)} tags)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Print a random quote from an embedded list.")
    ap.add_argument("--tag", help="only pick quotes carrying this tag")
    ap.add_argument("--list", action="store_true", help="list every quote")
    ap.add_argument("--list-tags", action="store_true", help="list tags with counts")
    ap.add_argument("--seed", type=int, help="seed for reproducible picks")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run internal checks and exit")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    if args.list_tags:
        for tag, count in tags().items():
            print(f"{tag:<8} {count}")
        return 0
    if args.tag and args.tag not in tags():
        print(f"quotes: unknown tag {args.tag!r}; try: {', '.join(tags())}", file=sys.stderr)
        return 2
    if args.list:
        for i, (text, author, quote_tags) in enumerate(QUOTES, 1):
            print(f"{i:>2}. {text} -- {author} [{', '.join(quote_tags)}]")
        return 0

    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    try:
        quote = pick(args.tag, rng)
    except KeyError:
        print(f"quotes: no quotes tagged {args.tag!r}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(as_dict(quote), indent=2))
    else:
        print(f'"{quote[0]}"\n  -- {quote[1]}  [{", ".join(quote[2])}]')
    return 0


if __name__ == "__main__":
    sys.exit(main())
