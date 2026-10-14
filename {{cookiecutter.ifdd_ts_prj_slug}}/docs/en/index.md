(ifdd-ts-index)=
# {{ cookiecutter.ifdd_ts_prj_name }} (ts)

The time series service of an IFDD node: VictoriaMetrics stores the series,
Grafana shows them next to the JSON-LD objects of the backend they belong
to. This chapter describes the instance `{{ cookiecutter.ifdd_ts_prj_slug }}`,
generated from the template `ifdd-de/ts`, from the point of view of the
people who set it up, run and secure it.

| | |
|---|---|
| Grafana | `https://{{ cookiecutter.ifdd_ts_host }}/` (default of `IFDD_TS_HOST`; routed by the proxy) |
| Images | `{{ cookiecutter.ifdd_ts_grafana_image }}`, `{{ cookiecutter.ifdd_ts_vm_image }}` (upstream, nothing is built) |
| Retention | `{{ cookiecutter.ifdd_ts_retention }}` |
| Backend, as Grafana reaches it | `{{ cookiecutter.ifdd_ts_be_url }}` |
| Realm, client | `{{ cookiecutter.ifdd_ts_oidc_issuer }}`, `{{ cookiecutter.ifdd_ts_oidc_client_id }}` |
| Networks | `{{ cookiecutter.ifdd_proxy_network }}` (Grafana), `{{ cookiecutter.ifdd_ts_ingest_network }}` (writers to VictoriaMetrics), an internal one between the two |

## What the instance contains

Two compose files, the Grafana configuration (`grafana/grafana.ini`, the
provisioned data sources and dashboards), the plugin lock file and the
script that fetches the plugin, `.env` and generated secrets, an example
loader and static tests. Nothing is downloaded at runtime: the Grafana
plugin is fetched once by `adm_01_plugins.sh` and mounted read-only; update
checks and telemetry are off.

Every series carries the full IRIs of its object, property and unit in the
labels `ifdd_id`, `ifdd_property` and `ifdd_unit` ({ref}`ifdd-ts-series`).
Two dashboards are provisioned in the folder IFDD:

- **IFDD series overview**: all objects that have series.
- **IFDD object**: the series of one object, the object as the backend
  returns it, and the property and unit of every series, each with a link to
  its IRI.

## Architecture

```{mermaid}
flowchart LR
  Writers[writers] -->|"{{ cookiecutter.ifdd_ts_ingest_network }}, port 8428"| VM[(VictoriaMetrics)]
  Users[users] --> Proxy[proxy: Traefik] --> Grafana
  Grafana -->|internal network| VM
  Grafana -->|Infinity, client credentials| BE[be]
  Grafana -->|login| KC[Keycloak]
```

| Who | Uses ts for |
|---|---|
| people | dashboards in Grafana, login through Keycloak |
| containers that write series | VictoriaMetrics on the ingest network |

| Grafana calls | For |
|---|---|
| Keycloak (`{{ cookiecutter.ifdd_ts_oidc_issuer }}`) | the login of people; a token for its service account |
| be (`{{ cookiecutter.ifdd_ts_be_url }}`) | the objects next to their series (Infinity plugin) |

## Chapters

```{toctree}
:maxdepth: 2

setup
build-release
operations
security
troubleshooting
reference
series
```

The values of the variables of this instance and how they relate to the
other services are listed in the chapter on the service instances
({ref}`ifdd-instances-ts`).
