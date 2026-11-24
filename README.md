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
| `ifdd_ts_grafana_image`, `ifdd_ts_vm_image` | `grafana/grafana:13.3.1`, `victoriametrics/victoria-metrics:v1.157.0` | images; for a mirror, the image in the internal registry |
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
and `sphinxcontrib.plantuml` (PlantUML with Java and Graphviz).
Labels start with `ifdd-ts-`; references to
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

The check runs PlantUML, so it needs Java and Graphviz.
`tests/docs/get_plantuml.sh` downloads the pinned PlantUML jar into the user
cache, checks its SHA-256 and prints its path:

```bash
export IFDD_PLANTUML_JAR="$(tests/docs/get_plantuml.sh)"
```

## CI

| Workflow | Does |
|---|---|
| `template-test.yml` | renders both fixtures, checks for leftover placeholders, runs the static checks, checks and builds the documentation (`tests/check_docs.py`), validates both compose files, checks that the hook rejects bad values; smoke test: starts the development stack with the real images, loads the examples, checks plugin signature, dashboards and a query through Grafana |
| `template-update-test.yml` | generates from the latest tag, applies the current template with `cruft update`, fails on reject files, runs the static checks |

## AI assistance

Some parts of this repository, in particular the tests, the test data and the
documentation, were developed or improved with the help of large language
models (LLMs). All changes were reviewed and released by the maintainer.
