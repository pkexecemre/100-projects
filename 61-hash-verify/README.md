# 61 - hash-verify

Create a sha256 manifest for one or more files/directories, then verify that
the tree still matches. Manifest format is sha256sum-compatible
(`<digest>  <path>`), so `sha256sum -c` also works on it.

## Usage

```sh
# hash everything under ./etc-snapshot, paths relative to /srv
./hash_verify.py --create /tmp/etc.sha256 --root /srv /srv/etc-snapshot

# verify later, printing only problems
./hash_verify.py --check /tmp/etc.sha256 --root /srv

# show every OK line as well
./hash_verify.py --check /tmp/etc.sha256 --root /srv --verbose
```

Use `--exclude NAME` to skip directory basenames (default: `.git`). Symlinks are
not followed or hashed. Rerunning `--create` replaces the manifest atomically.

## Exit codes

| code | meaning |
|------|---------|
| 0 | every manifest entry verified |
| 1 | at least one file changed or is missing |
| 2 | bad arguments, unreadable manifest, or IO error |

## Self-test

```sh
./hash_verify.py --self-test
```

Creates a temporary tree, hashes it, verifies it, then tampers with and deletes
files to confirm the failure paths.
