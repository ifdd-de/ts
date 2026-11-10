(ifdd-ts-troubleshooting)=
# Fehlersuche

Beginnen mit `docker compose -f docker-compose-production.yml logs grafana`.

## Start

| Symptom | Ursache | Abhilfe |
|---|---|---|
| `adm_02_run.sh`: `Grafana plugins are missing` | `adm_01_plugins.sh` ist nicht gelaufen | ausführen (oder `--offline` mit den Zips in `grafana/plugins-cache/`) |
| `adm_02_run.sh`: `secrets/... is missing` oder `secrets/oidc_client_secret is empty` | die Secrets wurden nicht angelegt oder das Client-Secret nicht eingetragen | das Client-Secret in `secrets/oidc_client_secret` schreiben |
| `docker compose` bricht mit `set IFDD_TS_... in .env` ab | ein Eintrag fehlt in `.env` | ihn setzen |
| eine Plugin-Prüfsumme passt nicht | das Zip im Cache ist nicht das aus `plugins.lock` | es aus `grafana/plugins-cache/` löschen und neu holen |
| Grafana bleibt unhealthy | VictoriaMetrics ist nicht healthy, oder die Konfiguration ist falsch | Logs beider Container |
| `cookiecutter` oder `cruft`: `refusing to run as root` | die Instanz wird als root erzeugt | als der Nutzer erzeugen, dem die Reihen gehören sollen |
| `adm_02_run.sh`: `... does not belong to uid ...` | die Daten wurden als root geschrieben (Instanz von vor `IFDD_TS_VM_UID`) oder von einem anderen Nutzer | das `chown` aus der Meldung, einmalig ({ref}`ifdd-ts-operations-data-owner`) |
| `adm_02_run.sh`: `... is missing`, oder `docker compose`: `bind source path does not exist` | `IFDD_TS_VM_DATA_DIR` fehlt; compose legt es nicht an | `mkdir -m 700` als der Nutzer aus `IFDD_TS_VM_UID` |
| VictoriaMetrics-Log: `FATAL: cannot stat "/storage/...": permission denied` | ohne `adm_02_run.sh` gestartet, mit Daten eines anderen Nutzers | wie oben: `chown` |

## Anmeldung

| Symptom | Ursache | Abhilfe |
|---|---|---|
| Keycloak antwortet `Invalid parameter: redirect_uri` | dem Client fehlt `https://<IFDD_TS_HOST>/login/generic_oauth` | am Client ergänzen |
| die Anmeldung wird nach Keycloak abgewiesen | der Benutzer hat keine der Rollen `{{ cookiecutter.ifdd_ts_role_admin }}`, `{{ cookiecutter.ifdd_ts_role_editor }}`, `{{ cookiecutter.ifdd_ts_role_viewer }}` | eine Realm-Rolle zuweisen |
| Zertifikatsfehler im Grafana-Log bei der Anmeldung | Grafana vertraut der CA des Realm-Zertifikats nicht, oder der Server schickt keine Zwischen-CA | die CA nach `certs/` legen, Grafana neu starten ({ref}`ifdd-ts-security-certificates`) |

## Dashboards

| Symptom | Ursache | Abhilfe |
|---|---|---|
| eine Reihe ist gespeichert, aber kein Dashboard zeigt sie | ihr fehlt das Label `ifdd_id` | {ref}`ifdd-ts-series` folgen |
| das Objekt-Panel bleibt leer | das Backend hat den Service-Account abgewiesen (401/403), das Objekt liegt nicht unter `IFDD_TS_BE_URL`, oder die IRIs sind Beispiele | Rechte des Clients und `IFDD_TS_BE_URL` prüfen |
| Werte werden bei der Annahme abgewiesen | sie sind älter als die Aufbewahrung | erwartet |
| eine Dashboard-Änderung in der Oberfläche lässt sich nicht speichern | Dashboards werden aus Dateien bereitgestellt | das JSON bearbeiten und Grafana neu starten |
