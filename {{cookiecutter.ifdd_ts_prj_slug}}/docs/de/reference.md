(ifdd-ts-reference)=
# Referenz

Die Variablen des Templates und ihre Werte in dieser Instanz stehen in
{ref}`ifdd-instances-ts`. Diese Seite führt auf, was keine Template-Variable
ist.

## Aufbau

| Pfad | Zweck |
|---|---|
| `docker-compose-production.yml`, `docker-compose-development.yml` | die beiden Betriebsarten |
| `dotenv.dist` → `.env` | Werte für compose; `.env` wird nicht committet |
| `secrets/` | Admin-Passwort, Secret Key (erzeugt), Keycloak-Client-Secret (Ihres); nicht committet |
| `grafana/grafana.ini` | Grafana-Einstellungen, umgebungsabhängige Werte über `$__env{}` |
| `grafana/provisioning/` | Datenquellen und Dashboard-Ordner |
| `grafana/dashboards/ifdd/`, `grafana/dashboards/private/` | mitgelieferte Dashboards, eigene |
| `grafana/plugins.lock` | Plugins mit Version, Plattform und SHA-256 |
| `adm_01_plugins.sh`, `adm_02_run.sh` | Plugins holen; prüfen und starten |
| `examples/load_examples.py` | ein Tag Beispielreihen |
| `tests/` | statische Prüfungen der Konfiguration |

## Umgebung (`.env`)

| Variable | Vorgabe hier | Bedeutung |
|---|---|---|
| `IFDD_TS_HOST` | `{{ cookiecutter.ifdd_ts_host }}` | Host, den der Proxy zu Grafana routet |
| `IFDD_TS_VM_DATA_DIR` | `{{ cookiecutter.ifdd_ts_vm_data_dir }}` | Verzeichnis der Reihen; Pflicht in Produktion |
| `IFDD_TS_RETENTION` | `{{ cookiecutter.ifdd_ts_retention }}` | wie lange Werte bleiben (h, d, w, M, y) |
| `IFDD_TS_BE_URL` | `{{ cookiecutter.ifdd_ts_be_url }}` | das Backend, wie Grafana es erreicht; ohne abschließenden Schrägstrich |
| `IFDD_TS_OIDC_ISSUER` | `{{ cookiecutter.ifdd_ts_oidc_issuer }}` | Realm-URL |
| `IFDD_TS_OIDC_CLIENT_ID` | `{{ cookiecutter.ifdd_ts_oidc_client_id }}` | Client für Anmeldung und Service-Account |
| `IFDD_TS_GRAFANA_DEV_PORT`, `IFDD_TS_VM_DEV_PORT` | `{{ cookiecutter.ifdd_ts_grafana_dev_port }}`, `{{ cookiecutter.ifdd_ts_vm_dev_port }}` | Ports auf 127.0.0.1 in der Entwicklung |

## Datenquellen

| Name | Typ | Ziel |
|---|---|---|
| VictoriaMetrics (Vorgabe) | Prometheus | `http://victoriametrics:8428` |
| IFDD backend | Infinity | `IFDD_TS_BE_URL`, OAuth2 Client Credentials in Produktion, keine in der Entwicklung |

Beide werden bereitgestellt und sind in der Oberfläche nicht bearbeitbar.

## Container, Ports und Netze

| Container | Port | Netze |
|---|---|---|
| `victoriametrics` | 8428 (in Produktion nicht veröffentlicht; 127.0.0.1:`IFDD_TS_VM_DEV_PORT` in der Entwicklung) | intern, `{{ cookiecutter.ifdd_ts_ingest_network }}` |
| `grafana` | 3000 (vom Proxy geroutet; 127.0.0.1:`IFDD_TS_GRAFANA_DEV_PORT` in der Entwicklung) | intern, `{{ cookiecutter.ifdd_proxy_network }}` |

Router und Dienst: `{{ cookiecutter.ifdd_ts_prj_slug }}`, Regel
`Host(<IFDD_TS_HOST>)`, Port 3000. Volume: `grafana-data`.
