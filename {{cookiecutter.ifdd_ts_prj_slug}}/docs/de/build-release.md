(ifdd-ts-build-release)=
# Bauen und Freigeben

## Images

| Container | Image |
|---|---|
| `grafana` | `{{ cookiecutter.ifdd_ts_grafana_image }}` |
| `victoriametrics` | `{{ cookiecutter.ifdd_ts_vm_image }}` |

Die Instanz baut kein Image. Beide laufen mit schreibgeschütztem
Root-Dateisystem; Konfiguration, Provisioning-Dateien, Dashboards und das
Plugin sind nur lesend eingebunden. Für einen Mirror die Image-Variablen auf
die Images in der internen Registry setzen.

## Das Grafana-Plugin

`grafana/plugins.lock` nennt jedes Plugin mit Version, Plattform, SHA-256
und Download-URL; `adm_01_plugins.sh` holt und prüft sie. Die Plattform kommt
vom Host (`linux_amd64`, `linux_arm64`) oder aus `IFDD_TS_PLUGIN_PLATFORM`.

## Versionen und Updates

Die Image-Tags sind Template-Variablen; `plugins.lock` kommt aus dem
Template. Für ein Update von Grafana oder dem Plugin das Image oder
`plugins.lock` (Version, Prüfsumme, URL) im Template ändern, die
Grafana-Abhängigkeit des Plugins prüfen, dann die Instanz mit `cruft update`
aktualisieren und `adm_01_plugins.sh` erneut ausführen. Getestet mit Grafana
13.2.3, VictoriaMetrics v1.153.0 und Infinity 4.0.0.

## Dashboards

Dashboards sind Dateien. Die mitgelieferten liegen in
`grafana/dashboards/ifdd/` (von cruft aktualisiert), eigene in
`grafana/dashboards/private/` (von cruft übersprungen). Änderungen in der
Grafana-Oberfläche lassen sich nicht speichern: das JSON bearbeiten und neu
starten.

## Tests

```bash
pytest tests        # statische Prüfungen der Konfiguration
```

Die statischen Prüfungen decken die Offline- und Strenge-Einstellungen von
`grafana.ini` ab, die Datenquellen, die abgeschalteten mitgelieferten
Plugins, jedes Dashboard, die Plugin-Lock-Datei, die Härtung der Container,
das Fehlen veröffentlichter Ports in Produktion, dass `dotenv.dist` jede
Compose-Variable abdeckt und dass die Beispiele dem Reihenvertrag folgen.

## CI der Instanz

`.github/workflows/ci.yml` führt die statischen Prüfungen aus und validiert
beide Compose-Dateien.

## Freigabe

Es gibt keinen Release-Workflow, weil kein Image gebaut wird.
