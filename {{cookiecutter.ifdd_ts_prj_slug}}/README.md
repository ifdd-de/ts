# {{ cookiecutter.ifdd_ts_prj_name }}

Time series service of IFDD: VictoriaMetrics stores the series, Grafana shows
them next to the JSON-LD objects of ifdd-be they belong to. Generated from
the template `ifdd-de/ts`; keep it current with `cruft update`. Both
containers are upstream images; nothing is built, and nothing is downloaded
at runtime.

## Quick start

```bash
docker network create {{ cookiecutter.ifdd_ts_ingest_network }}   # once
# .env: IFDD_TS_HOST, IFDD_TS_VM_DATA_DIR; secrets/oidc_client_secret from Keycloak
./adm_01_plugins.sh
./adm_02_run.sh production
```

Writers set the labels `ifdd_id`, `ifdd_property` and `ifdd_unit` with full
IRIs ([series contract](docs/en/series.md)).

## Documentation

Setup, build and release, operations, security, troubleshooting, reference
and the series contract of this instance:

- English: [docs/en/index.md](docs/en/index.md)
- Deutsch: [docs/de/index.md](docs/de/index.md)

The pages are Sphinx sources in MyST Markdown, meant to be copied into a
documentation project that covers all services; GitHub shows them as plain
Markdown.

## Honesty notes

Checked against the real binaries (VictoriaMetrics v1.153.0, Grafana 13.2.3,
Infinity 4.0.0) with a fake Keycloak and a fake ifdd-be: provisioning of
both data sources and dashboards, the plugin signature without internet,
`$__env{}`/`$__file{}`, the backend queries of all dashboard panels including
the OAuth2 token for ifdd-be, and the login with all role mappings (including
denial without a role and roles that are only in the access token).

Not checked here: the container images themselves (tags, read-only file
system, healthchecks) - covered by the CI smoke test; anything that only
runs in the browser (the regex of the hidden `object_path` variable,
transformations, data links); a real Keycloak.

## License

BSD-3-Clause, see `LICENSE`.
