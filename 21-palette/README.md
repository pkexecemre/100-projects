# 21-palette

A tiny, dependency-free color palette generator. Each shuffle produces five
colors from one of five harmony schemes (analogous, split, triad, mono, mixed).

## Features

- Random five-color palettes with pleasing hue and lightness relationships.
- Lock any swatch so it survives the next generation.
- Click a swatch or its hex code to copy that hex value to the clipboard.
- Press Space (outside a form field) or the New palette button to shuffle.
- Responsive layout: five columns, then two, then one on small screens.

## Usage

Open `index.html` directly in a browser, or serve the folder locally:

```sh
cd 21-palette
python3 -m http.server 8000
```

Then open the address the server prints. Copy uses the Clipboard API with a
hidden-textarea fallback for non-secure origins.

## Verification

```sh
python3 test.py
```

The smoke test checks that `index.html`, `style.css`, `app.js` and this README
exist, that required element ids and JS markers are present, and that no web
file references an external URL or calls `fetch()`. It handles `--help` and
rejects unknown arguments. Exit codes: 0 means all checks passed, 1 means a
file, marker or external-URL check failed, 2 means bad command-line usage.
