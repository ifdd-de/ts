(ifdd-ts-setup)=
# Einrichtung

## Voraussetzungen

| Was | Warum |
|---|---|
| Docker mit Compose | Grafana und VictoriaMetrics laufen als Container |
| das externe Netz `{{ cookiecutter.ifdd_proxy_network }}` und eine laufende Proxy-Instanz | Traefik routet `IFDD_TS_HOST` zu Grafana |
| das externe Netz `{{ cookiecutter.ifdd_ts_ingest_network }}` | Schreiber erreichen dort VictoriaMetrics; einmal anlegen |
| der Client `{{ cookiecutter.ifdd_ts_oidc_client_id }}` im Realm | Anmeldung und Lesen des Backends; das Keycloak-Template legt ihn an |
| ein Verzeichnis für die Reihen (`IFDD_TS_VM_DATA_DIR`) | VictoriaMetrics hält dort seine Daten |
| einmal Internet oder die Plugin-Zips | `adm_01_plugins.sh` holt das Grafana-Plugin |

## Instanz anlegen

Üblicherweise legt das Meta-Repository alle Instanzen in einem Zug an
(`.adm_meta_01_all.sh`, Schritt `.adm_01_create_services.sh`), mit der
gemeinsamen Variablendatei `.cookiecutter_all.yaml`, und kopiert das
Client-Secret aus der Keycloak-Instanz nach `secrets/oidc_client_secret`. Von
Hand, im Verzeichnis der Instanzen, mit der Skip-Liste, die dieses Template
empfiehlt:

```bash
cruft create --no-input --config-file .cookiecutter_all.yaml \
  --skip .env --skip secrets --skip grafana/dashboards/private \
  https://github.com/ifdd-de/ts
```

Das Meta-Repository übergibt `--skip envs --skip .env`.

## Keycloak

1. Client `{{ cookiecutter.ifdd_ts_oidc_client_id }}` im Realm
   `IFDD_TS_OIDC_ISSUER`: vertraulich, Standard Flow (Anmeldung) und
   Service-Account (Grafana liest damit das Backend). Redirect-URI
   `https://<IFDD_TS_HOST>/login/generic_oauth`. Dem Service-Account die
   Leserechte im Backend geben, die er braucht, und nicht mehr.
2. Das Client-Secret in `secrets/oidc_client_secret` schreiben (kein
   Zeilenumbruch nötig); im Realm des Keycloak-Templates ist es
   `IFDD_KEYCLOAK_TS_CLIENT_SECRET`.
3. Realm-Rollen bestimmen die Grafana-Rolle; ein Benutzer ohne eine davon
   kommt nicht hinein:

   | Keycloak-Realm-Rolle | Grafana-Rolle |
   |---|---|
   | `{{ cookiecutter.ifdd_ts_role_admin }}` | Admin |
   | `{{ cookiecutter.ifdd_ts_role_editor }}` | Editor |
   | `{{ cookiecutter.ifdd_ts_role_viewer }}` | Viewer |

   Grafana sucht den Claim `{{ cookiecutter.ifdd_ts_roles_claim }}` im
   ID-Token, in der Userinfo-Antwort und im Access-Token. Einmal prüfen, dass
   eine Anmeldung jeder Rolle dort landet, wo sie soll.

## Konfiguration und Secrets

Der Post-Generation-Hook schreibt `.env` aus `dotenv.dist` und erzeugt das
Grafana-Admin-Passwort und den Secret Key in `secrets/`. In `.env` mindestens
`IFDD_TS_HOST` und `IFDD_TS_VM_DATA_DIR` setzen, dann `IFDD_TS_BE_URL`,
`IFDD_TS_OIDC_ISSUER` und `IFDD_TS_OIDC_CLIENT_ID` prüfen. Die Einträge stehen
in {ref}`ifdd-ts-reference`; die Template-Variablen in
{ref}`ifdd-instances-ts`.

## Plugins und erster Start

```bash
docker network create {{ cookiecutter.ifdd_ts_ingest_network }}   # einmal
./adm_01_plugins.sh
./adm_02_run.sh production
```

`adm_01_plugins.sh` holt die in `grafana/plugins.lock` genannten Plugins,
prüft ihre SHA-256 und entpackt sie nach `grafana/plugins/`. Ohne Internet
auf dem Host die dort genannten Zips nach `grafana/plugins-cache/` kopieren
und `./adm_01_plugins.sh --offline` ausführen. `adm_02_run.sh` prüft, was
compose nicht prüfen kann (`.env`, die Secrets, das Plugin, ein nicht leeres
Client-Secret und das Datenverzeichnis in Produktion), und ruft dann
`docker compose up -d` auf.

Das lokale Konto `admin` (Passwort in `secrets/grafana_admin_password`)
bleibt als Notzugang über das Anmeldeformular.

## Lokale Entwicklung

```bash
./adm_01_plugins.sh
./adm_02_run.sh development
python3 examples/load_examples.py
```

Grafana liegt unter `http://127.0.0.1:{{ cookiecutter.ifdd_ts_grafana_dev_port }}`
(Benutzer `admin`), VictoriaMetrics unter
`http://127.0.0.1:{{ cookiecutter.ifdd_ts_vm_dev_port }}`. Keycloak ist aus;
das Backend wird ohne Token abgefragt. Die Beispiel-IRIs liegen unter
example.org, daher bleibt das Objekt-Panel leer, bis Reihen für Objekte des
eigenen Backends geschrieben werden.
