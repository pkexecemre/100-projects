# 94-weather-mock

A deliberately fake weather report generator. The result is derived only from
the city name via SHA-256, so the same city always produces the same forecast
and **no network request is made**. Output is clearly labelled as fictional.

## Usage

```sh
./weather_mock.py Lisbon
./weather_mock.py --days 5 --units f "New York"
./weather_mock.py --json Oslo | python3 -m json.tool
./weather_mock.py --self-test
```

`--days` accepts 1-7. Temperatures are generated in Celsius and converted to
Fahrenheit (rounded) for display. The JSON payload includes `"mock": true`.

## Exit codes

- `0` success, including `--self-test`
- `1` missing city or bad flag (argparse)
- `2` invalid day count
