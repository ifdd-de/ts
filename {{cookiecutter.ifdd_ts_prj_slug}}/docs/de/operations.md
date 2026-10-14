(ifdd-ts-operations)=
# Betrieb

## Starten, Stoppen, Reihenfolge

```bash
./adm_02_run.sh production                     # Prüfungen, dann docker compose up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down
```

Grafana wartet auf ein gesundes VictoriaMetrics. Für die Anmeldung und die
Objekt-Panels braucht es Keycloak und das Backend; es also nach diesen
starten (`.adm_03_up_services.sh` des Meta-Repositorys tut das).

## Healthchecks

| Container | Prüfung | Intervall |
|---|---|---|
| `victoriametrics` | `wget` auf `http://127.0.0.1:8428/health` | 10 s, Timeout 5 s, 3 Versuche, Startphase 10 s |
| `grafana` | `curl` auf `http://127.0.0.1:3000/api/health` | 10 s, Timeout 5 s, 3 Versuche, Startphase 30 s |

Beide starten mit `unless-stopped` neu.

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f grafana victoriametrics
```

## Daten und Sicherung

Alle Reihen liegen in `IFDD_TS_VM_DATA_DIR`. Konsistent sichern mit einem
Snapshot (`/snapshot/create` von VictoriaMetrics) oder dem eigenen Werkzeug
vmbackup; eine einfache Kopie des laufenden Verzeichnisses ist nicht
konsistent. Grafana hält in seinem Volume `grafana-data` nur Benutzer und
Sitzungen. `.env` und `secrets/` ebenfalls aufbewahren.

```{note}
Nicht getestet: Sicherung und Wiederherstellung der Reihen.
```

## Aufbewahrung

`IFDD_TS_RETENTION` (hier `{{ cookiecutter.ifdd_ts_retention }}`). Ältere
Werte werden gelöscht und bei der Annahme abgewiesen. Ein kleinerer Wert
löscht Daten.

## Ressourcen

| Container | Speichergrenze |
|---|---|
| `grafana` | `{{ cookiecutter.ifdd_ts_grafana_memory_limit }}` |
| `victoriametrics` | `{{ cookiecutter.ifdd_ts_vm_memory_limit }}` (ein Startwert) |

Grafana 13 startet jede mitgelieferte Datenquelle als eigenen Prozess;
`grafana.ini` schaltet die ungenutzten ab (`disable_plugins`). Gemessen auf
arm64 (Grafana 13.2.3, im Leerlauf): mit allen mitgelieferten Plugins 15
Prozesse und 209 MB anonymer Speicher, mit `disable_plugins` 3 Prozesse und
191 MB. Der Datei-Cache füllt, was die Grenze übrig lässt, und gibt es bei
Bedarf zurück. Im Container prüfen mit
`cat /sys/fs/cgroup/memory.stat /sys/fs/cgroup/memory.events`: `anon` sind
die Prozesse; `max` zählt, wie oft die Grenze erreicht wurde, `oom_kill` muss
0 bleiben.

## Änderungen übernehmen

Datenquellen, Dashboards und `grafana.ini` werden beim Start gelesen: nach
einer Änderung
`docker compose -f docker-compose-production.yml restart grafana`.
Änderungen in der Grafana-Oberfläche an bereitgestellten Dashboards oder
Datenquellen lassen sich nicht speichern.

## Aktualisieren

Template-Updates kommen mit `cruft update`; `.env`, `secrets` und
`grafana/dashboards/private` stehen auf der Skip-Liste. Nach einem Update von
`plugins.lock` `adm_01_plugins.sh` erneut ausführen.
