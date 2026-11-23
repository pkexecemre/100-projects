# 24-md-preview

A live mini Markdown editor. The left pane holds source, the right pane renders
a safe preview on every keystroke. Plain HTML, CSS and JavaScript only.

## Supported syntax

- Headings with one, two or three `#` characters.
- Bold with double asterisks, italic with single asterisks or underscores.
- Inline code with backticks and fenced code blocks with triple backticks.
- Unordered lists (`-`, `*`, `+`) and ordered lists (`1.` style).
- Links in label-and-address form. Only http, https, mailto, anchor (`#`) and
  root-relative addresses become clickable; anything else renders as label text.
- Blockquotes with `>` and horizontal rules with three dashes.

HTML is escaped before formatting, and links use `target="_blank"` with
`rel="noopener noreferrer"`.

## Usage

Open `index.html` or serve the folder:

```sh
cd 24-md-preview
python3 -m http.server 8000
```

Tab inserts two spaces in the editor. The preview is intentionally small: no
nested lists, tables or images.

## Verification

```sh
python3 test.py
```

Checks required files, editor/preview ids, parser markers and that no web file
has an external URL or a `fetch()` call. Exit codes: 0 pass, 1 failed check,
2 bad command-line usage.
