# 28-unit-convert-web

A live unit converter for length, weight and temperature. Pure HTML, CSS and
JavaScript with no dependencies or network access.

## Features

- Category tabs for length, weight and temperature.
- Length: meters, kilometers, centimeters, millimeters, miles, yards, feet,
  inches.
- Weight: kilograms, grams, milligrams, pounds, ounces, stone.
- Temperature: Celsius, Fahrenheit, Kelvin, with the usual offset formulas.
- Output updates on every keystroke; unit changes and category changes also
  recalculate immediately.
- Swap button exchanges the two units and carries the result across.
- Each category remembers its last used unit pair while the page is open.
- Formula line shows the converted equation; responsive single-column layout.

## Usage

Open `index.html`, or serve the folder:

```sh
cd 28-unit-convert-web
python3 -m http.server 8000
```

Type a value in the From field. Length and weight use factors relative to one
base unit; temperature converts through Celsius. Very small and very large
results switch to exponential notation.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, the inputs/selects/swap ids, tab markers,
conversion constants, and that no web file references an external URL or calls
`fetch()`. Exit codes: 0 pass, 1 failed check, 2 bad command-line usage.
