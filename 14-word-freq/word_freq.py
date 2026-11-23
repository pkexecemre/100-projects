#!/usr/bin/env python3
"""Count the most frequent words in text, with optional stopword filtering."""

import argparse
import json
import re
import sys
from collections import Counter

STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can cannot could couldn't did didn't
do does doesn't doing don't down during each few for from further had hadn't has
hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself
let's me more most mustn't my myself no nor not of off on once only or other ought
our ours ourselves out over own same shan't she she'd she'll she's should shouldn't
so some such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under until up
very was wasn't we we'd we'll we're we've were weren't what what's when when's where
where's which while who who's whom why why's with won't would wouldn't you you'd
you'll you're you've your yours yourself yourselves
""".split())

TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text):
    """Lowercase word tokens that contain at least one letter."""
    for token in TOKEN_RE.findall(text.casefold()):
        if any(char.isalpha() for char in token):
            yield token


def count_words(text, top=10, min_length=1, stopwords=STOPWORDS):
    counts = Counter()
    for token in tokenize(text):
        if len(token) < min_length:
            continue
        if stopwords and token in stopwords:
            continue
        counts[token] += 1
    return counts.most_common(top)


def load_stopwords(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return {line.strip().casefold() for line in handle
                    if line.strip() and not line.startswith("#")}
    except OSError as exc:
        raise ValueError("cannot read stopwords: %s" % exc)


def self_test():
    text = "The cat and the hat. A CAT! Do not stop the cat's nap."
    pairs = count_words(text, top=3, stopwords=STOPWORDS)
    assert pairs[0] == ("cat", 3)
    assert ("the", 6) not in pairs
    assert ("and", 1) not in pairs
    raw = count_words(text, top=2, stopwords=set())
    assert raw[0] == ("the", 3)
    short = count_words("go go going going going", top=5, min_length=3)
    assert short == [("going", 3)]
    case = count_words("Python python PYTHON", top=1, stopwords=set())
    assert case == [("python", 3)]
    assert count_words("", top=5) == []
    import os
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                     encoding="utf-8") as handle:
        handle.write("# comment\nCustom\n")
        path = handle.name
    try:
        custom = load_stopwords(path)
    finally:
        os.unlink(path)
    assert custom == {"custom"}
    print("self-test: 8 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Show the most frequent words in a text file or stdin.")
    parser.add_argument("file", nargs="?", default="-",
                        help="text file, or - for stdin (default)")
    parser.add_argument("--top", type=int, default=10, metavar="N",
                        help="number of words to show (default 10)")
    parser.add_argument("--min-length", type=int, default=1, metavar="N",
                        help="ignore words shorter than N characters")
    parser.add_argument("--stopwords", metavar="FILE",
                        help="extra stopword file (one word per line)")
    parser.add_argument("--no-stopwords", action="store_true",
                        help="count stopwords too")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if args.top < 1:
        parser.error("--top must be at least 1")
    if args.min_length < 1:
        parser.error("--min-length must be at least 1")

    stops = set() if args.no_stopwords else set(STOPWORDS)
    try:
        if args.stopwords:
            stops |= load_stopwords(args.stopwords)
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
    except OSError as exc:
        print("word-freq: error: %s" % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        print("word-freq: error: %s" % exc, file=sys.stderr)
        return 2

    pairs = count_words(text, args.top, args.min_length, stops)
    if not pairs:
        print("word-freq: error: no words found", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([{"word": word, "count": count} for word, count in pairs],
                         indent=2))
    else:
        width = len(str(pairs[0][1]))
        for word, count in pairs:
            print("%*d  %s" % (width, count, word))
    return 0


if __name__ == "__main__":
    sys.exit(main())
