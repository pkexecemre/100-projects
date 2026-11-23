# 55 - file-watch

Poll a file or a directory tree for changes and run a command when something is
added, modified, or removed. Changes are detected from `st_mtime_ns` and size,
so no inotify dependency is needed and network filesystems work too. Python 3
standard library only.

## Usage

```sh
# run a build once after the next change
./file_watch.py src --once -- make

# keep rebuilding, checking twice a second
./file_watch.py src --interval 0.5 -- make test

# watch a single file and run a script
./file_watch.py config.ini -- ./reload.sh
```

The command runs through `/bin/sh` by default, so pipes and redirection work.
Pass shell syntax as a single quoted argument:

```sh
./file_watch.py inbox --interval 2 -- 'echo changed >> ~/watch.log'
```

Use `--exec` to skip the shell and execute the argv directly, which is safer
when paths may contain shell metacharacters. Directory scans skip `.git` and
`__pycache__`. A change made while the command is running is detected on the
next poll, so notifications are not lost.

In continuous mode the exit code is `0` on `Ctrl-C`. With `--once` the tool
exits with the command's own status. Progress lines and change summaries are
printed; the command inherits the terminal for its own output.

## Options

- `--interval SECONDS` - scan period, default 1, may be fractional
- `--once` - run on the first detected change, then exit
- `--exec` - execute argv without a shell
- `--self-test` - run detection tests with a scripted snapshot sequence

Options must come before the `--` separator. Everything after `--` is the
command.

## Exit codes

- `0` - watcher stopped normally, or `--once` command succeeded
- command's status - `--once` mode when the command fails
- `2` - missing path or bad arguments

## Test

```sh
./file_watch.py --self-test
```

The test builds real snapshots in a temporary directory plus a scripted
modified snapshot, asserts change classification, that the command runs exactly
once, and that its exit status is propagated.
