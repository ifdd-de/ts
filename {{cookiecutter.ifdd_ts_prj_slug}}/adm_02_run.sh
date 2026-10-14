#!/usr/bin/env bash
# Start (or restart) the service after checking what compose cannot check.
#
#   ./adm_02_run.sh production
#   ./adm_02_run.sh development
#
# Further arguments go to "docker compose up", e.g. --force-recreate.
set -euo pipefail
cd "$(dirname "$0")"

mode="${1:-}"
case "$mode" in
  production|development) shift ;;
  *) echo "usage: $0 production|development [docker compose up options]" >&2; exit 2 ;;
esac

fail() { echo "error: $*" >&2; exit 1; }

[[ -f .env ]] || fail ".env is missing - copy dotenv.dist to .env and fill it in"
for secret in grafana_admin_password grafana_secret_key oidc_client_secret; do
  [[ -f "secrets/$secret" ]] || fail "secrets/$secret is missing (see README)"
done
[[ -f grafana/plugins/yesoreyeram-infinity-datasource/plugin.json ]] \
  || fail "Grafana plugins are missing - run ./adm_01_plugins.sh first"

if [[ "$mode" == production ]]; then
  [[ -s secrets/oidc_client_secret ]] || fail "secrets/oidc_client_secret is empty"
  set -a; source .env; set +a
  [[ -n "${IFDD_TS_VM_DATA_DIR:-}" ]] || fail "IFDD_TS_VM_DATA_DIR is not set in .env"
fi

docker compose -f "docker-compose-$mode.yml" up -d "$@"
