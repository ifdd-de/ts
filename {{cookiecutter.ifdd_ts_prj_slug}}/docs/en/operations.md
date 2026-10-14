(ifdd-ts-operations)=
# Operations

## Start, stop, order

```bash
./adm_02_run.sh production                     # checks, then docker compose up -d
docker compose -f docker-compose-production.yml ps
docker compose -f docker-compose-production.yml down
```

Grafana waits for a healthy VictoriaMetrics. For the login and the object
panels it needs Keycloak and the backend; start it after them
(`.adm_03_up_services.sh` of the meta repository does).

## Health checks

| Container | Check | Interval |
|---|---|---|
| `victoriametrics` | `wget` on `http://127.0.0.1:8428/health` | 10 s, timeout 5 s, 3 retries, start period 10 s |
| `grafana` | `curl` on `http://127.0.0.1:3000/api/health` | 10 s, timeout 5 s, 3 retries, start period 30 s |

Both restart with `unless-stopped`.

## Logs

```bash
docker compose -f docker-compose-production.yml logs -f grafana victoriametrics
```

## Data and backup

All series are in `IFDD_TS_VM_DATA_DIR`. Back it up consistently with a
snapshot (`/snapshot/create` of VictoriaMetrics) or the separate tool
vmbackup; a plain copy of the running directory is not consistent. Grafana
keeps only users and sessions in its volume `grafana-data`. Keep `.env` and
`secrets/` as well.

```{note}
Not tested: a backup and restore of the series.
```

## Retention

`IFDD_TS_RETENTION` (here `{{ cookiecutter.ifdd_ts_retention }}`). Samples
older than that are deleted and not accepted on ingestion. Lowering it
deletes data.

## Resources

| Container | Memory limit |
|---|---|
| `grafana` | `{{ cookiecutter.ifdd_ts_grafana_memory_limit }}` |
| `victoriametrics` | `{{ cookiecutter.ifdd_ts_vm_memory_limit }}` (a starting value) |

Grafana 13 starts every bundled data source as a process of its own;
`grafana.ini` disables the unused ones (`disable_plugins`). Measured on
arm64 (Grafana 13.2.3, idle): with all bundled plugins 15 processes and
209 MB anonymous memory, with `disable_plugins` 3 processes and 191 MB. The
file cache fills whatever the limit leaves and is given back on demand.
Check in the container with
`cat /sys/fs/cgroup/memory.stat /sys/fs/cgroup/memory.events`: `anon` is the
processes; `max` counts how often the limit was reached, `oom_kill` must
stay 0.

## Applying changes

Data sources, dashboards and `grafana.ini` are read at start: after a change,
`docker compose -f docker-compose-production.yml restart grafana`. Changes
made in the Grafana UI to provisioned dashboards or data sources cannot be
saved.

## Updates

Template updates arrive with `cruft update`; `.env`, `secrets` and
`grafana/dashboards/private` are on the skip list. After an update of
`plugins.lock` run `adm_01_plugins.sh` again.
