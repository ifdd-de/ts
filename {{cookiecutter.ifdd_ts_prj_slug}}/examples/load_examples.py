"""Write a day of example time series into VictoriaMetrics.

    python3 examples/load_examples.py                     # development port
    python3 examples/load_examples.py --url http://victoriametrics:8428

The series follow the label contract in docs/en/series.md. The IRIs are
examples under example.org, not objects of a real ifdd-be; replace them with
@ids of your backend to see the link to the objects in Grafana.

Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
import urllib.request

OBJECTS = [
    "https://assets.example.org/products/transformer-0001",
    "https://assets.example.org/products/transformer-0002",
]

# metric name -> (property IRI, unit IRI, base value, daily amplitude)
PROPERTIES = {
    "active_power": (
        "https://type.example.org/v1/product/activePower",
        "https://unit.example.org/v1/unit/MegaW",
        120.0,
        40.0,
    ),
    "oil_temperature": (
        "https://type.example.org/v1/product/oilTemperature",
        "https://unit.example.org/v1/unit/DEG_C",
        55.0,
        8.0,
    ),
}


def series(seed: int, hours: int, step_s: int) -> list[dict]:
    """One JSON line per series in the VictoriaMetrics import format."""
    rng = random.Random(seed)
    end = int(time.time()) // step_s * step_s
    stamps = list(range(end - hours * 3600, end + 1, step_s))
    lines = []
    for number, object_id in enumerate(OBJECTS):
        for metric, (prop, unit, base, amplitude) in PROPERTIES.items():
            scale = 1.0 + 0.2 * number
            values = [
                round(
                    scale * base
                    + amplitude * math.sin(2 * math.pi * (t % 86400) / 86400)
                    + rng.gauss(0, amplitude / 20),
                    3,
                )
                for t in stamps
            ]
            lines.append(
                {
                    "metric": {
                        "__name__": metric,
                        "ifdd_id": object_id,
                        "ifdd_property": prop,
                        "ifdd_unit": unit,
                    },
                    "values": values,
                    "timestamps": [t * 1000 for t in stamps],
                }
            )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:{{ cookiecutter.ifdd_ts_vm_dev_port }}",
                        help="VictoriaMetrics base URL")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--step", type=int, default=60, help="seconds between samples")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    lines = series(args.seed, args.hours, args.step)
    body = "\n".join(json.dumps(line) for line in lines).encode()
    request = urllib.request.Request(
        args.url.rstrip("/") + "/api/v1/import", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()
    samples = sum(len(line["values"]) for line in lines)
    print(f"wrote {len(lines)} series, {samples} samples to {args.url}")


if __name__ == "__main__":
    main()
