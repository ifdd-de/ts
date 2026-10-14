(ifdd-ts-series)=
# Reihenvertrag

Wie eine Zeitreihe auf ein Objekt von ifdd-be verweist. Alles in Grafana, was
Reihen und Objekte verbindet, beruht auf diesen Labels; Schreiber müssen sie
setzen.

## Labels

| Label | Pflicht | Wert |
|---|---|---|
| `ifdd_id` | ja | die vollständige `@id`-IRI des Objekts in ifdd-be, genau so, wie das Backend sie speichert |
| `ifdd_property` | ja | die vollständige IRI der Eigenschaft im Vokabular `schema` |
| `ifdd_unit` | ja | die vollständige IRI der Einheit im Dienst `unit`; für dimensionslose Werte die IRI der Einheit „eins“ |

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

Schreiber erreichen VictoriaMetrics unter `http://victoriametrics:8428` aus
einem Container im Ingest-Netz (Produktion) oder unter `127.0.0.1` + dem
Entwicklungsport. VictoriaMetrics nimmt mehrere Protokolle an; zwei wurden
für dieses Template gegen v1.153.0 geprüft:

JSON-Zeilen (`/api/v1/import`), wie `examples/load_examples.py` sie nutzt:

```json
{"metric": {"__name__": "active_power",
            "ifdd_id": "https://assets.example.org/products/transformer-0001",
            "ifdd_property": "https://schema.example.org/v1/product.jsonld#activePower",
            "ifdd_unit": "https://unit.example.org/v1/base/megawatt"},
 "values": [118.2, 119.0], "timestamps": [1790000000000, 1790000060000]}
```

InfluxDB-Line-Protocol (`/write`); Tags werden zu Labels, der Metrikname ist
`<measurement>_<field>`, hier `breaker_state_value`:

```text
breaker_state,ifdd_id=https://assets.example.org/products/breaker-0003,ifdd_property=https://schema.example.org/v1/product.jsonld#switchState,ifdd_unit=https://unit.example.org/v1/base/one value=1
```

Im Line-Protocol müssen Kommas, Leerzeichen und `=` in einem Tag-Wert mit
einem Backslash maskiert werden. IRIs enthalten sie selten, aber vor dem
Verlassen darauf prüfen.

Werte, die älter als die Aufbewahrung (`IFDD_TS_RETENTION`) sind, werden
abgewiesen.
