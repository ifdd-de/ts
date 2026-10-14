(ifdd-ts-series)=
# Series contract

How a time series refers to an object of ifdd-be. Everything in Grafana that
links series and objects relies on these labels; writers must set them.

## Labels

| Label | Required | Value |
|---|---|---|
| `ifdd_id` | yes | the full `@id` IRI of the object in ifdd-be, exactly as the backend stores it |
| `ifdd_property` | yes | the full IRI of the property in the `schema` vocabulary |
| `ifdd_unit` | yes | the full IRI of the unit in the `unit` service; for dimensionless values the IRI of the "one" unit |

Full IRIs, never prefixed names (CURIEs): the labels must be comparable
without knowing a JSON-LD context. A series without `ifdd_id` is stored, but
neither dashboard shows it.

The metric name (`__name__`) is free and only for people: choose a short
snake_case name such as `active_power`. The meaning is in `ifdd_property`,
not in the name. Further labels are allowed; keep their values bounded (no
timestamps, no free text), because every distinct label set is a new series.

## How Grafana uses the labels

- **IFDD series overview** lists every `ifdd_id` that has series.
- **IFDD object** shows the series of one object and, next to them, the
  object itself, fetched from ifdd-be at `IFDD_TS_BE_URL` + the path of
  `ifdd_id`. This is the same mapping as in ifdd-ct: for
  `https://assets.example.org/products/t-1` it requests `/products/t-1`.
- Data links on every series open `ifdd_id`, `ifdd_property` and `ifdd_unit`
  as URLs. They only resolve where these IRIs are dereferenceable.

## Writing

Writers reach VictoriaMetrics at `http://victoriametrics:8428` from a
container on the ingest network (production) or at `127.0.0.1` + the
development port. VictoriaMetrics accepts several protocols; two were
checked against v1.153.0 for this template:

JSON lines (`/api/v1/import`), as used by `examples/load_examples.py`:

```json
{"metric": {"__name__": "active_power",
            "ifdd_id": "https://assets.example.org/products/transformer-0001",
            "ifdd_property": "https://schema.example.org/v1/product.jsonld#activePower",
            "ifdd_unit": "https://unit.example.org/v1/base/megawatt"},
 "values": [118.2, 119.0], "timestamps": [1790000000000, 1790000060000]}
```

InfluxDB line protocol (`/write`); tags become labels, the metric name is
`<measurement>_<field>`, here `breaker_state_value`:

```text
breaker_state,ifdd_id=https://assets.example.org/products/breaker-0003,ifdd_property=https://schema.example.org/v1/product.jsonld#switchState,ifdd_unit=https://unit.example.org/v1/base/one value=1
```

In line protocol, commas, spaces and `=` inside a tag value must be escaped
with a backslash. IRIs rarely contain them, but check before relying on it.

Samples older than the retention (`IFDD_TS_RETENTION`) are rejected.
