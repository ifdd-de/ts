# Changelog

## [Unreleased]

- VictoriaMetrics runs as a host user in production, no longer as root:
  `user: ${IFDD_TS_VM_UID}:${IFDD_TS_VM_GID}`. The image sets no user, so
  everything below `IFDD_TS_VM_DATA_DIR` belonged to root, and deleting it
  needed `sudo`. The post-generation hook writes the ids of the user who
  generates the instance into `.env` (`<<host:uid>>`, `<<host:gid>>` in
  `dotenv.dist`, as in `ifdd-de/keycloak`), creates the data directory
  (mode 0700) and refuses to run as root.
- The data directory is a bind mount with `create_host_path: false`: a
  missing directory stops compose instead of being created as root.
  `adm_02_run.sh production` checks the ids and that every file in the
  directory belongs to `IFDD_TS_VM_UID`, and names the `chown` otherwise.
- `.gitignore` of the instance lists a data directory inside the instance
  (default `./vm_data`); before, `git add .` took the series along.
- Development is unchanged (named volume `vm-dev-data`).
- Tests: `tests/test_config.py` (user, mount, ids in `.env`, `.gitignore`),
  `tests/test_run_script.py` (checks of `adm_02_run.sh` with a stand-in for
  docker); template CI: job `production-vm` starts VictoriaMetrics of the
  production file, writes a sample and deletes the directory as the runner
  user; the hook refuses `sudo cookiecutter`. Fixture `custom` uses
  `./data/vm`. The check of the ids in `.env` skips a `.env` from before
  this change (kept by the skip list, as in the update test); a `.env` with
  only one of the two ids fails.
- Docs: setup, operations ("Owner of the data"), security, reference,
  troubleshooting.
- Upgrade: `cruft update`; then add `IFDD_TS_VM_UID` and `IFDD_TS_VM_GID`
  (`id -u`, `id -g`) to `.env`, which is on the skip list; stop
  VictoriaMetrics, `sudo chown -R <uid>:<gid> <IFDD_TS_VM_DATA_DIR>` once,
  and start with `./adm_02_run.sh production`.

- Grafana trusts the CA certificates in `certs/` (new directory; the
  certificates are not committed): production mounts it read-only
  and sets `SSL_CERT_DIR=/etc/ssl/certs:/etc/ifdd/certs`, so the login
  (token exchange with the realm) and the plugins (Infinity, backend) work
  with an internal CA, also when realm or backend run on another server.
  Before, the template did not wire this up.
- Setup page: section on several servers; security page: certificates;
  troubleshooting: certificate errors at login point to `certs/`.
- Upgrade: `cruft update` brings `certs/README.md`; put the CA there, then
  recreate Grafana (`docker compose -f docker-compose-production.yml up -d`).
  The compose file requires the directory (`create_host_path: false`).
  `certs` stays off the skip list: there it would keep the directory from
  arriving, and cruft never touches the certificates in it, which are not
  part of the template.
- CI: the update test creates its instance with the skip list of the README.
  Without it, the secrets the hook generates in every rendering left `.rej`
  files; this showed with the first update after the tag `v26.10.3`.

## [26.10.3] - 2026-10-30

- Grafana 13.3.0 (`ifdd_ts_grafana_image`, was 13.2.3), VictoriaMetrics
  v1.155.0 (`ifdd_ts_vm_image`, was v1.153.0), Infinity data source 4.1.5
  (`grafana/plugins.lock`, was 4.0.0, checksums from the release zips).
- `build-release`: after a Grafana update check the list of bundled plugins
  for `disable_plugins`; Grafana 13.3.0 not tested.
- Documentation check: Sphinx 9.2.0 (`tests/docs/requirements.txt`).
- Upgrade: `cruft update`, `./adm_01_plugins.sh`, then
  `docker compose -f docker-compose-production.yml up -d`. Instances generated
  with the old image values change them with `cruft update
  --variables-to-update`.

- VictoriaMetrics runs with `-dedup.minScrapeInterval=1ms` in both modes: of
  two samples of one series with the same time it keeps one (the larger
  value), so that repeated writes, e.g. through ts-api, are harmless.
- In development VictoriaMetrics joins the ingest network too, so that
  writers such as ts-api reach it at `victoriametrics:8428` in both modes.
  The network must exist in development as well.
- Series contract (`docs/*/series.md`): `ifdd_property` names a property in a
  vocabulary of the type service (was "the `schema` vocabulary"), example
  IRIs in the form of the type and unit services, the optional label
  `ifdd_store`, the two ways in (ts-api, directly) and the deduplication.
  `examples/load_examples.py` uses the new example IRIs.
- Security page: what ts-api checks and what it does not reach (Grafana, the
  ingest network).

## [26.10.2] - 2026-10-14

- Documentation of the instance in `docs/en` and `docs/de` (Sphinx sources,
  MyST Markdown): index, setup, build and release, operations, security,
  troubleshooting, reference, series. `docs/series.md` moved to
  `docs/en/series.md` (with a German version `docs/de/series.md`); the links
  in the README and `examples/load_examples.py` follow. The instance README
  is now an entry point with a quick start, the links, the honesty notes and
  the license; its former sections moved into the documentation.
- `docs/_build/` in `.gitignore` of the instance.
- Template CI: `tests/check_docs.py` checks that both languages match and
  build without warnings (`tests/docs/conf.py`, `tests/docs/requirements.txt`).
- Grafana: `disable_plugins` in `grafana.ini` for the bundled data sources the
  instance does not use (elasticsearch, postgresql, pyroscope, influxdb,
  jaeger, loki, mssql, mysql, opentsdb, stackdriver, tempo, zipkin). Grafana
  13.2.3 started each as a process of its own (measured on arm64: 3 processes
  instead of 15, process memory 191 MB instead of 209 MB).
- Default `ifdd_ts_grafana_memory_limit` 1G (was 512M): Grafana's processes
  need about 200 MB idle, and the container kept reaching 512M (file cache
  pushed out 1941 times, no OOM kill). Existing instances keep their value
  in `.cruft.json`; change it with
  `cruft update --variables-to-update '{"ifdd_ts_grafana_memory_limit": "1G"}'`.

## [26.10.1] - 2026-10-01

First release of the template `ifdd-de/ts`.

- VictoriaMetrics (v1.153.0) and Grafana (13.2.3) as upstream images, read-only,
  without capabilities; VictoriaMetrics only on the internal and the ingest network.
- Series contract: labels `ifdd_id`, `ifdd_property`, `ifdd_unit` with full IRIs.
- Dashboards "IFDD series overview" and "IFDD object"; the object is read from
  ifdd-be with the Infinity plugin (4.0.0) and OAuth2 client credentials.
- Keycloak login with strict role mapping (admin, readwrite, readonly).
- No internet at runtime: plugin fetched and checksum-verified by
  `adm_01_plugins.sh`, also from an offline cache.
- Retention 10 years by default.
