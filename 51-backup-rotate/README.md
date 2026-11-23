# 51 - backup-rotate

Create a timestamped `tar.gz` backup of a directory, keep only the newest `N`
archives, and record every archive in a `manifest.json` file inside the
destination. Python 3 standard library only.

## Usage

```sh
./backup_rotate.py ~/work/project --dest /backups/project --keep 7
./backup_rotate.py ~/work/project --dest /backups/project --dry-run
./backup_rotate.py ~/work/project --dest /backups/project --keep 3 --prefix nightly
```

Archive names look like `project-20261123-211452.tar.gz`. If two backups start
in the same second a numeric suffix (`-1`, `-2`) is added. The archive is first
written to a temporary file and then renamed into place, so an interrupted run
never leaves a half-written archive under the final name.

Retention only considers archives that match the active prefix, and removes the
oldest names first. The manifest is rewritten atomically and pruned to archives
that still exist. If the destination is inside the source tree it is excluded
from the archive.

## Options

- `--dest DIR` (required) - destination for archives and `manifest.json`
- `--keep N` - archives retained, default 5, minimum 1
- `--prefix NAME` - archive prefix, default: source directory name
- `--dry-run` - print planned archive creation and removals, touch nothing
- `--self-test` - run built-in checks in a temporary directory

## Exit codes

- `0` - success (including a dry run and a no-op retention pass)
- `2` - bad arguments, missing source directory, unwritable destination

## Test

```sh
./backup_rotate.py --self-test
```

The self-test creates a temporary tree, checks archive contents, retention with
`--keep 1`, manifest bookkeeping, and that dry-run leaves the destination
unchanged.
