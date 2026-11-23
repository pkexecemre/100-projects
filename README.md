# 100 Projects

A collection of 100 small, self-contained projects: CLI tools, web toys,
terminal games, converters and utilities. Every folder has its own README,
runnable code and a smoke test. Python 3 standard library only; web projects
are plain HTML/CSS/JS with no build step.

**100 projects** · built with parallel agents · no third-party dependencies.

## Index

| # | Folder | What it does |
|---|--------|--------------|
| 01 | [`01-disk-alert`](01-disk-alert/) | Report local filesystem usage and flag mounts that cross warning or critical thresholds. |
| 02 | [`02-port-check`](02-port-check/) | TCP connect scanner for one host. |
| 03 | [`03-dupfinder`](03-dupfinder/) | Find duplicate files. |
| 04 | [`04-logfilter`](04-logfilter/) | Grep-style line filter for logs. |
| 05 | [`05-envcheck`](05-envcheck/) | Sanity-check the shell environment. |
| 06 | [`06-batch-rename`](06-batch-rename/) | Rename files in one directory with a regular expression. |
| 07 | [`07-temp-sweep`](07-temp-sweep/) | Find old files in temporary directories and report how much space they use. |
| 08 | [`08-sysinfo-json`](08-sysinfo-json/) | Print a single JSON snapshot of system state, built from standard `/proc` files and `statvfs`. |
| 09 | [`09-cron-explain`](09-cron-explain/) | Translate a standard five-field cron expression into an English sentence, and optionally list the next N run times. |
| 10 | [`10-url-check`](10-url-check/) | Check one or more HTTP/HTTPS URLs with the standard library. |
| 11 | [`11-csv-stats`](11-csv-stats/) | Summarize every column in a CSV file. |
| 12 | [`12-json-flatten`](12-json-flatten/) | Flatten nested JSON into a single-level object whose keys are dot-separated paths, or rebuild the original structure with `--unflatten`. |
| 13 | [`13-md-toc`](13-md-toc/) | Generate a Markdown table of contents from the headings in a Markdown file. |
| 14 | [`14-word-freq`](14-word-freq/) | Count the most frequent words in a text file or stdin. |
| 15 | [`15-line-diff`](15-line-diff/) | Compare two text files line by line using a longest-common-subsequence table. |
| 16 | [`16-b64-tool`](16-b64-tool/) | Base64 encode or decode text, stdin, or file contents, with an optional URL-safe alphabet. |
| 17 | [`17-uuidgen`](17-uuidgen/) | Generate random UUID version 4 values in bulk using Python's `uuid` module. |
| 18 | [`18-passgen`](18-passgen/) | Generate secure random passwords with Python's `secrets` module. |
| 19 | [`19-slugify`](19-slugify/) | Turn arbitrary text into a URL-friendly slug. |
| 20 | [`20-ascii-table`](20-ascii-table/) | Read CSV or JSON rows and print them as an aligned ASCII table. |
| 21 | [`21-palette`](21-palette/) | A tiny, dependency-free color palette generator. |
| 22 | [`22-pomodoro`](22-pomodoro/) | A single-card Pomodoro timer built with plain HTML, CSS and JavaScript. |
| 23 | [`23-todo`](23-todo/) | A small todo list that persists in the browser using `localStorage`. |
| 24 | [`24-md-preview`](24-md-preview/) | A live mini Markdown editor. |
| 25 | [`25-bmi`](25-bmi/) | A body mass index calculator with metric and imperial input. |
| 26 | [`26-typing-test`](26-typing-test/) | A 30 second typing speed test with live words-per-minute and accuracy. |
| 27 | [`27-countdown`](27-countdown/) | A live event countdown with a date-time picker. |
| 28 | [`28-unit-convert-web`](28-unit-convert-web/) | A live unit converter for length, weight and temperature. |
| 29 | [`29-reaction-test`](29-reaction-test/) | A five-attempt reaction timer with a random wait. |
| 30 | [`30-gradient-lab`](30-gradient-lab/) | A two- or three-stop linear gradient generator with an angle slider and one click to copy the CSS. |
| 31 | [`31-snake`](31-snake/) | A curses snake game. |
| 32 | [`32-game2048`](32-game2048/) | A terminal implementation of 2048. |
| 33 | [`33-minesweeper`](33-minesweeper/) | A text-mode minesweeper with a configurable grid, mine counter, flood reveal, and flags. |
| 34 | [`34-hangman`](34-hangman/) | Classic hangman against a built-in list of 35 lowercase words. |
| 35 | [`35-connect4`](35-connect4/) | Local two-player Connect Four on a 6x7 board. |
| 36 | [`36-tic-tac-toe`](36-tic-tac-toe/) | Tic-tac-toe with two modes: play against a perfect minimax AI (default) or against a second player on the same terminal. |
| 37 | [`37-guess-number`](37-guess-number/) | Two-way number guessing with binary-search bookkeeping. |
| 38 | [`38-memory`](38-memory/) | A text-grid memory game. |
| 39 | [`39-rps`](39-rps/) | Best-of-N rock-paper-scissors against a random computer. |
| 40 | [`40-dice`](40-dice/) | A dice-notation parser, roller, and statistical simulator. |
| 41 | [`41-dns-lookup`](41-dns-lookup/) | Resolve A/AAAA records with `getaddrinfo` or do a reverse PTR lookup, with a hard timeout so a broken resolver cannot hang the terminal. |
| 42 | [`42-tcp-sweep`](42-tcp-sweep/) | Concurrent TCP connect checks. |
| 43 | [`43-http-headers`](43-http-headers/) | Request a URL with `urllib`, then print the final status line, the redirect chain, and every response header. |
| 44 | [`44-tls-expiry`](44-tls-expiry/) | Open a TLS connection, read the peer certificate, and report its subject, issuer, validity window, remaining days, and DNS SANs. |
| 45 | [`45-listeners`](45-listeners/) | Show listening TCP and UDP sockets. |
| 46 | [`46-whois-lite`](46-whois-lite/) | Query a WHOIS server over plain TCP port 43 and print the raw response. |
| 47 | [`47-download-speed`](47-download-speed/) | Stream a URL to `/dev/null` while printing a progress line, then report the average throughput measured with `time.monotonic()`. |
| 48 | [`48-ip-summary`](48-ip-summary/) | One-screen network summary: interface names, state, MTU, addresses, and default routes. |
| 49 | [`49-mtu-probe`](49-mtu-probe/) | Find the path MTU by sending single ICMP packets with the IPv4 Don't Fragment bit set and binary-searching the largest payload that gets… |
| 50 | [`50-selfsigned-cert`](50-selfsigned-cert/) | Wrapper around `openssl req -x509` that validates the common name and subject alternative names, generates a key and certificate, locks… |
| 51 | [`51-backup-rotate`](51-backup-rotate/) | Create a timestamped `tar.gz` backup of a directory, keep only the newest `N` archives, and record every archive in a `manifest.json`… |
| 52 | [`52-unit-watch`](52-unit-watch/) | Poll one or more systemd units with `systemctl is-active`, print the initial state of each unit, and log only state changes with… |
| 53 | [`53-cron-line`](53-cron-line/) | Validate a cron schedule and a command, then print a ready-to-paste crontab line together with comments explaining when it runs and the… |
| 54 | [`54-log-rotate`](54-log-rotate/) | Rotate a log file once it reaches a size limit. |
| 55 | [`55-file-watch`](55-file-watch/) | Poll a file or a directory tree for changes and run a command when something is added, modified, or removed. |
| 56 | [`56-retry`](56-retry/) | Run a command and retry it on failure with exponential backoff and optional jitter. |
| 57 | [`57-parallel-run`](57-parallel-run/) | Run shell commands listed in a file with a bounded number of concurrent workers, capture stdout, stderr and exit codes, then print a… |
| 58 | [`58-notify`](58-notify/) | Send a desktop notification through `notify-send`, with a plain terminal fallback when no desktop session or notification daemon is… |
| 59 | [`59-single-instance`](59-single-instance/) | Run a command while holding an exclusive kernel `flock`, so a second copy of the same job exits immediately instead of overlapping. |
| 60 | [`60-timeit`](60-timeit/) | Run a command and report wall-clock time plus user and system CPU time from `resource.getrusage(RUSAGE_CHILDREN)`, its exit code, and… |
| 61 | [`61-hash-verify`](61-hash-verify/) | Create a sha256 manifest for one or more files/directories, then verify that the tree still matches. |
| 62 | [`62-pass-audit`](62-pass-audit/) | Offline password strength audit. |
| 63 | [`63-suid-report`](63-suid-report/) | Walk one or more directory trees and report every regular file carrying the SUID (`4000`) or SGID (`2000`) bit. |
| 64 | [`64-world-writable`](64-world-writable/) | Find world-writable files and directories under one or more paths. |
| 65 | [`65-sshd-audit`](65-sshd-audit/) | Parse `sshd_config`, follow `Include` globs (relative includes resolve from the including file's directory, as OpenSSH does), and flag… |
| 66 | [`66-firewall-summary`](66-firewall-summary/) | One screen of local firewall state, covering four common Linux backends: |
| 67 | [`67-login-report`](67-login-report/) | Parse `last -F` output and count successful logins per user per calendar day. |
| 68 | [`68-port-map`](68-port-map/) | List listening TCP and UDP sockets and the process that owns each one. |
| 69 | [`69-integrity-baseline`](69-integrity-baseline/) | Snapshot a directory tree into a JSON baseline (sha256, size, mode, mtime per regular file), then compare later. |
| 70 | [`70-secret-scan`](70-secret-scan/) | Scan files for common credential shapes and print every hit with the secret redacted (first four and last four characters, middle starred). |
| 71 | [`71-unit-convert`](71-unit-convert/) | Convert between byte sizes (SI and IEC), durations, lengths and weights from one small, explicit unit registry. |
| 72 | [`72-timestamp`](72-timestamp/) | Convert between Unix epoch values, ISO 8601 timestamps and relative spans. |
| 73 | [`73-base-convert`](73-base-convert/) | Convert integers between binary, octal, decimal and hexadecimal with strict prefix handling and per-base digit validation. |
| 74 | [`74-color-convert`](74-color-convert/) | Convert colors between hexadecimal, `rgb()` and `hsl()`. |
| 75 | [`75-csv-json`](75-csv-json/) | Read CSV from a file or stdin and emit a JSON array of objects. |
| 76 | [`76-json-csv`](76-json-csv/) | Turn JSON into CSV. |
| 77 | [`77-ini-tool`](77-ini-tool/) | Read and edit INI files with Python's `configparser`. |
| 78 | [`78-morse`](78-morse/) | Translate text to Morse code and Morse back to text. |
| 79 | [`79-roman`](79-roman/) | Convert integers to Roman numerals and Roman numerals back to integers, with strict canonical validation and range checks (1-3999). |
| 80 | [`80-ip-math`](80-ip-math/) | CIDR arithmetic for IPv4 and IPv6 using Python's `ipaddress` module: network and broadcast addresses, netmask/wildcard, host ranges,… |
| 81 | [`81-clip-history`](81-clip-history/) | Keep a small, deduplicated history of clipboard text. |
| 82 | [`82-countdown-cli`](82-countdown-cli/) | A tiny countdown timer. |
| 83 | [`83-habit-log`](83-habit-log/) | A JSON-backed daily habit tracker. |
| 84 | [`84-note-search`](84-note-search/) | Recursive grep for a directory of notes. |
| 85 | [`85-bookmarks`](85-bookmarks/) | A small JSON bookmark manager. |
| 86 | [`86-expenses`](86-expenses/) | A CSV expense log with a monthly summary and category breakdown. |
| 87 | [`87-flashcards`](87-flashcards/) | A JSON flashcard deck with an interactive quiz. |
| 88 | [`88-reading-list`](88-reading-list/) | A JSON reading list with three statuses (`want`, `reading`, `read`) and a 0-5 star rating. |
| 89 | [`89-meal-plan`](89-meal-plan/) | A weekly meal planner stored as JSON. |
| 90 | [`90-workout-log`](90-workout-log/) | A JSON strength-training log. |
| 91 | [`91-blocktext`](91-blocktext/) | Render uppercase A-Z, digits 0-9 and spaces as big 5x7 block letters made of `#` characters. |
| 92 | [`92-quotes`](92-quotes/) | A tiny quote machine with the collection embedded in the script, so it works completely offline. |
| 93 | [`93-banner`](93-banner/) | Draw a rectangular ASCII banner around arbitrary text. |
| 94 | [`94-weather-mock`](94-weather-mock/) | A deliberately fake weather report generator. |
| 95 | [`95-coinflip`](95-coinflip/) | Flip an arbitrary number of fair coins and report the sequence, totals, percentages, the longest run of identical results, and a small… |
| 96 | [`96-lottery`](96-lottery/) | Pick unique lottery numbers from any inclusive numeric range. |
| 97 | [`97-maze`](97-maze/) | Generate a perfect maze (exactly one path between any two cells) using randomised depth-first search carving, then solve it with… |
| 98 | [`98-life`](98-life/) | Conway's Game of Life on a toroidal (wrap-around) grid, with built-in patterns: `blinker`, `toad`, `glider`, `block`, `pulsar`, and… |
| 99 | [`99-matrix`](99-matrix/) | A Matrix-style digital rain for the terminal. |
| 100 | [`100-sysfetch`](100-sysfetch/) | A compact neofetch-style system summary with an ASCII penguin logo. |

## Running

```sh
cd 01-disk-alert && python3 disk_alert.py --help
cd 21-palette && python3 -m http.server 8000   # open http://localhost:8000
```

Each project's README shows its exact command. Structural check:

```sh
python3 tools/check.py
```

## License

MIT — see [LICENSE](LICENSE).
