#!/usr/bin/env python3
"""Get, set, list and dump INI files with configparser."""

import argparse
import configparser
import json
import os
import sys


def new_parser():
    parser = configparser.RawConfigParser(interpolation=None)
    parser.optionxform = str  # keep option case
    return parser


def load(path):
    if not os.path.isfile(path):
        raise ValueError(f"file not found: {path}")
    parser = new_parser()
    try:
        with open(path, encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise ValueError(f"cannot read {path}: {exc}")
    return parser


def section_values(parser, section):
    if section == parser.default_section:
        return dict(parser.defaults())
    if not parser.has_section(section):
        raise ValueError(f"no such section: {section}")
    return {key: parser.get(section, key) for key in parser.options(section)}


def all_values(parser):
    data = {}
    if parser.defaults():
        data[parser.default_section] = dict(parser.defaults())
    for section in parser.sections():
        data[section] = {key: parser.get(section, key) for key in parser.options(section)}
    return data


def save(parser, path):
    try:
        with open(path, "w", encoding="utf-8") as handle:
            parser.write(handle)
    except OSError as exc:
        raise ValueError(f"cannot write {path}: {exc}")


def self_test():
    parser = new_parser()
    parser.read_string("[DEFAULT]\ndefault = yes\n[server]\nhost = localhost\n"
                       "port = 8080\npath = 100%\n[demo]\nkey = value\n")
    assert parser.get("server", "port") == "8080"
    assert parser.get("server", "path") == "100%"  # no interpolation
    assert parser.get("server", "default") == "yes"  # defaults inherited
    assert section_values(parser, "demo") == {"default": "yes", "key": "value"}
    assert list(section_values(parser, "DEFAULT")) == ["default"]

    parser["server"]["port"] = "9090"
    parser.add_section("new")
    parser["new"]["x"] = "1"
    assert all_values(parser)["server"]["port"] == "9090"
    assert all_values(parser)["new"]["x"] == "1"
    assert all_values(parser)["new"]["default"] == "yes"

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test.ini")
        save(parser, path)
        again = load(path)
        assert again.get("server", "port") == "9090"
        assert again.get("new", "x") == "1"
        assert again.get("demo", "key") == "value"
        json.dumps(all_values(again))
        missing = os.path.join(tmp, "missing.ini")
        try:
            load(missing)
        except ValueError:
            pass
        else:
            raise AssertionError("missing file was accepted")
    print("self-test: all checks passed")


def build_parser():
    ap = argparse.ArgumentParser(
        description="Inspect and edit INI files.",
        epilog="Examples: ini_tool.py list app.ini | ini_tool.py set app.ini port 8080 "
               "--section server --create",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="list sections or keys")
    list_cmd.add_argument("file")
    list_cmd.add_argument("--section", help="list keys in this section")
    list_cmd.add_argument("--json", action="store_true")

    get_cmd = sub.add_parser("get", help="print one value")
    get_cmd.add_argument("file")
    get_cmd.add_argument("key")
    get_cmd.add_argument("--section", default="DEFAULT")
    get_cmd.add_argument("--json", action="store_true")

    set_cmd = sub.add_parser("set", help="set one value")
    set_cmd.add_argument("file")
    set_cmd.add_argument("key")
    set_cmd.add_argument("value")
    set_cmd.add_argument("--section", default="DEFAULT")
    set_cmd.add_argument("--create", action="store_true", help="create missing section")
    set_cmd.add_argument("-o", "--output", help="write to another file")

    dump_cmd = sub.add_parser("dump", help="print the whole file")
    dump_cmd.add_argument("file")
    dump_cmd.add_argument("--json", action="store_true")
    return ap


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv:
        self_test()
        return 0

    args = build_parser().parse_args(argv)
    try:
        if args.command == "set" and not os.path.exists(args.file):
            parser = new_parser()
        else:
            parser = load(args.file)
        if args.command == "list":
            if args.section:
                data = section_values(parser, args.section)
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    for key in data:
                        print(key)
            else:
                sections = list(parser.sections())
                if parser.defaults():
                    sections.insert(0, parser.default_section)
                if args.json:
                    print(json.dumps(sections, indent=2))
                else:
                    for section in sections:
                        print(section)
        elif args.command == "get":
            value = section_values(parser, args.section)[args.key]
            if args.json:
                print(json.dumps({"section": args.section, "key": args.key,
                                  "value": value}, indent=2))
            else:
                print(value)
        elif args.command == "set":
            section = args.section
            if section != parser.default_section and not parser.has_section(section):
                if not args.create:
                    raise ValueError(f"no such section: {section} (use --create)")
                parser.add_section(section)
            parser[section][args.key] = args.value
            save(parser, args.output or args.file)
        elif args.command == "dump":
            if args.json:
                print(json.dumps(all_values(parser), indent=2))
            else:
                parser.write(sys.stdout)
    except (KeyError, ValueError, configparser.Error) as exc:
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        print(f"error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
