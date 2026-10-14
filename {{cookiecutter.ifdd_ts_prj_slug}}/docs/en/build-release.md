(ifdd-ts-build-release)=
# Build and release

## Images

| Container | Image |
|---|---|
| `grafana` | `{{ cookiecutter.ifdd_ts_grafana_image }}` |
| `victoriametrics` | `{{ cookiecutter.ifdd_ts_vm_image }}` |

The instance builds no image. Both run with a read-only root file system;
the configuration, the provisioning files, the dashboards and the plugin
are mounted read-only. For a mirror, set the image variables to the images
in the internal registry.

## The Grafana plugin

`grafana/plugins.lock` names each plugin with version, platform, SHA-256 and
download URL; `adm_01_plugins.sh` fetches and verifies them. The platform is
taken from the host (`linux_amd64`, `linux_arm64`), or from
`IFDD_TS_PLUGIN_PLATFORM`.

## Versions and updates

The image tags are template variables; `plugins.lock` comes from the
template. To update Grafana or the plugin, change the image or
`plugins.lock` (version, checksum, URL) in the template, check the plugin's
Grafana dependency, then `cruft update` the instance and run
`adm_01_plugins.sh` again. Tested with Grafana 13.2.3, VictoriaMetrics
v1.153.0 and Infinity 4.0.0.

## Dashboards

Dashboards are files. The shipped ones live in `grafana/dashboards/ifdd/`
(updated by cruft), your own in `grafana/dashboards/private/` (skipped by
cruft). Changes made in the Grafana UI cannot be saved: edit the JSON and
restart.

## Tests

```bash
pytest tests        # static checks of the configuration
```

The static checks cover the offline and strict settings of `grafana.ini`,
the data sources, the disabled bundled plugins, every dashboard, the plugin
lock, the container hardening, the absence of published ports in
production, that `dotenv.dist` covers every compose variable, and that the
examples follow the series contract.

## CI of the instance

`.github/workflows/ci.yml` runs the static checks and validates both compose
files.

## Release

There is no release workflow, because no image is built.
