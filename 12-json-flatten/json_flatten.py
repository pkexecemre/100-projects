#!/usr/bin/env python3
"""Flatten nested JSON into dot-separated paths, or rebuild it with --unflatten."""

import argparse
import json
import sys


def flatten(obj, prefix="", sep="."):
    """Flatten dicts/lists into {path: scalar}. Empty containers stay as leaves."""
    out = {}

    def walk(value, path):
        if isinstance(value, dict):
            if not value and path:
                out[path] = {}
            for key, child in value.items():
                child_path = "%s%s%s" % (path, sep, key) if path else str(key)
                walk(child, child_path)
        elif isinstance(value, list):
            if not value and path:
                out[path] = []
            for index, child in enumerate(value):
                child_path = "%s%s%d" % (path, sep, index) if path else str(index)
                walk(child, child_path)
        else:
            out[path] = value

    walk(obj, prefix)
    return out


def unflatten(flat, sep="."):
    """Rebuild nested JSON. Numeric path segments create list indexes."""
    if not isinstance(flat, dict):
        raise ValueError("flattened input must be a JSON object")
    if not flat:
        return {}
    if list(flat.keys()) == [""]:
        return flat[""]

    parts_list = [str(key).split(sep) for key in flat]
    if any(not part for parts in parts_list for part in parts):
        raise ValueError("path contains an empty segment")
    root_is_list = all(parts[0].isdigit() for parts in parts_list)
    root = [] if root_is_list else {}

    for parts, value in zip(parts_list, flat.values()):
        current = root
        for index, part in enumerate(parts):
            last = index == len(parts) - 1
            need_list = not last and parts[index + 1].isdigit()
            if isinstance(current, list):
                if not part.isdigit():
                    raise ValueError("conflicting path: %r expects a list index" % part)
                slot = int(part)
                while len(current) <= slot:
                    current.append(None)
                if last:
                    if current[slot] is not None:
                        raise ValueError("conflicting path at index %r" % part)
                    current[slot] = value
                    break
                if current[slot] is None:
                    current[slot] = [] if need_list else {}
                elif need_list != isinstance(current[slot], list):
                    raise ValueError("conflicting path at %r" % part)
                current = current[slot]
            else:
                if last:
                    if part in current:
                        raise ValueError("conflicting path at %r" % part)
                    current[part] = value
                    break
                if part not in current:
                    current[part] = [] if need_list else {}
                elif not isinstance(current[part], (dict, list)):
                    raise ValueError("conflicting path at %r" % part)
                elif need_list != isinstance(current[part], list):
                    raise ValueError("conflicting path at %r" % part)
                current = current[part]
    return root


def self_test():
    doc = {
        "user": {"name": "Ada", "tags": ["math", "code"],
                 "address": {"city": "London"}},
        "active": True,
        "empty": {},
    }
    flat = flatten(doc)
    assert flat["user.name"] == "Ada"
    assert flat["user.tags.1"] == "code"
    assert flat["user.address.city"] == "London"
    assert flat["active"] is True
    assert flat["empty"] == {}
    assert unflatten(flat) == doc
    assert flatten([{"x": 1}, [2, 3]]) == {"0.x": 1, "1.0": 2, "1.1": 3}
    assert unflatten({"0.x": 1, "1.0": 2, "1.1": 3}) == [{"x": 1}, [2, 3]]
    assert unflatten(flatten({"a": [[1], []]})) == {"a": [[1], []]}
    assert flatten(7) == {"": 7} and unflatten({"": 7}) == 7
    assert flatten({"a.b": 1}, sep="/") == {"a.b": 1}
    try:
        unflatten({"a": 1, "a.b": 2})
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting paths should fail")
    try:
        unflatten({"a.b": 1, "a": 2})
    except ValueError:
        pass
    else:
        raise AssertionError("reverse conflicting paths should fail")
    print("self-test: 15 checks passed")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flatten nested JSON to dot paths, or unflatten a flat object.")
    parser.add_argument("file", nargs="?", default="-",
                        help="JSON file, or - for stdin (default)")
    parser.add_argument("--unflatten", action="store_true",
                        help="rebuild nested JSON from flat keys")
    parser.add_argument("--sep", default=".", help="path separator (default '.')")
    parser.add_argument("--compact", action="store_true",
                        help="emit single-line JSON")
    parser.add_argument("--self-test", action="store_true",
                        help="run offline checks and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        return 0
    if not args.sep:
        parser.error("--sep must not be empty")

    try:
        if args.file == "-":
            text = sys.stdin.read()
        else:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        data = json.loads(text)
        result = (unflatten(data, args.sep) if args.unflatten
                  else flatten(data, sep=args.sep))
    except OSError as exc:
        print("json-flatten: error: %s" % exc, file=sys.stderr)
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print("json-flatten: error: %s" % exc, file=sys.stderr)
        return 2

    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
