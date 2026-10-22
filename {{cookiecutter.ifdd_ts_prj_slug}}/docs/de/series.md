(ifdd-ts-series)=
# Reihenvertrag

Wie eine Zeitreihe auf ein Objekt von ifdd-be verweist. Alles in Grafana, was
Reihen und Objekte verbindet, beruht auf diesen Labels; Schreiber müssen sie
setzen.

## Labels

| Label | Pflicht | Wert |
|---|---|---|
| `ifdd_id` | ja | die vollständige `@id`-IRI des Objekts in ifdd-be, genau so, wie das Backend sie speichert |
| `ifdd_property` | ja | die vollständige IRI der Eigenschaft in einem Vokabular des Dienstes `type` |
| `ifdd_unit` | ja | die vollständige IRI der Einheit im Dienst `unit`; für dimensionslose Werte die IRI einer dimensionslosen Einheit |
| `ifdd_store` | nein | der Store, von ts-api an jedes darüber geschriebene Sample gesetzt (siehe unten) |

Vollständige IRIs, nie Präfix-Namen (CURIEs): Die Labels müssen ohne Kenntnis
eines JSON-LD-Kontexts vergleichbar sein. Eine Reihe ohne `ifdd_id` wird
gespeichert, aber kein Dashboard zeigt sie.

Der Metrikname (`__name__`) ist frei und nur für Menschen: einen kurzen
snake_case-Namen wie `active_power` wählen. Die Bedeutung steht in
`ifdd_property`, nicht im Namen. Weitere Labels sind erlaubt; ihre Werte
begrenzt halten (keine Zeitstempel, kein Freitext), denn jede verschiedene
Label-Menge ist eine neue Reihe.

## Wie Grafana die Labels nutzt

- **IFDD series overview** listet jede `ifdd_id`, die Reihen hat.
- **IFDD object** zeigt die Reihen eines Objekts und daneben das Objekt
  selbst, geholt von ifdd-be unter `IFDD_TS_BE_URL` + dem Pfad von
  `ifdd_id`. Das ist dieselbe Abbildung wie in ifdd-ct: Für
  `https://assets.example.org/products/t-1` fragt es `/products/t-1` an.
- Data Links an jeder Reihe öffnen `ifdd_id`, `ifdd_property` und
  `ifdd_unit` als URLs. Sie lösen sich nur dort auf, wo diese IRIs
  dereferenzierbar sind.

## Schreiben

Es gibt zwei Wege hinein:

- **ts-api** (Template `ifdd-de/ts-api`, Pfad `/tsapi` auf dem Host von
  Grafana): mit einem Access-Token des Realms, nur in den Stores, die die
  Rollen des Aufrufers öffnen, und mit Prüfung jedes Samples gegen das
  Vokabular seiner Eigenschaft. Sie nimmt genau die vier Labels oben an und
  setzt `ifdd_store`. Dienste, die keinen ungeprüften Zugang bekommen sollen,
  schreiben dort.
- **direkt**: Container im Ingest-Netz erreichen VictoriaMetrics unter
  `http://victoriametrics:8428` (in Produktion und in der Entwicklung), der
  Host unter `127.0.0.1` + dem Entwicklungsport. Dort wird
  nichts geprüft.

VictoriaMetrics nimmt mehrere Protokolle an; zwei wurden für dieses Template
gegen v1.153.0 geprüft:

JSON-Zeilen (`/api/v1/import`), wie `examples/load_examples.py` sie nutzt:

```json
{"metric": {"__name__": "active_power",
            "ifdd_id": "https://assets.example.org/products/transformer-0001",
            "ifdd_property": "https://type.example.org/v1/product/activePower",
            "ifdd_unit": "https://unit.example.org/v1/unit/MegaW"},
 "values": [118.2, 119.0], "timestamps": [1790000000000, 1790000060000]}
```

InfluxDB-Line-Protocol (`/write`); Tags werden zu Labels, der Metrikname ist
`<measurement>_<field>`, hier `breaker_state_value`:

```text
breaker_state,ifdd_id=https://assets.example.org/products/breaker-0003,ifdd_property=https://type.example.org/v1/product/switchState,ifdd_unit=https://unit.example.org/v1/unit/UNITLESS value=1
```

Im Line-Protocol müssen Kommas, Leerzeichen und `=` in einem Tag-Wert mit
einem Backslash maskiert werden. IRIs enthalten sie selten, aber vor dem
Verlassen darauf prüfen.

Werte, die älter als die Aufbewahrung (`IFDD_TS_RETENTION`) sind, werden
abgewiesen.

## Stores

Ein Store ist ein benannter Teil der Zeitreihen: das Label `ifdd_store`, z. B.
`temperature.ops.example.ifdd.de`. ts-api setzt es an jedes darüber
geschriebene Sample und liest nur Reihen des angefragten Stores; die Rollen
des Aufrufers entscheiden, welche Stores er nutzen darf. Grafana beachtet das
Label nicht: Beide Dashboards zeigen die Reihen aller Stores, Werte zweier
Stores (etwa Temperatur und Feuchte eines Objekts) erscheinen also
nebeneinander. Direkte Schreiber dürfen `ifdd_store` setzen oder weglassen;
ts-api sieht Reihen ohne das Label nicht.

## Gleiche Zeit zweimal

VictoriaMetrics läuft mit `-dedup.minScrapeInterval=1ms`. Von zwei Samples
einer Reihe mit derselben Zeit (auf die Millisekunde) behält es eines: den
größeren Wert, nicht den späteren (beobachtet mit v1.153.0). Dasselbe Sample
noch einmal zu schreiben, schadet also nicht, und ein Wert lässt sich durch
erneutes Schreiben nicht korrigieren. Ohne den Schalter behält VictoriaMetrics
beide Samples.
