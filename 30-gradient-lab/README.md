# 30-gradient-lab

A two- or three-stop linear gradient generator with an angle slider and one
click to copy the CSS. Plain HTML, CSS and JavaScript, no dependencies.

## Features

- Native color pickers for three stops.
- Toggle the third stop off for a two-color gradient.
- Angle slider from 0 to 360 degrees, with a live numeric readout.
- Large live preview plus the exact generated CSS string.
- Copy button writes a complete `background: ...;` declaration, with a hidden
  textarea fallback when the Clipboard API is unavailable.
- Randomize picks a harmonious hue set and a 15-degree angle step.
- Responsive workspace stacks on smaller screens.

## Usage

Open `index.html`, or serve the folder:

```sh
cd 30-gradient-lab
python3 -m http.server 8000
```

Adjust colors and the angle, then press Copy CSS and paste it into a
stylesheet. Three stops are placed at 0, 50 and 100 percent; two stops at 0 and
100 percent.

## Verification

```sh
python3 test.py
```

The smoke test checks required files, color/angle/preview ids, copy and
linear-gradient markers, and that no web file references an external URL or
calls `fetch()`. Exit codes: 0 pass, 1 failed check, 2 bad command-line usage.
