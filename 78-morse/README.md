# 78 - morse

Translate text to Morse code and Morse back to text. Includes letters, digits
and common punctuation, strict token validation, and optional WAV rendering
using only the standard library (`wave` + `struct`).

## Usage

```console
$ ./morse.py SOS
... --- ...
$ ./morse.py 'Hello, world!'
.... . .-.. .-.. --- --..-- / .-- --- .-. .-.. -.. -.-.--
$ ./morse.py -d '... --- ...'
SOS
$ ./morse.py -d '.... . .-.. .-.. --- / .-- --- .-. .-.. -..'
HELLO WORLD
$ ./morse.py SOS --wav sos.wav --wpm 15
wrote sos.wav (17280 frames at 15 wpm)
$ printf 'PING' | ./morse.py
.--. .. -. --.
```

Format:

- letters are separated by spaces, words by ` / ` (also accepts `|` or three
  or more spaces between words)
- encoding is case-insensitive and always outputs uppercase Morse
- decoding outputs uppercase letters; unknown tokens and unsupported characters
  are rejected with exit `1`

WAV output is 8 kHz, 16-bit mono PCM with a 700 Hz tone. Dot length is
`1.2 / wpm` seconds; letter gap is 3 dots and word gap 7 dots.

## Options

- `-d, --decode` - treat input as Morse code
- `-f, --file FILE` - read input from a file instead of TEXT or stdin
- `--wav PATH` - write the encoded Morse as audio (encode mode only)
- `--wpm N` - WAV speed, 5-40 (default 12)
- `--self-test` - encode/decode/WAV checks in a temp directory

## Exit codes

- `0` success
- `1` unsupported character, unknown Morse token, empty input, file/WAV error
- `2` conflicting arguments, `--wav` with `--decode`, invalid `--wpm`

## Self-test

```console
$ ./morse.py --self-test
self-test: all checks passed
```
