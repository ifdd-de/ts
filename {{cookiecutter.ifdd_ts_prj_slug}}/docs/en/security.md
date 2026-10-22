(ifdd-ts-security)=
# Security

## VictoriaMetrics

VictoriaMetrics has no authentication. It is not routed by the proxy and
publishes no port in production; it is reachable on the internal network
(Grafana) and on the ingest network `{{ cookiecutter.ifdd_ts_ingest_network }}`.
Whoever is on the ingest network can write and delete series: attach only
containers that write series.

Services that should write or read only some series use ts-api instead
(template `ifdd-de/ts-api`): it checks an access token, the roles and the
store of every request. That check does not reach Grafana or the ingest
network: everyone with a Grafana login sees the series of every store, and
containers on the ingest network bypass ts-api. Both are deliberate
(decision of 2026-10-21).

## Login to Grafana

- Login through Keycloak (generic OAuth) with the client
  `{{ cookiecutter.ifdd_ts_oidc_client_id }}`; the Grafana role comes from the
  realm roles in `{{ cookiecutter.ifdd_ts_roles_claim }}` (strict: a user
  without one of the three roles is refused).
- Grafana creates a user at the first Keycloak login (`allow_sign_up` of the
  OAuth section, with PKCE); sign-up of local users is off. The local
  `admin` account (`secrets/grafana_admin_password`) remains as break-glass
  access through the login form.
- The session cookie is marked secure in production.

## Access to the backend

The data source "IFDD backend" (Infinity plugin) reads the backend with the
client credentials of `{{ cookiecutter.ifdd_ts_oidc_client_id }}`, limited
to `IFDD_TS_BE_URL` (allowed hosts). Editors and admins can write Infinity
queries; they reach the backend with the rights of that service account.
Give it only the read rights the dashboards need.

## Certificates

With an internal CA, the CA must be trusted by Grafana (Keycloak login) and
by the Infinity plugin (backend). The template does not wire this up.

## Secrets

`secrets/` holds the Grafana admin password and secret key (generated) and
the client secret (set by hand); it is git-ignored, on the recommended skip
list, and handed to Grafana as Docker secrets. `.env` holds no secrets.

## Containers

Both containers run with a read-only root file system, `/tmp` as tmpfs, all
capabilities dropped and `no-new-privileges`. Nothing is downloaded at
runtime. The Grafana router attaches no security headers of the proxy.
