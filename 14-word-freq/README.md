# word-freq

Count the most frequent words in a text file or stdin. Tokens are Unicode word
runs, case-folded, with a built-in English stopword list removed by default.
Only tokens containing at least one letter are counted, so punctuation and
bare numbers do not pollute the ranking.

## Usage

```sh
python3 word_freq.py article.txt
python3 word_freq.py article.txt --top 20 --json
cat article.txt | python3 word_freq.py --no-stopwords --min-length 4
python3 word_freq.py article.txt --stopwords my-stops.txt
```

Output is one `count  word` pair per line, right-aligned on the count. Options:
`--top N` (default 10), `--min-length N`, `--stopwords FILE` (adds words to the
built-in list), `--no-stopwords`, and `--json`.

Exit codes: `0` success, `1` when no words remain after filtering, `2` for
unreadable files or bad arguments.

## Test

```sh
python3 word_freq.py --self-test
```

The offline test checks counting, stopword removal, minimum length, case
folding, empty input, and custom stopword loading.
