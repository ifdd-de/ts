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
  # Placeholders of dotenv.dist (<<host:uid>>) are no shell syntax.
  ! grep -q '=<<' .env \
    || fail ".env has placeholders of dotenv.dist (<<...>>): set IFDD_TS_VM_UID and IFDD_TS_VM_GID to the ids of the host user that owns the data (id -u, id -g)"
  set -a; source .env; set +a
  [[ -n "${IFDD_TS_VM_DATA_DIR:-}" ]] || fail "IFDD_TS_VM_DATA_DIR is not set in .env"
  # VictoriaMetrics runs as this host user; its data must belong to it.
  uid="${IFDD_TS_VM_UID:-}"
  gid="${IFDD_TS_VM_GID:-}"
  [[ "$uid" =~ ^[0-9]+$ && "$gid" =~ ^[0-9]+$ ]] \
    || fail "IFDD_TS_VM_UID and IFDD_TS_VM_GID must be set in .env to the ids of the host user that owns the data (see docs/en/operations.md)"
  [[ "$uid" != 0 ]] || fail "IFDD_TS_VM_UID is 0: VictoriaMetrics would write its data as root"
  data="$IFDD_TS_VM_DATA_DIR"
  [[ -d "$data" ]] || fail "$data is missing - create it as the user with uid $uid: mkdir -m 700 $data"
  not_owned=$(find "$data" ! -user "$uid" -print -quit 2>/dev/null || true)
  [[ -z "$not_owned" ]] \
    || fail "$not_owned does not belong to uid $uid - once: docker compose -f docker-compose-production.yml stop victoriametrics; sudo chown -R $uid:$gid $data"
fi

docker compose -f "docker-compose-$mode.yml" up -d "$@"
