import logging
import pathlib
import subprocess

import paramiko

LOG = logging.getLogger(__name__)


def rsync_local_to_remote(
    local_path: pathlib.Path,
    remote_path: pathlib.Path,
    remote: str,
    port: int = 22,
    *,
    exclude_from: pathlib.Path,
    dir_content_only: bool = False,
):
    local_path_str = str(local_path) if not dir_content_only else f"{local_path}/"
    rsync_cmd = [
        "rsync",
        "-av",
        "-e",
        f"ssh -p {port} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
        local_path_str,
        f"{remote}:{remote_path}/",
    ]
    if exclude_from:
        rsync_cmd.append(f"--exclude-from={exclude_from.absolute()}")
    return subprocess.run(rsync_cmd, check=True, capture_output=True)


def rsync_remote_to_local(
    remote_path: pathlib.Path,
    local_path: pathlib.Path,
    remote: str,
    port: int = 22,
    *,
    exclude_from: pathlib.Path,
):
    local_path.mkdir(parents=True, exist_ok=True)

    rsync_cmd = [
        "rsync",
        "-av",
        "-e",
        f"ssh -p {port} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
        f"{remote}:{remote_path}/",
        f"{local_path}/",
    ]
    if exclude_from:
        rsync_cmd.append(f"--exclude-from={exclude_from.absolute()}")
    return subprocess.run(rsync_cmd, check=True, capture_output=True)


class SilentMissingHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname: str, key) -> None:
        pass


def ssh_connect(hostname: str, port: int = 22, username: str | None = None) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(SilentMissingHostKeyPolicy())

    client.connect(
        hostname=hostname,
        username=username,
        port=port,
        look_for_keys=True,
        allow_agent=True,
    )
    transport = client.get_transport()
    assert transport is not None  # for mypy; after connect, transport is set
    transport.set_keepalive(5)
    return client


def remote_exec_command(ssh_client: paramiko.SSHClient, command: str, **kwargs):
    stdin, stdout, stderr = ssh_client.exec_command(command, **kwargs)
    status_code = stdout.channel.recv_exit_status()
    log_func = LOG.info if status_code == 0 else LOG.error
    log_func(
        "Command: %r stdout: %r stderr: %r status_code: %r",
        command,
        stdout.read().decode(errors="backslashreplace"),
        stderr.read().decode(errors="backslashreplace"),
        status_code,
    )
    if status_code != 0:
        raise subprocess.CalledProcessError(status_code, command, stdout.read(), stderr.read())
