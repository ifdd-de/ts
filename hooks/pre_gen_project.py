"""Validation before generation.

Rejects values that would render but not work, so a mistake shows up here
and not later as a container that does not start, a router Traefik drops or
a login that grants the wrong role.
"""

import re
import sys

values = {
    "ifdd_ts_prj_slug": "{{ cookiecutter.ifdd_ts_prj_slug }}",
    "ifdd_ts_host": "{{ cookiecutter.ifdd_ts_host }}",
    "ifdd_ts_grafana_dev_port": "{{ cookiecutter.ifdd_ts_grafana_dev_port }}",
    "ifdd_ts_vm_dev_port": "{{ cookiecutter.ifdd_ts_vm_dev_port }}",
    "ifdd_ts_retention": "{{ cookiecutter.ifdd_ts_retention }}",
    "ifdd_ts_be_url": "{{ cookiecutter.ifdd_ts_be_url }}",
    "ifdd_ts_oidc_issuer": "{{ cookiecutter.ifdd_ts_oidc_issuer }}",
    "ifdd_ts_oidc_client_id": "{{ cookiecutter.ifdd_ts_oidc_client_id }}",
    "ifdd_ts_roles_claim": "{{ cookiecutter.ifdd_ts_roles_claim }}",
    "ifdd_ts_role_admin": "{{ cookiecutter.ifdd_ts_role_admin }}",
    "ifdd_ts_role_editor": "{{ cookiecutter.ifdd_ts_role_editor }}",
    "ifdd_ts_role_viewer": "{{ cookiecutter.ifdd_ts_role_viewer }}",
    "ifdd_ts_grafana_image": "{{ cookiecutter.ifdd_ts_grafana_image }}",
    "ifdd_ts_vm_image": "{{ cookiecutter.ifdd_ts_vm_image }}",
    "ifdd_ts_grafana_memory_limit": "{{ cookiecutter.ifdd_ts_grafana_memory_limit }}",
    "ifdd_ts_vm_memory_limit": "{{ cookiecutter.ifdd_ts_vm_memory_limit }}",
    "ifdd_ts_ingest_network": "{{ cookiecutter.ifdd_ts_ingest_network }}",
    "ifdd_proxy_network": "{{ cookiecutter.ifdd_proxy_network }}",
}

SLUG = r"[a-z0-9][a-z0-9-]*"
HOST = r"[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?"
NAME = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
URL = r"https?://[^\s/]+(/[^\s]*)?"

rules = {
    "ifdd_ts_prj_slug": (SLUG, "lower-case letters, digits and '-', starting with a letter or digit"),
    "ifdd_ts_host": (HOST, "a host name without scheme or path"),
    "ifdd_ts_grafana_dev_port": (r"[0-9]{2,5}", "a port number"),
    "ifdd_ts_vm_dev_port": (r"[0-9]{2,5}", "a port number"),
    "ifdd_ts_retention": (r"[1-9][0-9]*[hdwMy]", "a number with a unit h, d, w, M or y, e.g. 10y"),
    "ifdd_ts_be_url": (URL, "an http(s) URL"),
    "ifdd_ts_oidc_issuer": (URL, "the http(s) URL of the Keycloak realm"),
    "ifdd_ts_oidc_client_id": (NAME, "a Keycloak client id"),
    "ifdd_ts_roles_claim": (r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*", "a dotted claim path, e.g. realm_access.roles"),
    "ifdd_ts_role_admin": (NAME, "a Keycloak role name"),
    "ifdd_ts_role_editor": (NAME, "a Keycloak role name"),
    "ifdd_ts_role_viewer": (NAME, "a Keycloak role name"),
    "ifdd_ts_grafana_image": (r"[^\s:]+(:[^\s:]+)?", "an image reference"),
    "ifdd_ts_vm_image": (r"[^\s:]+(:[^\s:]+)?", "an image reference"),
    "ifdd_ts_grafana_memory_limit": (r"[1-9][0-9]*[KMG]", "a size such as 1G"),
    "ifdd_ts_vm_memory_limit": (r"[1-9][0-9]*[KMG]", "a size such as 2G"),
    "ifdd_ts_ingest_network": (NAME, "a Docker network name"),
    "ifdd_proxy_network": (NAME, "a Docker network name"),
}

errors = []
for key, (pattern, meaning) in rules.items():
    if not re.fullmatch(pattern, values[key]):
        errors.append(f"{key}={values[key]!r}: expected {meaning}")

for key in ("ifdd_ts_grafana_dev_port", "ifdd_ts_vm_dev_port"):
    if values[key].isdigit() and not 1024 <= int(values[key]) <= 65535:
        errors.append(f"{key}={values[key]}: expected a port between 1024 and 65535")
if values["ifdd_ts_grafana_dev_port"] == values["ifdd_ts_vm_dev_port"]:
    errors.append("ifdd_ts_grafana_dev_port and ifdd_ts_vm_dev_port must differ")

for key in ("ifdd_ts_be_url", "ifdd_ts_oidc_issuer"):
    if values[key].endswith("/"):
        errors.append(f"{key}={values[key]!r}: no trailing slash")

roles = [values["ifdd_ts_role_admin"], values["ifdd_ts_role_editor"], values["ifdd_ts_role_viewer"]]
if len(set(roles)) != 3:
    errors.append("the three Keycloak roles (admin, editor, viewer) must be different")

retention = values["ifdd_ts_retention"]
if retention.endswith("h") and retention[:-1].isdigit() and int(retention[:-1]) < 24:
    errors.append("ifdd_ts_retention: VictoriaMetrics needs at least 24h")

if values["ifdd_ts_ingest_network"] == values["ifdd_proxy_network"]:
    errors.append("ifdd_ts_ingest_network must not be the proxy network: "
                  "VictoriaMetrics would be reachable by every service behind the proxy")

if errors:
    print("Invalid template values:", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    sys.exit(1)
