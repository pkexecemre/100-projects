# 25-bmi

A body mass index calculator with metric and imperial input. Plain HTML, CSS
and JavaScript, no dependencies.

## Features

- Metric mode: height in centimetres, weight in kilograms.
- Imperial mode: height in inches, weight in pounds.
- Switching units converts any values already typed.
- Validates empty, non-numeric and out-of-range input with a clear message.
- Shows BMI to one decimal, the category (underweight, normal, overweight,
  obese), and the healthy weight range for the entered height.
- A colour-coded scale places a marker at the computed BMI.
- Responsive layout; result stacks on narrow screens.

## Usage

Open `index.html`, or serve the directory:

```sh
cd 25-bmi
python3 -m http.server 8000
```

Choose a unit system, enter height and weight, then press Calculate BMI. The
formula is weight in kilograms divided by height in metres squared; imperial
input is converted first.

## Verification

```sh
python3 test.py
```

The smoke test checks required files and ids, BMI threshold markers, and that
no web file references an external URL or calls `fetch()`. Exit codes: 0 pass,
1 failed check, 2 bad command-line usage.

BMI is a screening estimate, not a diagnosis or medical advice.
