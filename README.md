# ifdd-de/ts

cookiecutter/cruft template for the time series service of IFDD:
VictoriaMetrics stores the series, Grafana shows them and links each series
to its JSON-LD object in ifdd-be through the full IRIs in the labels
`ifdd_id`, `ifdd_property` and `ifdd_unit`.

The generated instance runs upstream images only (no image of its own, no
`release.yml`) behind the IFDD proxy (`ifdd-de/proxy`) and needs no internet
at runtime. See the instance documentation (`docs/`) for setup and
operation.

## Generate an instance

```bash
cruft create --no-input --checkout <tag> \
  --config-file cookiecutter_all.yaml \
  --skip .env --skip secrets --skip grafana/dashboards/private \
  --output-dir ../instances https://github.com/ifdd-de/ts
```

The skip list keeps instance-owned files out of every later `cruft update`.

## Variables

| Variable | Default | Meaning |
|---|---|---|
| `ifdd_ts_prj_name`, `ifdd_ts_prj_slug` | `IFDD TS`, derived | name; the slug names the directory and the Traefik router |
| `ifdd_ts_host` | `ts` | host routed to Grafana (default for `IFDD_TS_HOST`) |
| `ifdd_ts_grafana_dev_port`, `ifdd_ts_vm_dev_port` | `8091`, `8092` | ports on 127.0.0.1 in development |
| `ifdd_ts_retention` | `10y` | how long VictoriaMetrics keeps samples (h, d, w, M, y) |
| `ifdd_ts_be_url` | `http://be` | ifdd-be as reached from Grafana; no trailing slash |
| `ifdd_ts_oidc_issuer` | `https://keycloak.example.org/realms/ifdd` | Keycloak realm URL; a placeholder, set it |
| `ifdd_ts_oidc_client_id` | `ifdd-ts` | Keycloak client for login and for reading ifdd-be |
| `ifdd_ts_roles_claim` | `realm_access.roles` | where the roles are in the token |
| `ifdd_ts_role_admin`, `_editor`, `_viewer` | `admin`, `readwrite`, `readonly` | Keycloak roles for Grafana Admin, Editor, Viewer |
| `ifdd_ts_grafana_image`, `ifdd_ts_vm_image` | `grafana/grafana:13.2.3`, `victoriametrics/victoria-metrics:v1.153.0` | images; for a mirror, the image in the internal registry |
| `ifdd_ts_grafana_memory_limit`, `ifdd_ts_vm_memory_limit` | `1G`, `2G` | memory limits; Grafana measured (instance documentation, operations), VictoriaMetrics a starting value |
| `ifdd_ts_ingest_network` | `ts-ingest` | Docker network on which writers reach VictoriaMetrics |
| `ifdd_proxy_network` | `proxy-net` | Docker network of the proxy |

Values that are defaults for `.env` (host, retention, URLs, client, ports)
can be changed later in `.env` without regenerating. The roles end up in
`grafana/grafana.ini`; change them with `cruft update --variables-to-update`.

The pre-generation hook rejects values that would render but not work.
Do not put `_copy_without_render` into `cookiecutter_all.yaml`.

## Layout

| Path | Purpose |
|---|---|
| `cookiecutter.json` | variables |
| `hooks/` | validation before; `.env` and generated secrets after generation |
| `{{cookiecutter.ifdd_ts_prj_slug}}/` | the instance, see its README |
| `tests/fixtures/` | `defaults`, `custom` (all variables changed) |
| `tests/check_docs.py`, `tests/docs/` | used by `template-test.yml`: the documentation of the instance, see below |

`.github`, `tests` and `grafana/dashboards` inside the instance are copied
without rendering: GitHub Actions expressions and Grafana's `{{label}}`
syntax collide with Jinja.

## Documentation of the instance (`docs/`)

Every instance carries its operating documentation as Sphinx sources in
MyST Markdown, in English (`docs/en`) and German (`docs/de`), with the same
files, labels and headings in both. The pages follow the work around the
service: `index` (purpose, architecture), `setup`, `build-release`,
`operations`, `security`, `troubleshooting`, `reference`, plus `series` (the
label contract for writers). cookiecutter fills in the values of the
instance. The instance README is only an entry point that links to them.

The pages have no `conf.py` of their own: they are meant to be copied into a
Sphinx project that documents all services. That project needs `myst_parser`
and `sphinxcontrib.mermaid`. Labels start with `ifdd-ts-`; references to
`ifdd-instances-ts` (the instance chapter of the meta repository) resolve
only there.

Rules for editing the pages in the template:

- change both languages in the same commit;
- no Jinja syntax in examples (`{{`, `{%`, `{#`); wrap such text in
  `{% raw %}`;
- the placeholder check of the CI greps the rendered instance for the text
  `cookiecutter` followed by a dot; do not write it literally.

`tests/check_docs.py` checks a rendered instance: same files, labels and
headings per level in both languages, every label with the prefix, every
reference to an own label resolvable, and a Sphinx build of each language
with `-W` (configuration `tests/docs/conf.py`, versions
`tests/docs/requirements.txt`).

## CI

| Workflow | Does |
|---|---|
| `template-test.yml` | renders both fixtures, checks for leftover placeholders, runs the static checks, checks and builds the documentation (`tests/check_docs.py`), validates both compose files, checks that the hook rejects bad values; smoke test: starts the development stack with the real images, loads the examples, checks plugin signature, dashboards and a query through Grafana |
| `template-update-test.yml` | generates from the latest tag, applies the current template with `cruft update`, fails on reject files, runs the static checks |

## Honesty notes

Documentation `docs/` (2026-10-13): rendered with cookiecutter 2.7.1 for
both fixtures and with the `cookiecutter_all.yaml` of the meta repository;
`tests/check_docs.py` passes for each (Sphinx 9.1.0, myst-parser 5.1.0,
sphinxcontrib-mermaid 2.1.1, on Python 3.13 and 3.14.6), the placeholder
check finds nothing and the instance tests pass. The workflow file passes
actionlint 1.7.12; the workflow itself has not run. Content: taken from the
previous instance README, `docs/series.md` (moved, English text unchanged
apart from the label), the compose files, `grafana.ini` and the provisioning
files. Also checked (2026-10-13): one Sphinx project per language with the
pages of all ten service templates (rendered with `cookiecutter_all.yaml`), the
instance chapter of the meta repository and ifdd-be-core with its OpenAPI
document builds with `-W` and no suppressed warnings, so every cross
reference resolves; the Mermaid diagrams of all services, and of the option
variants of the fixtures, render in headless Chromium 141.0.7390.37
(Playwright 1.56.0, Mermaid 11.12.1 served locally).

Checked with the real binaries (VictoriaMetrics v1.153.0, Grafana 13.2.3,
Infinity 4.0.0), a fake Keycloak and a fake ifdd-be: see the instance
README. The image tags and the containers themselves were not run at build
time (no Docker); the smoke test in CI covers them.

Unused bundled plugins (2026-10-08): the process list and memory figures
come from a running instance on arm64 (Grafana 13.2.3). `disable_plugins`
("comma-separated list of plugin identifiers to avoid loading (including
core plugins)") is taken from the Grafana configuration documentation
("latest"); its effect on 13.2.3 and the memory saved were not measured
here (Grafana could not be downloaded in the build environment). The new
instance test fails against the previous template. Measured afterwards on
the same instance: three processes instead of fifteen, `anon` 191 MB instead
of 209 MB. The RSS of the plugins was mostly mapped program files, not
process memory; the default limit became 1G for headroom.
