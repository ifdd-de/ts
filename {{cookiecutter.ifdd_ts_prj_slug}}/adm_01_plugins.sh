#!/usr/bin/env bash
# Fetch the Grafana plugins listed in grafana/plugins.lock, verify their
# checksums and unpack them into grafana/plugins/, which Grafana mounts
# read-only. Grafana itself never downloads anything.
#
#   ./adm_01_plugins.sh             download what is missing from the cache
#   ./adm_01_plugins.sh --offline   use only zips already in the cache
#
# Without internet on the host: copy the zips named in plugins.lock into
# grafana/plugins-cache/ and run with --offline.
#
# IFDD_TS_PLUGIN_PLATFORM overrides the platform (linux_amd64, linux_arm64),
# which is otherwise taken from this host.
set -euo pipefail
cd "$(dirname "$0")"

LOCK=grafana/plugins.lock
CACHE=grafana/plugins-cache
TARGET=grafana/plugins
OFFLINE=false
[[ "${1:-}" == "--offline" ]] && OFFLINE=true

case "${IFDD_TS_PLUGIN_PLATFORM:-$(uname -m)}" in
  x86_64|linux_amd64)  PLATFORM=linux_amd64 ;;
  aarch64|arm64|linux_arm64) PLATFORM=linux_arm64 ;;
  *) echo "unsupported platform: ${IFDD_TS_PLUGIN_PLATFORM:-$(uname -m)}" >&2; exit 1 ;;
esac

mkdir -p "$CACHE" "$TARGET"
found=0
while read -r id version platform sha256 url; do
  [[ -z "$id" || "$id" == \#* || "$platform" != "$PLATFORM" ]] && continue
  found=$((found + 1))
  zip="$CACHE/$(basename "$url")"

  if [[ ! -f "$zip" ]]; then
    if $OFFLINE; then
      echo "missing $zip (offline mode)" >&2; exit 1
    fi
    echo "download $id $version ($platform)"
    curl -fsSL --retry 3 -o "$zip.part" "$url"
    mv "$zip.part" "$zip"
  fi

  if ! echo "$sha256  $zip" | shasum --algorithm 256 --check --status; then
    echo "checksum mismatch for $zip - removed, not installed" >&2
    rm -f "$zip"; exit 1
  fi

  staging=$(mktemp -d)
  unzip -q "$zip" -d "$staging"
  if [[ ! -f "$staging/$id/plugin.json" ]]; then
    echo "$zip does not contain $id/plugin.json" >&2; rm -rf "$staging"; exit 1
  fi
  rm -rf "${TARGET:?}/$id"
  mv "$staging/$id" "$TARGET/$id"
  rm -rf "$staging"
  # Readable for the Grafana user in the container (uid 472).
  chmod -R a+rX "$TARGET/$id"
  echo "installed $id $version ($platform)"
done < "$LOCK"

if [[ $found -eq 0 ]]; then
  echo "no plugin in $LOCK for platform $PLATFORM" >&2; exit 1
fi
