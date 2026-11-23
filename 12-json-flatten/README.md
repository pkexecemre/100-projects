# json-flatten

Flatten nested JSON into a single-level object whose keys are dot-separated
paths, or rebuild the original structure with `--unflatten`. Standard library
only; reads a file or stdin.

## Usage

```sh
python3 json_flatten.py config.json
cat config.json | python3 json_flatten.py --unflatten --compact
python3 json_flatten.py data.json --sep /
```

Given `{"user": {"name": "Ada", "tags": ["math", "code"]}}` it prints:

```json
{
  "user.name": "Ada",
  "user.tags.0": "math",
  "user.tags.1": "code"
}
```

List indexes become numeric path segments. `--unflatten` reverses this and
infers lists from numeric segments, so most documents round-trip exactly.
Keys that consist only of digits are indistinguishable from list indexes and
become lists on unflattening. Empty objects and arrays are kept as leaves.
Paths that conflict (for example `a` and `a.b` with incompatible types) are
rejected.

Options: `--unflatten`, `--sep STRING` (default `.`), `--compact`.
Keys that contain the separator are not escaped, so choose a separator that
does not occur inside your key names. Exit status is `0` on success and `2` for
unreadable files, invalid JSON, invalid flattened input, or conflicting paths.
The separator must not be empty.

## Test

```sh
python3 json_flatten.py --self-test
```

The offline test checks flattening, unflattening, list reconstruction, empty
containers, scalar roots, and conflict detection.
