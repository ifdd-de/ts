(ifdd-ts-reference)=
# Reference

The variables of the template and their values in this instance are listed
in {ref}`ifdd-instances-ts`. This page lists what is not a template
variable.

## Layout

| Path | Purpose |
|---|---|
| `docker-compose-production.yml`, `docker-compose-development.yml` | the two modes |
| `dotenv.dist` → `.env` | values for compose; `.env` is not committed |
| `secrets/` | admin password, secret key (generated), Keycloak client secret (yours); not committed |
| `grafana/grafana.ini` | Grafana settings, environment-specific values via `$__env{}` |
| `grafana/provisioning/` | data sources and dashboard folders |
| `grafana/dashboards/ifdd/`, `grafana/dashboards/private/` | shipped dashboards, your own |
| `grafana/plugins.lock` | plugins with version, platform and SHA-256 |
| `adm_01_plugins.sh`, `adm_02_run.sh` | fetch the plugins; check and start |
| `examples/load_examples.py` | a day of example series |
| `tests/` | static checks of the configuration |

## Environment (`.env`)

| Variable | Default here | Meaning |
|---|---|---|
| `IFDD_TS_HOST` | `{{ cookiecutter.ifdd_ts_host }}` | host the proxy routes to Grafana |
| `IFDD_TS_VM_DATA_DIR` | `{{ cookiecutter.ifdd_ts_vm_data_dir }}` | directory of the series; required in production |
| `IFDD_TS_RETENTION` | `{{ cookiecutter.ifdd_ts_retention }}` | how long samples are kept (h, d, w, M, y) |
| `IFDD_TS_BE_URL` | `{{ cookiecutter.ifdd_ts_be_url }}` | the backend as reached from Grafana; no trailing slash |
| `IFDD_TS_OIDC_ISSUER` | `{{ cookiecutter.ifdd_ts_oidc_issuer }}` | realm URL |
| `IFDD_TS_OIDC_CLIENT_ID` | `{{ cookiecutter.ifdd_ts_oidc_client_id }}` | client for login and service account |
| `IFDD_TS_GRAFANA_DEV_PORT`, `IFDD_TS_VM_DEV_PORT` | `{{ cookiecutter.ifdd_ts_grafana_dev_port }}`, `{{ cookiecutter.ifdd_ts_vm_dev_port }}` | ports on 127.0.0.1 in development |

## Data sources

| Name | Type | Target |
|---|---|---|
| VictoriaMetrics (default) | Prometheus | `http://victoriametrics:8428` |
| IFDD backend | Infinity | `IFDD_TS_BE_URL`, OAuth2 client credentials in production, none in development |

Both are provisioned and not editable in the UI.

## Containers, ports and networks

| Container | Port | Networks |
|---|---|---|
| `victoriametrics` | 8428 (not published in production; 127.0.0.1:`IFDD_TS_VM_DEV_PORT` in development) | internal, `{{ cookiecutter.ifdd_ts_ingest_network }}` |
| `grafana` | 3000 (routed by the proxy; 127.0.0.1:`IFDD_TS_GRAFANA_DEV_PORT` in development) | internal, `{{ cookiecutter.ifdd_proxy_network }}` |

Router and service: `{{ cookiecutter.ifdd_ts_prj_slug }}`, rule
`Host(<IFDD_TS_HOST>)`, port 3000. Volume: `grafana-data`.
