# b64-tool

Base64 encode or decode text, stdin, or file contents, with an optional
URL-safe alphabet. Decoding is validated and tolerates missing padding and
whitespace/newlines.

## Usage

```sh
python3 b64_tool.py "hello world"
python3 b64_tool.py --decode "aGVsbG8gd29ybGQ="
printf 'binary' | python3 b64_tool.py --urlsafe --wrap 76
python3 b64_tool.py --file image.png
python3 b64_tool.py --decode --file encoded.txt -o image.png
```

When encoding, `--file` reads raw bytes, so binary files work. When decoding,
`--file` reads Base64 text. Decoded bytes are printed only if they are valid
UTF-8; use `-o PATH` to write arbitrary binary output. `-o PATH` writes the
result (decoded bytes, or encoded text) to a file. `--urlsafe` selects the
`-`/`_` alphabet when encoding (decoding accepts both alphabets). `--wrap N`
breaks encoded output every N columns.

Exit codes: `0` success, `2` unreadable file, invalid Base64, non-UTF-8 decoded
output without `-o`, or conflicting arguments.

## Test

```sh
python3 b64_tool.py --self-test
```

The offline test round-trips text and binary data, checks URL-safe output,
padding tolerance, wrapping, and rejection of malformed input.
