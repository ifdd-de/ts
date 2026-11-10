"""After generation: create .env, the secrets that are unique per instance and
the data directory of VictoriaMetrics.

Existing files are left alone, so running the hook again (cruft update
renders into a temporary directory) never replaces a real value.

In .env, a variable whose whole value is <<host:uid>> or <<host:gid>> gets
the user or group id of the user running this hook. VictoriaMetrics runs as
that user in production, so everything below IFDD_TS_VM_DATA_DIR belongs to
that user and not to root. Refused for root.
"""

import os
import re
import secrets
import sys
from pathlib import Path

HOST_ID = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*=)<<host:(uid|gid)>>[ \t]*$", re.MULTILINE)

root = Path.cwd()


def fail(message: str) -> None:
    print(f"post_gen_project: {message}", file=sys.stderr)
    sys.exit(1)


def host_id(match: re.Match) -> str:
    return match.group(1) + str(os.getuid() if match.group(2) == "uid" else os.getgid())


env = root / ".env"
if not env.exists():
    text = (root / "dotenv.dist").read_text()
    if HOST_ID.search(text) and os.getuid() == 0:
        fail("refusing to run as root: VictoriaMetrics would write its data as root; "
             "generate the instance as the user who will own the data directory")
    env.write_text(HOST_ID.sub(host_id, text))

secret_dir = root / "secrets"
secret_dir.mkdir(exist_ok=True)
secret_dir.chmod(0o700)

generated = {
    "grafana_admin_password": secrets.token_urlsafe(24),
    "grafana_secret_key": secrets.token_urlsafe(32),
    # Filled in by the operator: the secret of the Keycloak client.
    "oidc_client_secret": "",
}
for name, value in generated.items():
    path = secret_dir / name
    if not path.exists():
        path.write_text(value)
    # Readable by the Grafana user inside the container (uid 472); the
    # directory itself is closed to other users on the host.
    path.chmod(0o644)

# The data directory of VictoriaMetrics (production). Compose does not create
# it (create_host_path: false): created by Docker it would belong to root.
data_dir = Path("{{ cookiecutter.ifdd_ts_vm_data_dir }}")
if not data_dir.is_absolute():
    data_dir = root / data_dir
try:
    data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
except OSError as error:
    print(f"post_gen_project: note: {data_dir} not created ({error.strerror}); create it as "
          "the user in IFDD_TS_VM_UID of .env before the first start", file=sys.stderr)
