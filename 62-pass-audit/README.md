# 62 - pass-audit

Offline password strength audit. Reads candidates from a file or stdin, then
reports length, character-class coverage, a Shannon-style entropy estimate,
detected weak patterns, and a 0-100 score. Passwords are never echoed back.

## Usage

```sh
# one candidate per line, human-readable table
./pass_audit.py --file candidates.txt

# from stdin, machine-readable
printf 'hunter2\nXk9$mQ2!pL7#vR4\n' | ./pass_audit.py --json

# raise the policy minimum to 12 characters
./pass_audit.py --file candidates.txt --min-length 12
```

Pattern checks: common dictionary words, repeated blocks (`abcabcabc`), triple
repeated characters, sequential alphabet/number/keyboard runs, and missing
character classes. Ratings: weak (<30), fair (<55), good (<75), strong (>=75).

`--json` output:

```json
{"min_length": 8, "count": 2,
 "results": [{"length": 8, "class_count": 1, "entropy_bits": 37.6,
              "score": 14, "rating": "weak", "issues": ["..."]}]}
```

## Exit codes

| code | meaning |
|------|---------|
| 0 | audit completed |
| 2 | no candidates, unreadable file, or bad arguments |

Findings do not set a failure exit code; use the JSON scores in a pipeline.

## Self-test

```sh
./pass_audit.py --self-test
```

Checks weak/strong classification, repeat detection, JSON shape, redaction of
the input passwords, and the empty-input error path.
