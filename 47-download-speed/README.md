# 47 - download-speed

Stream a URL to `/dev/null` while printing a progress line, then report the
average throughput measured with `time.monotonic()`. Payload is never written
to disk.

## Usage

```sh
python3 download_speed.py https://example.com/file.iso
python3 download_speed.py https://example.com/file.iso --quiet
python3 download_speed.py https://example.com/file.iso --json
python3 download_speed.py --self-test
```

Progress goes to stderr and shows bytes transferred, percentage when the
server sends `Content-Length`, and current rate. stdout carries only the final
summary (or JSON). Rates use decimal MB/s (1 MB = 1,000,000 bytes); sizes use
binary KiB/MiB. `--timeout` bounds each socket operation.

## JSON fields

`url`, `bytes`, `seconds`, `mb_per_second`, `status`, `content_type`,
`content_length` (null when the server does not advertise it).

## Exit codes

- `0` - download completed
- `2` - invalid URL/flag, DNS/connection failure, HTTP error, or timeout
- `130` - interrupted with Ctrl-C

## Notes

`--self-test` exercises the rate/size formatters and the copy loop with a
fake clock and in-memory stream; it performs no network I/O.
