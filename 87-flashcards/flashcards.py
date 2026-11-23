#!/usr/bin/env python3
"""Flashcard deck with an interactive quiz and per-card scores."""

import argparse
import io
import json
import os
import random
import re
import sys
import tempfile

DEFAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deck.json")


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {"cards": []}
    except (OSError, ValueError) as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    raw_cards = data.get("cards") if isinstance(data, dict) else None
    if not isinstance(raw_cards, list):
        sys.exit(f"error: {path} must contain an object with a 'cards' list")
    cards = []
    for item in raw_cards:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            continue
        try:
            correct = max(0, int(item.get("correct", 0)))
            wrong = max(0, int(item.get("wrong", 0)))
        except (TypeError, ValueError):
            correct = wrong = 0
        cards.append({"question": question, "answer": answer,
                      "correct": correct, "wrong": wrong})
    return {"cards": cards}


def save(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def normalize(text):
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,!?;:'\"")


def check_answer(given, expected):
    """Accept the answer or any pipe-separated alternative, loosely matched."""
    given = normalize(given)
    if not given:
        return False
    alternatives = {normalize(part) for part in str(expected).split("|")}
    alternatives.discard("")
    return given in alternatives


def add_card(data, question, answer):
    question = question.strip()
    answer = answer.strip()
    if not question or not answer:
        raise ValueError("question and answer must not be empty")
    if any(card["question"].lower() == question.lower() for card in data["cards"]):
        raise ValueError("that question is already in the deck")
    card = {"question": question, "answer": answer, "correct": 0, "wrong": 0}
    data["cards"].append(card)
    return card


def show_cards(data, out=sys.stdout):
    if not data["cards"]:
        out.write("deck is empty\n")
        return
    for index, card in enumerate(data["cards"], 1):
        out.write(
            f"{index:3d}. {card['question']}  ->  {card['answer']}"
            f"  (+{card['correct']}/-{card['wrong']})\n"
        )


def quiz(data, limit=None, shuffle=True, out=sys.stdout, ask=input):
    cards = list(data["cards"])
    if not cards:
        out.write("deck is empty; add a card first\n")
        return None
    if shuffle:
        random.shuffle(cards)
    if limit:
        cards = cards[:limit]
    score = 0
    answered = 0
    for index, card in enumerate(cards, 1):
        out.write(f"\n[{index}/{len(cards)}] {card['question']}\n> ")
        out.flush()
        try:
            given = ask()
        except EOFError:
            out.write("\nquiz ended early\n")
            break
        answered += 1
        if check_answer(given, card["answer"]):
            score += 1
            card["correct"] += 1
            out.write("correct\n")
        else:
            card["wrong"] += 1
            out.write(f"answer: {card['answer']}\n")
    if answered:
        out.write(f"\nScore: {score}/{answered} ({round(100 * score / answered)}%)\n")
    return score, answered


def positive(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def self_test():
    assert normalize("  Paris!  ") == "paris"
    assert normalize("New   York") == "new york"
    assert check_answer("paris", "Paris")
    assert check_answer("city of light", "paris|city of light")
    assert check_answer("  PARIS. ", "paris")
    assert not check_answer("london", "paris")
    assert not check_answer("", "paris")
    assert not check_answer("paris", "")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "deck.json")
        data = load(path)
        add_card(data, "Capital of France?", "Paris")
        add_card(data, "Capital of Japan?", "Tokyo")
        try:
            add_card(data, "capital of france?", "Lyon")
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate question accepted")
        save(path, data)
        loaded = load(path)
        assert len(loaded["cards"]) == 2

        answers = iter(["paris", "wrong"])
        buffer = io.StringIO()
        result = quiz(loaded, limit=2, shuffle=False, out=buffer, ask=lambda: next(answers))
        assert result == (1, 2)
        report = buffer.getvalue()
        assert "Score: 1/2 (50%)" in report
        assert "answer: Tokyo" in report
        assert loaded["cards"][0]["correct"] == 1
        assert loaded["cards"][1]["wrong"] == 1
        save(path, loaded)
        assert load(path)["cards"][1]["wrong"] == 1

        buffer = io.StringIO()
        show_cards(loaded, buffer)
        assert "+1/-0" in buffer.getvalue()
    print("self-test OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Keep a JSON flashcard deck and quiz yourself.",
        epilog="Answers may list alternatives separated by '|'. Matching is "
        "case-insensitive and ignores extra whitespace and punctuation. "
        "Exit codes: 0 success, 1 deck/storage error, 2 usage error.",
    )
    ap.add_argument("--file", default=DEFAULT_FILE, help="deck JSON file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks")
    sub = ap.add_subparsers(dest="command", metavar="command")

    add_parser = sub.add_parser("add", help="add a card")
    add_parser.add_argument("question")
    add_parser.add_argument("answer", help="answer, with '|' between alternatives")

    sub.add_parser("list", help="show cards and their score")

    quiz_parser = sub.add_parser("quiz", help="quiz yourself")
    quiz_parser.add_argument("--limit", type=positive, metavar="N",
                             help="maximum number of cards")
    quiz_parser.add_argument("--no-shuffle", action="store_true",
                             help="keep deck order")

    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.command:
        ap.print_help()
        return 2

    data = load(args.file)
    if args.command == "add":
        try:
            card = add_card(data, args.question, args.answer)
            save(args.file, data)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"added: {card['question']}")
    elif args.command == "list":
        show_cards(data)
    elif args.command == "quiz":
        result = quiz(data, args.limit, not args.no_shuffle)
        if result is None:
            return 1
        try:
            save(args.file, data)
        except OSError as exc:
            print(f"error: cannot save scores: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
