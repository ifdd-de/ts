# {{ cookiecutter.ifdd_ts_prj_name }}

Time series service of IFDD: VictoriaMetrics stores the series, Grafana shows
them next to the JSON-LD objects of ifdd-be they belong to. Generated from
the template `ifdd-de/ts`; keep it current with `cruft update`. Both
containers are upstream images; nothing is built, and nothing is downloaded
at runtime.

## Quick start

```bash
docker network create {{ cookiecutter.ifdd_ts_ingest_network }}   # once
# generated as the user who owns the series, not as root (IFDD_TS_VM_UID)
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

## AI assistance

Some parts of the template `ifdd-de/ts` this instance was generated
from, in particular the tests, the test data and the documentation, were
developed or improved with the help of large language models (LLMs). All
changes were reviewed and released by the maintainer.

## License

BSD-3-Clause, see `LICENSE`.
