(ifdd-ts-index)=
# {{ cookiecutter.ifdd_ts_prj_name }} (ts)

Der Zeitreihendienst eines IFDD-Knotens: VictoriaMetrics speichert die
Reihen, Grafana zeigt sie neben den JSON-LD-Objekten des Backends, zu denen
sie gehören. Dieses Kapitel beschreibt die Instanz
`{{ cookiecutter.ifdd_ts_prj_slug }}`, erzeugt aus dem Template `ifdd-de/ts`,
aus Sicht derer, die sie einrichten, betreiben und absichern.

| | |
|---|---|
| Grafana | `https://{{ cookiecutter.ifdd_ts_host }}/` (Vorgabe von `IFDD_TS_HOST`; vom Proxy geroutet) |
| Images | `{{ cookiecutter.ifdd_ts_grafana_image }}`, `{{ cookiecutter.ifdd_ts_vm_image }}` (Upstream, nichts wird gebaut) |
| Aufbewahrung | `{{ cookiecutter.ifdd_ts_retention }}` |
| Backend, wie Grafana es erreicht | `{{ cookiecutter.ifdd_ts_be_url }}` |
| Realm, Client | `{{ cookiecutter.ifdd_ts_oidc_issuer }}`, `{{ cookiecutter.ifdd_ts_oidc_client_id }}` |
| Netze | `{{ cookiecutter.ifdd_proxy_network }}` (Grafana), `{{ cookiecutter.ifdd_ts_ingest_network }}` (Schreiber zu VictoriaMetrics), ein internes zwischen beiden |

## Was die Instanz enthält

Zwei Compose-Dateien, die Grafana-Konfiguration (`grafana/grafana.ini`, die
bereitgestellten Datenquellen und Dashboards), die Lock-Datei der Plugins
und das Skript, das das Plugin holt, `.env` und erzeugte Secrets, ein
Beispiel-Lader und statische Tests. Zur Laufzeit wird nichts
heruntergeladen: Das Grafana-Plugin holt `adm_01_plugins.sh` einmal, es wird
nur lesend eingebunden; Update-Prüfungen und Telemetrie sind aus.

Jede Reihe trägt die vollständigen IRIs ihres Objekts, ihrer Eigenschaft und
ihrer Einheit in den Labels `ifdd_id`, `ifdd_property` und `ifdd_unit`
({ref}`ifdd-ts-series`). Im Ordner IFDD stehen zwei Dashboards bereit:

- **IFDD series overview**: alle Objekte, die Reihen haben.
- **IFDD object**: die Reihen eines Objekts, das Objekt, wie das Backend es
  liefert, und Eigenschaft und Einheit jeder Reihe, jeweils mit einem Link
  auf ihre IRI.

## Architektur

```{mermaid}
flowchart LR
  Writers[Schreiber] -->|"{{ cookiecutter.ifdd_ts_ingest_network }}, Port 8428"| VM[(VictoriaMetrics)]
  Users[Benutzer] --> Proxy[proxy: Traefik] --> Grafana
  Grafana -->|internes Netz| VM
  Grafana -->|Infinity, Client Credentials| BE[be]
  Grafana -->|Anmeldung| KC[Keycloak]
```

| Wer | Nutzt ts für |
|---|---|
| Menschen | Dashboards in Grafana, Anmeldung über Keycloak |
| Container, die Reihen schreiben | VictoriaMetrics im Ingest-Netz |

| Grafana ruft auf | Für |
|---|---|
| Keycloak (`{{ cookiecutter.ifdd_ts_oidc_issuer }}`) | die Anmeldung von Menschen; ein Token für seinen Service-Account |
| be (`{{ cookiecutter.ifdd_ts_be_url }}`) | die Objekte neben ihren Reihen (Plugin Infinity) |

## Kapitel

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

Die Werte der Variablen dieser Instanz und ihre Beziehungen zu den anderen
Diensten stehen im Kapitel über die Dienst-Instanzen
({ref}`ifdd-instances-ts`).
