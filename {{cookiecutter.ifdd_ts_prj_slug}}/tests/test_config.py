"""Static checks of the instance configuration.

They need no Docker and no running service: pytest and PyYAML only.
    pip install pytest pyyaml && pytest tests
"""

from __future__ import annotations

import configparser
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GRAFANA = ROOT / "grafana"
COMPOSE = {mode: ROOT / f"docker-compose-{mode}.yml" for mode in ("production", "development")}
DATASOURCE_UIDS = {"ifdd-ts-vm", "ifdd-ts-be"}
IRI = re.compile(r"^https?://[^\s/]+/\S*$")


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text())


def dashboards():
    return sorted((GRAFANA / "dashboards").rglob("*.json"))


def test_nothing_left_unrendered():
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and path.suffix in {".yml", ".yaml", ".ini", ".md", ".py", ".sh", ".dist"}:
            assert "cookiecutter." not in path.read_text(errors="ignore") or path.name == "test_config.py", path


def test_grafana_ini_offline_and_strict():
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(GRAFANA / "grafana.ini")
    assert ini["analytics"]["reporting_enabled"] == "false"
    assert ini["analytics"]["check_for_updates"] == "false"
    assert ini["plugins"]["preinstall_disabled"] == "true"
    assert ini["plugins"]["public_key_retrieval_disabled"] == "true"
    assert ini["snapshots"]["external_enabled"] == "false"
    oauth = ini["auth.generic_oauth"]
    assert oauth["role_attribute_strict"] == "true"
    assert oauth["client_secret"].startswith("$__file{/run/secrets/")
    for role in ("'Admin'", "'Editor'", "'Viewer'"):
        assert role in oauth["role_attribute_path"]


def test_datasources():
    config = load_yaml(GRAFANA / "provisioning/datasources/ifdd.yaml")
    by_uid = {ds["uid"]: ds for ds in config["datasources"]}
    assert set(by_uid) == DATASOURCE_UIDS
    assert by_uid["ifdd-ts-vm"]["url"] == "http://victoriametrics:8428"
    be = by_uid["ifdd-ts-be"]
    # Infinity reads the base URL from the top-level url, not from jsonData.
    assert be["url"] == "$__env{IFDD_TS_BE_URL}"
    assert "url" not in be["jsonData"]
    assert be["jsonData"]["allowedHosts"] == [be["url"]]


def test_unused_bundled_plugins_are_disabled():
    """Each bundled data source runs as a process of its own; only the provisioned ones stay."""
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(GRAFANA / "grafana.ini")
    disabled = {p.strip() for p in ini["plugins"]["disable_plugins"].split(",")}
    used = {ds["type"] for ds in load_yaml(GRAFANA / "provisioning/datasources/ifdd.yaml")["datasources"]}
    assert used == {"prometheus", "yesoreyeram-infinity-datasource"}
    assert not disabled & used
    assert {"loki", "tempo", "elasticsearch", "mysql", "stackdriver"} <= disabled


@pytest.mark.parametrize("path", dashboards(), ids=lambda p: p.name)
def test_dashboard(path):
    dash = json.loads(path.read_text())
    assert dash["uid"] and dash["editable"] is False
    used = set()

    def collect(node):
        if isinstance(node, dict):
            ds = node.get("datasource")
            if isinstance(ds, dict) and "uid" in ds:
                used.add(ds["uid"])
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)

    collect(dash)
    assert used <= DATASOURCE_UIDS, used - DATASOURCE_UIDS


def test_dashboard_uids_unique():
    uids = [json.loads(p.read_text())["uid"] for p in dashboards()]
    assert len(uids) == len(set(uids))


def test_object_path_regex():
    dash = json.loads((GRAFANA / "dashboards/ifdd/ifdd-object.json").read_text())
    variable = next(v for v in dash["templating"]["list"] if v["name"] == "object_path")
    pattern = variable["regex"].strip("/").replace("\\/", "/")
    assert re.match(pattern, "https://a.example.org/products/t-1").group(1) == "/products/t-1"
    assert re.match(pattern, "http://a.example.org/x/y#frag").group(1) == "/x/y"


def test_plugins_lock():
    lines = [l.split() for l in (GRAFANA / "plugins.lock").read_text().splitlines()
             if l.strip() and not l.startswith("#")]
    assert lines
    for plugin_id, version, platform, sha256, url in lines:
        assert re.fullmatch(r"[0-9a-f]{64}", sha256)
        assert platform in {"linux_amd64", "linux_arm64"}
        assert url.startswith("https://") and version in url and platform in url


@pytest.mark.parametrize("mode", COMPOSE)
def test_compose_hardening(mode):
    services = load_yaml(COMPOSE[mode])["services"]
    assert set(services) == {"victoriametrics", "grafana"}
    for name, service in services.items():
        assert service["read_only"] is True, name
        assert service["cap_drop"] == ["ALL"], name
        assert "no-new-privileges:true" in service["security_opt"], name
    assert "traefik.enable=false" in services["victoriametrics"]["labels"]


@pytest.mark.parametrize("mode", COMPOSE)
def test_victoriametrics_deduplicates_and_joins_the_ingest_network(mode):
    document = load_yaml(COMPOSE[mode])
    vm = document["services"]["victoriametrics"]
    assert "-dedup.minScrapeInterval=1ms" in vm["command"]
    assert "ingest" in vm["networks"]
    assert document["networks"]["ingest"]["external"] is True


def test_grafana_trusts_the_cas_in_certs():
    """Grafana calls the realm (login) and the backend (data sources) itself;
    on another server with a CA of its own that CA must be trusted (certs/)."""
    grafana = load_yaml(COMPOSE["production"])["services"]["grafana"]
    dirs = grafana["environment"]["SSL_CERT_DIR"].split(":")
    assert "/etc/ssl/certs" in dirs, "the system CAs must stay trusted"
    mounts = [v for v in grafana["volumes"] if isinstance(v, dict) and v.get("target") in dirs]
    assert len(mounts) == 1, grafana["volumes"]
    mount = mounts[0]
    assert mount["source"] == "./certs" and mount["read_only"] is True
    assert mount["bind"]["create_host_path"] is False
    assert (ROOT / "certs").is_dir()



def dotenv_values(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line and not line.startswith("#"))


def test_victoriametrics_runs_as_the_host_user_in_production():
    """The image sets no user: without one, VictoriaMetrics runs as root and
    everything below IFDD_TS_VM_DATA_DIR belongs to root on the host."""
    vm = load_yaml(COMPOSE["production"])["services"]["victoriametrics"]
    assert re.fullmatch(r"\$\{IFDD_TS_VM_UID:\?[^}]*\}:\$\{IFDD_TS_VM_GID:\?[^}]*\}", vm["user"])
    mounts = [v for v in vm["volumes"] if isinstance(v, dict) and v.get("target") == "/storage"]
    assert len(mounts) == 1, vm["volumes"]
    assert mounts[0]["type"] == "bind"
    assert mounts[0]["source"].startswith("${IFDD_TS_VM_DATA_DIR:?")
    # Created by Docker, a missing directory would belong to root.
    assert mounts[0]["bind"]["create_host_path"] is False


def test_dotenv_takes_the_ids_of_the_host_user():
    values = dotenv_values(ROOT / "dotenv.dist")
    assert values["IFDD_TS_VM_UID"] == "<<host:uid>>"
    assert values["IFDD_TS_VM_GID"] == "<<host:gid>>"


def test_generated_env_names_a_user_other_than_root():
    """A fresh .env has the ids (the template CI checks that the hook writes
    them). An instance from before keeps its .env (skip list) and gets them
    by hand, as operations.md describes; adm_02_run.sh reports them missing."""
    env = ROOT / ".env"
    if not env.exists():
        pytest.skip("no .env")
    values = dotenv_values(env)
    if "IFDD_TS_VM_UID" not in values and "IFDD_TS_VM_GID" not in values:
        pytest.skip(".env from before IFDD_TS_VM_UID: add the ids by hand (docs/en/operations.md)")
    uid, gid = values.get("IFDD_TS_VM_UID", ""), values.get("IFDD_TS_VM_GID", "")
    assert uid.isdigit() and gid.isdigit(), (uid, gid)
    assert uid != "0"


def test_relative_data_directory_is_not_committed():
    data = dotenv_values(ROOT / "dotenv.dist")["IFDD_TS_VM_DATA_DIR"]
    if not data.startswith("./"):
        pytest.skip(f"IFDD_TS_VM_DATA_DIR={data} is outside the instance")
    assert "/" + data[2:].rstrip("/") + "/" in (ROOT / ".gitignore").read_text().splitlines()

def test_production_does_not_publish_ports():
    services = load_yaml(COMPOSE["production"])["services"]
    assert all("ports" not in service for service in services.values())
    networks = load_yaml(COMPOSE["production"])["networks"]
    assert networks["internal"]["internal"] is True


def test_dotenv_covers_compose_variables():
    defined = {l.split("=", 1)[0] for l in (ROOT / "dotenv.dist").read_text().splitlines()
               if l and not l.startswith("#")}
    used = set()
    for path in COMPOSE.values():
        used |= set(re.findall(r"\$\{(IFDD_TS_[A-Z_]+)", path.read_text()))
    assert used <= defined, used - defined


def test_examples_follow_series_contract():
    spec = importlib.util.spec_from_file_location("load_examples", ROOT / "examples/load_examples.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in module.series(seed=1, hours=1, step_s=600):
        labels = line["metric"]
        for key in ("ifdd_id", "ifdd_property", "ifdd_unit"):
            assert IRI.match(labels[key]), (key, labels[key])
        assert len(line["values"]) == len(line["timestamps"])
