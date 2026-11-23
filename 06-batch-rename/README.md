# 06-batch-rename

Rename files in one directory with a regular expression. The default is a dry
run: it prints each planned `old -> new` pair and changes nothing. `--apply`
performs the renames. Directories are ignored; only regular files are renamed.

## Usage

```sh
./batch_rename.py . 'IMG_(\d+)\.jpeg' 'photo-\1.jpg'          # preview
./batch_rename.py . 'IMG_(\d+)\.jpeg' 'photo-\1.jpg' --apply  # rename
./batch_rename.py ~/docs '^draft[ _]' 'final-' --apply
```

The pattern is matched against the file name only. `re.sub` semantics apply, so
every match is replaced and backreferences are supported. Before touching
anything the tool validates the whole batch and refuses to proceed if:

- a target name is empty, `.`, `..`, or contains a path separator;
- a target already exists in the directory;
- two source files would map to the same target.

A refusal exits 2 with no renames performed, so a partial batch is never left
behind by validation. Rename errors during `--apply` (for example a permission
problem) are reported per file and the remaining files are still attempted.

## Exit codes

| code | meaning |
|------|---------|
| 0 | dry run completed, or every rename succeeded |
| 1 | at least one rename failed during `--apply` |
| 2 | bad directory, bad regex, or a refused/colliding plan |

## Test

`./batch_rename.py --self-test` builds a temporary directory, checks the plan,
applies it, and asserts that both duplicate targets and existing targets are
refused. Files outside the temp directory are untouched.
