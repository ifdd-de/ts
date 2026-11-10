"""adm_02_run.sh production: the checks of the data directory of VictoriaMetrics.

The script runs in a copy of the files it reads, with a stand-in for docker
that only records its arguments; no Docker and no root are needed. Files
that belong to another user are simulated by setting IFDD_TS_VM_UID to an id
other than that of the user running the tests.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "adm_02_run.sh"


@pytest.fixture
def instance(tmp_path):
    work = tmp_path / "instance"
    work.mkdir()
    shutil.copy(SCRIPT, work / SCRIPT.name)
    (work / "secrets").mkdir()
    for name in ("grafana_admin_password", "grafana_secret_key", "oidc_client_secret"):
        (work / "secrets" / name).write_text("x")
    plugin = work / "grafana/plugins/yesoreyeram-infinity-datasource"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text("{}")
    data = work / "vm_data"
    (data / "cache").mkdir(parents=True)
    (data / "cache" / "part").write_text("x")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text('#!/bin/sh\necho "$@" > "$DOCKER_LOG"\n')
    docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "docker.log"

    def run(uid=os.getuid(), gid=os.getgid(), data_dir="./vm_data"):
        (work / ".env").write_text(
            f"IFDD_TS_VM_DATA_DIR={data_dir}\nIFDD_TS_VM_UID={uid}\nIFDD_TS_VM_GID={gid}\n"
        )
        env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", DOCKER_LOG=str(log))
        result = subprocess.run(["bash", str(work / SCRIPT.name), "production"],
                                cwd=work, env=env, capture_output=True, text=True)
        started = log.read_text() if log.exists() else ""
        return result, started

    return run


@pytest.mark.skipif(os.getuid() == 0, reason="the script refuses uid 0 (run the tests as a user)")
def test_data_owned_by_the_configured_user_starts(instance):
    result, started = instance()
    assert result.returncode == 0, result.stderr
    assert "compose -f docker-compose-production.yml up -d" in started


def test_data_of_another_user_is_refused_with_the_chown_command(instance):
    other = os.getuid() + 1
    result, started = instance(uid=other)
    assert result.returncode == 1
    assert f"does not belong to uid {other}" in result.stderr
    assert f"sudo chown -R {other}:" in result.stderr
    assert started == ""


def test_missing_data_directory_is_refused(instance):
    result, started = instance(data_dir="./missing")
    assert result.returncode == 1
    assert "./missing is missing" in result.stderr
    assert started == ""


@pytest.mark.parametrize("uid,gid", [("0", "0"), ("", ""), ("<<host:uid>>", "<<host:gid>>")])
def test_root_or_unset_ids_are_refused(instance, uid, gid):
    result, started = instance(uid=uid, gid=gid)
    assert result.returncode == 1
    assert "IFDD_TS_VM_UID" in result.stderr
    assert started == ""
