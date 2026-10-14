(ifdd-ts-security)=
# Sicherheit

## VictoriaMetrics

VictoriaMetrics hat keine Authentifizierung. Es wird vom Proxy nicht geroutet
und veröffentlicht in Produktion keinen Port; erreichbar ist es im internen
Netz (Grafana) und im Ingest-Netz `{{ cookiecutter.ifdd_ts_ingest_network }}`.
Wer im Ingest-Netz hängt, kann Reihen schreiben und löschen: nur Container
anschließen, die Reihen schreiben.

## Anmeldung an Grafana

- Anmeldung über Keycloak (generisches OAuth) mit dem Client
  `{{ cookiecutter.ifdd_ts_oidc_client_id }}`; die Grafana-Rolle kommt aus den
  Realm-Rollen in `{{ cookiecutter.ifdd_ts_roles_claim }}` (streng: Ein
  Benutzer ohne eine der drei Rollen wird abgewiesen).
- Grafana legt einen Benutzer bei der ersten Keycloak-Anmeldung an
  (`allow_sign_up` im OAuth-Abschnitt, mit PKCE); Selbstregistrierung lokaler
  Benutzer ist aus. Das lokale Konto `admin`
  (`secrets/grafana_admin_password`) bleibt als Notzugang über das
  Anmeldeformular.
- Das Sitzungs-Cookie ist in Produktion als secure markiert.

## Zugriff auf das Backend

Die Datenquelle „IFDD backend“ (Plugin Infinity) liest das Backend mit den
Client Credentials von `{{ cookiecutter.ifdd_ts_oidc_client_id }}`, begrenzt
auf `IFDD_TS_BE_URL` (erlaubte Hosts). Editoren und Admins können
Infinity-Abfragen schreiben; sie erreichen das Backend mit den Rechten dieses
Service-Accounts. Ihm nur die Leserechte geben, die die Dashboards brauchen.

## Zertifikate

Mit einer internen CA muss Grafana (Keycloak-Anmeldung) und das Plugin
Infinity (Backend) der CA vertrauen. Das Template richtet das nicht ein.

## Secrets

`secrets/` enthält das Grafana-Admin-Passwort und den Secret Key (erzeugt)
und das Client-Secret (von Hand gesetzt); es ist von Git ausgenommen, steht
auf der empfohlenen Skip-Liste und geht als Docker-Secrets an Grafana. `.env`
enthält keine Secrets.

## Container

Beide Container laufen mit schreibgeschütztem Root-Dateisystem, `/tmp` als
tmpfs, ohne alle Capabilities und mit `no-new-privileges`. Zur Laufzeit wird
nichts heruntergeladen. Der Grafana-Router hängt keine Sicherheits-Header des
Proxys an.
