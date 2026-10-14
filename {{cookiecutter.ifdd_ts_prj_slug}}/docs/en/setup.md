(ifdd-ts-setup)=
# Setup

## Prerequisites

| What | Why |
|---|---|
| Docker with Compose | Grafana and VictoriaMetrics run as containers |
| the external network `{{ cookiecutter.ifdd_proxy_network }}` and a running proxy instance | Traefik routes `IFDD_TS_HOST` to Grafana |
| the external network `{{ cookiecutter.ifdd_ts_ingest_network }}` | writers reach VictoriaMetrics there; create it once |
| the client `{{ cookiecutter.ifdd_ts_oidc_client_id }}` in the realm | login and reading the backend; the keycloak template creates it |
| a directory for the series (`IFDD_TS_VM_DATA_DIR`) | VictoriaMetrics keeps its data there |
| internet once, or the plugin zips | `adm_01_plugins.sh` fetches the Grafana plugin |

## Create the instance

Usually the meta repository creates every instance in one go
(`.adm_meta_01_all.sh`, step `.adm_01_create_services.sh`) with the shared
variable file `.cookiecutter_all.yaml`, and copies the client secret from
the keycloak instance into `secrets/oidc_client_secret`. By hand, from the
directory that holds the instances, with the skip list this template
recommends:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip .env --skip secrets --skip grafana/dashboards/private \
  https://github.com/ifdd-de/ts
```

The meta repository passes `--skip envs --skip .env`.

## Keycloak

1. Client `{{ cookiecutter.ifdd_ts_oidc_client_id }}` in the realm
   `IFDD_TS_OIDC_ISSUER`: confidential, standard flow (login) and service
   account (Grafana reads the backend with it). Redirect URI
   `https://<IFDD_TS_HOST>/login/generic_oauth`. Give the service account the
   read rights it needs in the backend, and nothing more.
2. Write the client secret into `secrets/oidc_client_secret` (no newline
   needed); in the realm of the keycloak template it is
   `IFDD_KEYCLOAK_TS_CLIENT_SECRET`.
3. Realm roles decide the Grafana role; a user with none of them is not let
   in:

   | Keycloak realm role | Grafana role |
   |---|---|
   | `{{ cookiecutter.ifdd_ts_role_admin }}` | Admin |
   | `{{ cookiecutter.ifdd_ts_role_editor }}` | Editor |
   | `{{ cookiecutter.ifdd_ts_role_viewer }}` | Viewer |

   Grafana looks for the claim `{{ cookiecutter.ifdd_ts_roles_claim }}` in the
   ID token, the userinfo response and the access token. Check once that a
   login of each role lands where it should.

## Configuration and secrets

The post-generation hook writes `.env` from `dotenv.dist` and generates the
Grafana admin password and secret key into `secrets/`. Set at least
`IFDD_TS_HOST` and `IFDD_TS_VM_DATA_DIR` in `.env`, then check
`IFDD_TS_BE_URL`, `IFDD_TS_OIDC_ISSUER` and `IFDD_TS_OIDC_CLIENT_ID`. The
entries are listed in {ref}`ifdd-ts-reference`; the template variables in
{ref}`ifdd-instances-ts`.

## Plugins and first start

```bash
docker network create {{ cookiecutter.ifdd_ts_ingest_network }}   # once
./adm_01_plugins.sh
./adm_02_run.sh production
```

`adm_01_plugins.sh` fetches the plugins named in `grafana/plugins.lock`,
checks their SHA-256 and unpacks them into `grafana/plugins/`. Without
internet on the host, copy the zips named there into `grafana/plugins-cache/`
and run `./adm_01_plugins.sh --offline`. `adm_02_run.sh` checks what compose
cannot (`.env`, the secrets, the plugin, a non-empty client secret and the
data directory in production) and then runs `docker compose up -d`.

The local `admin` account (password in `secrets/grafana_admin_password`)
stays as break-glass access through the login form.

## Local development

```bash
./adm_01_plugins.sh
./adm_02_run.sh development
python3 examples/load_examples.py
```

Grafana is at `http://127.0.0.1:{{ cookiecutter.ifdd_ts_grafana_dev_port }}`
(user `admin`), VictoriaMetrics at
`http://127.0.0.1:{{ cookiecutter.ifdd_ts_vm_dev_port }}`. Keycloak is off;
the backend is queried without a token. The example IRIs are under
example.org, so the object panel stays empty until you write series for
objects of your backend.
