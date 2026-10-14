"""After generation: create .env and the secrets that are unique per instance.

Existing files are left alone, so running the hook again (cruft update
renders into a temporary directory) never replaces a real value.
"""

import secrets
import shutil
from pathlib import Path

root = Path.cwd()

env = root / ".env"
if not env.exists():
    shutil.copyfile(root / "dotenv.dist", env)

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
