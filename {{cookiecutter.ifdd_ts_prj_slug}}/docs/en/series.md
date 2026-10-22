(ifdd-ts-series)=
# Series contract

How a time series refers to an object of ifdd-be. Everything in Grafana that
links series and objects relies on these labels; writers must set them.

## Labels

| Label | Required | Value |
|---|---|---|
| `ifdd_id` | yes | the full `@id` IRI of the object in ifdd-be, exactly as the backend stores it |
| `ifdd_property` | yes | the full IRI of the property in a vocabulary of the `type` service |
| `ifdd_unit` | yes | the full IRI of the unit in the `unit` service; for dimensionless values the IRI of a dimensionless unit |
| `ifdd_store` | no | the store, set by ts-api on every sample written through it (see below) |

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

There are two ways in:

- **ts-api** (template `ifdd-de/ts-api`, path `/tsapi` on the host of
  Grafana): with an access token of the realm, only in the stores the
  caller's roles open, and with every sample checked against the vocabulary
  of its property. It accepts exactly the four labels above and sets
  `ifdd_store`. Services that should not get unchecked access write there.
- **directly**: containers on the ingest network reach VictoriaMetrics at
  `http://victoriametrics:8428` (in production and in development), the
  host at `127.0.0.1` + the development port. Nothing is
  checked there.

VictoriaMetrics accepts several protocols; two were checked against v1.153.0
for this template:

JSON lines (`/api/v1/import`), as used by `examples/load_examples.py`:

```json
{"metric": {"__name__": "active_power",
            "ifdd_id": "https://assets.example.org/products/transformer-0001",
            "ifdd_property": "https://type.example.org/v1/product/activePower",
            "ifdd_unit": "https://unit.example.org/v1/unit/MegaW"},
 "values": [118.2, 119.0], "timestamps": [1790000000000, 1790000060000]}
```

InfluxDB line protocol (`/write`); tags become labels, the metric name is
`<measurement>_<field>`, here `breaker_state_value`:

```text
breaker_state,ifdd_id=https://assets.example.org/products/breaker-0003,ifdd_property=https://type.example.org/v1/product/switchState,ifdd_unit=https://unit.example.org/v1/unit/UNITLESS value=1
```

In line protocol, commas, spaces and `=` inside a tag value must be escaped
with a backslash. IRIs rarely contain them, but check before relying on it.

Samples older than the retention (`IFDD_TS_RETENTION`) are rejected.

## Stores

A store is a named part of the time series: the label `ifdd_store`, e.g.
`temperature.ops.example.ifdd.de`. ts-api sets it on every sample written
through it and reads only series with the store asked for; the roles of the
caller decide which stores it may use. Grafana ignores the label: both
dashboards show the series of every store, so values of two stores (say
temperature and humidity of one object) appear side by side. Direct writers
may set `ifdd_store` or leave it out; ts-api does not see series without it.

## Same time twice

VictoriaMetrics runs with `-dedup.minScrapeInterval=1ms`. Of two samples of
one series with the same time (to the millisecond) it keeps one: the larger
value, not the later one (observed with v1.153.0). Writing the same sample
again is therefore harmless, and a value cannot be corrected by writing it
again. Without the flag VictoriaMetrics keeps both samples.
