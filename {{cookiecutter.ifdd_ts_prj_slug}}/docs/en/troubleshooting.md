(ifdd-ts-troubleshooting)=
# Troubleshooting

Start with `docker compose -f docker-compose-production.yml logs grafana`.

## Start

| Symptom | Cause | Remedy |
|---|---|---|
| `adm_02_run.sh`: `Grafana plugins are missing` | `adm_01_plugins.sh` has not run | run it (or `--offline` with the zips in `grafana/plugins-cache/`) |
| `adm_02_run.sh`: `secrets/... is missing` or `secrets/oidc_client_secret is empty` | the secrets were not created or the client secret not filled in | write the client secret into `secrets/oidc_client_secret` |
| `docker compose` stops with `set IFDD_TS_... in .env` | an entry is missing in `.env` | set it |
| a plugin checksum does not match | the zip in the cache is not the one in `plugins.lock` | delete it from `grafana/plugins-cache/` and fetch again |
| Grafana stays unhealthy | VictoriaMetrics is not healthy, or the configuration is wrong | logs of both containers |

## Login

| Symptom | Cause | Remedy |
|---|---|---|
| Keycloak answers `Invalid parameter: redirect_uri` | the client lacks `https://<IFDD_TS_HOST>/login/generic_oauth` | add it to the client |
| the login is refused after Keycloak | the user has none of the roles `{{ cookiecutter.ifdd_ts_role_admin }}`, `{{ cookiecutter.ifdd_ts_role_editor }}`, `{{ cookiecutter.ifdd_ts_role_viewer }}` | assign a realm role |
| certificate errors in the Grafana log at login | Grafana does not trust the CA of the realm's certificate | not wired up by the template; see {ref}`ifdd-ts-security` |

## Dashboards

| Symptom | Cause | Remedy |
|---|---|---|
| a series is stored but no dashboard shows it | it has no `ifdd_id` label | follow {ref}`ifdd-ts-series` |
| the object panel stays empty | the backend refused the service account (401/403), the object is not under `IFDD_TS_BE_URL`, or the IRIs are examples | check the client's rights and `IFDD_TS_BE_URL` |
| samples are rejected on ingestion | they are older than the retention | expected |
| a dashboard change in the UI cannot be saved | dashboards are provisioned from files | edit the JSON and restart Grafana |
