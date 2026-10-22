# Changelog

## [Unreleased]

- VictoriaMetrics runs with `-dedup.minScrapeInterval=1ms` in both modes: of
  two samples of one series with the same time it keeps one (the larger
  value), so that repeated writes, e.g. through ts-api, are harmless.
- In development VictoriaMetrics joins the ingest network too, so that
  writers such as ts-api reach it at `victoriametrics:8428` in both modes.
  The network must exist in development as well.
- Series contract (`docs/*/series.md`): `ifdd_property` names a property in a
  vocabulary of the type service (was "the `schema` vocabulary"), example
  IRIs in the form of the type and unit services, the optional label
  `ifdd_store`, the two ways in (ts-api, directly) and the deduplication.
  `examples/load_examples.py` uses the new example IRIs.
- Security page: what ts-api checks and what it does not reach (Grafana, the
  ingest network).

## [26.10.2] - 2026-10-14

- Documentation of the instance in `docs/en` and `docs/de` (Sphinx sources,
  MyST Markdown): index, setup, build and release, operations, security,
  troubleshooting, reference, series. `docs/series.md` moved to
  `docs/en/series.md` (with a German version `docs/de/series.md`); the links
  in the README and `examples/load_examples.py` follow. The instance README
  is now an entry point with a quick start, the links, the honesty notes and
  the license; its former sections moved into the documentation.
- `docs/_build/` in `.gitignore` of the instance.
- Template CI: `tests/check_docs.py` checks that both languages match and
  build without warnings (`tests/docs/conf.py`, `tests/docs/requirements.txt`).
- Grafana: `disable_plugins` in `grafana.ini` for the bundled data sources the
  instance does not use (elasticsearch, postgresql, pyroscope, influxdb,
  jaeger, loki, mssql, mysql, opentsdb, stackdriver, tempo, zipkin). Grafana
  13.2.3 started each as a process of its own (measured on arm64: 3 processes
  instead of 15, process memory 191 MB instead of 209 MB).
- Default `ifdd_ts_grafana_memory_limit` 1G (was 512M): Grafana's processes
  need about 200 MB idle, and the container kept reaching 512M (file cache
  pushed out 1941 times, no OOM kill). Existing instances keep their value
  in `.cruft.json`; change it with
  `cruft update --variables-to-update '{"ifdd_ts_grafana_memory_limit": "1G"}'`.

## [26.10.1] - 2026-10-01

First release of the template `ifdd-de/ts`.

- VictoriaMetrics (v1.153.0) and Grafana (13.2.3) as upstream images, read-only,
  without capabilities; VictoriaMetrics only on the internal and the ingest network.
- Series contract: labels `ifdd_id`, `ifdd_property`, `ifdd_unit` with full IRIs.
- Dashboards "IFDD series overview" and "IFDD object"; the object is read from
  ifdd-be with the Infinity plugin (4.0.0) and OAuth2 client credentials.
- Keycloak login with strict role mapping (admin, readwrite, readonly).
- No internet at runtime: plugin fetched and checksum-verified by
  `adm_01_plugins.sh`, also from an offline cache.
- Retention 10 years by default.
