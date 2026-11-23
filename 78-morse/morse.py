#!/usr/bin/env python3
"""Translate text to Morse code and back, with optional WAV output."""

import argparse
import math
import os
import re
import struct
import sys
import wave

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "$": "...-..-", "@": ".--.-.",
}
REVERSE = {code: char for char, code in MORSE.items()}


def encode(text):
    words = text.upper().split()
    if not words:
        raise ValueError("no text to encode")
    encoded = []
    for word in words:
        tokens = []
        for char in word:
            if char not in MORSE:
                raise ValueError(f"unsupported character {char!r}")
            tokens.append(MORSE[char])
        encoded.append(" ".join(tokens))
    return " / ".join(encoded)


def decode(code):
    text = code.strip()
    if not text:
        raise ValueError("empty Morse input")
    text = text.replace("|", "/").replace("\n", " / ")
    text = re.sub(r"\s{3,}", " / ", text)
    words = [part.strip() for part in text.split("/") if part.strip()]
    if not words:
        raise ValueError("empty Morse input")
    decoded = []
    for word in words:
        letters = []
        for token in word.split():
            if token not in REVERSE:
                raise ValueError(f"unknown Morse token {token!r}")
            letters.append(REVERSE[token])
        decoded.append("".join(letters))
    return " ".join(decoded)


def write_wav(path, code, wpm, frequency=700, rate=8000):
    """Render Morse timing (dot = 1.2/wpm seconds) as 16-bit mono PCM."""
    unit = 1.2 / wpm
    frames = bytearray()

    def silence(seconds):
        frames.extend(b"\x00\x00" * max(1, int(rate * seconds)))

    def tone(seconds):
        count = max(1, int(rate * seconds))
        for index in range(count):
            sample = int(12000 * math.sin(2 * math.pi * frequency * index / rate))
            frames.extend(struct.pack("<h", sample))

    for word_index, word in enumerate(code.split(" / ")):
        if word_index:
            silence(7 * unit)
        for letter_index, letter in enumerate(word.split()):
            if letter_index:
                silence(3 * unit)
            for symbol_index, symbol in enumerate(letter):
                if symbol_index:
                    silence(unit)
                tone(unit if symbol == "." else 3 * unit)

    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))
    return len(frames) // 2


def self_test():
    assert encode("SOS") == "... --- ..."
    assert encode("hello world") == ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
    assert encode("Hi!") == ".... .. -.-.--"
    assert decode("... --- ...") == "SOS"
    assert decode(".--. .-. .. ... -- / -.-. --- -.. .") == "PRISM CODE"
    assert decode(".--. .-. .. ... --|-.-. --- -.. .") == "PRISM CODE"
    assert decode(".... .. -.-.--") == "HI!"
    assert decode(encode("Test 42?")) == "TEST 42?"
    for bad in ("", "   "):
        try:
            encode(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("empty text was encoded")
    try:
        encode("caf\u00e9")
    except ValueError:
        pass
    else:
        raise AssertionError("non-ASCII character was accepted")
    try:
        decode(".-.---")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid token was accepted")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sos.wav")
        frames = write_wav(path, encode("SOS"), 12)
        assert frames > 0 and os.path.getsize(path) > 44
        with wave.open(path, "rb") as handle:
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 2
            assert handle.getframerate() == 8000
            assert handle.getnframes() == frames
    print("self-test: all checks passed")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    ap = argparse.ArgumentParser(
        description="Encode text to Morse code or decode Morse to text.",
        epilog="Separate letters with spaces and words with '/' or '|'. "
               "Examples: morse.py SOS | morse.py -d '... --- ...'",
    )
    ap.add_argument("text", nargs="?", help="text or Morse; stdin when omitted")
    ap.add_argument("-d", "--decode", action="store_true", help="decode Morse to text")
    ap.add_argument("-f", "--file", help="read input from a file")
    ap.add_argument("--wav", metavar="PATH", help="write encoded Morse as a WAV file")
    ap.add_argument("--wpm", type=float, default=12,
                    help="WAV speed in words per minute (5-40, default 12)")
    args = ap.parse_args(argv)

    if args.text is not None and args.file:
        print("error: give TEXT or --file, not both", file=sys.stderr)
        return 2
    if args.decode and args.wav:
        print("error: --wav is only available when encoding", file=sys.stderr)
        return 2
    if not (5 <= args.wpm <= 40):
        print("error: --wpm must be between 5 and 40", file=sys.stderr)
        return 2

    try:
        if args.file:
            with open(args.file, encoding="utf-8") as handle:
                source = handle.read()
        elif args.text is not None:
            source = args.text
        else:
            source = sys.stdin.read()
        if not source.strip():
            raise ValueError("no input")
        output = decode(source) if args.decode else encode(source)
        if args.wav and not args.decode:
            frames = write_wav(args.wav, output, args.wpm)
            print(f"wrote {args.wav} ({frames} frames at {args.wpm:g} wpm)")
        else:
            print(output)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
