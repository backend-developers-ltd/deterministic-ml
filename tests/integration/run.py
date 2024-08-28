#!/usr/bin/env python3
import argparse
import contextlib
import logging
import pathlib
import re
import subprocess
import tempfile
from datetime import datetime

import tools.exp
import tools.ssh
import yaml
from rich.logging import RichHandler

LOG = logging.getLogger(__name__)

_THIS_DIR = pathlib.Path(__file__).parent
TOOLS_DIR = _THIS_DIR / "tools"
RSYNC_IGNORE_FILEPATH = _THIS_DIR / ".rsyncignore"


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


@contextlib.contextmanager
def build_deterministic_ml():
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["python", "-m", "build", "--wheel", ".", "-o", tmpdir],
            check=True,
            cwd=_THIS_DIR.parent.parent,
        )
        wheel = next(pathlib.Path(tmpdir).glob("deterministic_ml-*.whl"))
        yield wheel


def prepare_env(remote_run_command, run_dir, experiment_dir_name):
    remote_run_command(
        f"""
    set -exo pipefail
    
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH=$HOME/.cargo/bin:$PATH
    
    cd {run_dir}
    uv venv -p python3.11 --python-preference managed
    source .venv/bin/activate 
    uv pip install \
      ./deterministic_ml*.whl \
      pyyaml \
      -r {experiment_dir_name}/requirements.txt
    """
    )


class TimingStats:
    def __init__(self):
        self.timings = {}

    @contextlib.contextmanager
    def timed(self, name):
        start = datetime.now()
        yield
        took = datetime.now() - start
        self.timings[name] = took.total_seconds()


def main():
    parser = argparse.ArgumentParser(description="deterministic-ml experiment runner")
    parser.add_argument("experiment", help="Experiment name")
    parser.add_argument("-p", "--port", type=int, default=22, help="SSH port")
    parser.add_argument("remote", help="user@host")
    parser.add_argument("-c", "--comment", default="", help="Optional comment")
    parser.add_argument(
        "--remote-storage-path",
        default="~/experiments/",
        help="Remote storage path prefix for experiments' venv and other files",
    )
    args = parser.parse_args()

    slug = args.comment.lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    local_experiment_dir = tools.exp.get_experiment_dir(args.experiment)
    exp_run_id = f"{args.experiment}/{timestamp}_{slug}"
    remote_experiment_dir = pathlib.Path(args.remote_storage_path) / exp_run_id

    remote_output_dir = remote_experiment_dir / "output"
    local_output_dir = tools.exp.RESULTS_DIR_PATH / exp_run_id
    local_output_dir.parent.mkdir(parents=True, exist_ok=True)
    local_output_dir.mkdir()

    with (local_output_dir / "experiment.yaml").open("w") as f:
        yaml.dump(
            {
                "experiment": args.experiment,
                "experiment_hash": tools.exp.get_experiment_hash(args.experiment),
                "comment": args.comment,
                "timestamp": timestamp,
                "slug": slug,
                "run_id": exp_run_id,
            },
            f,
        )

    ts = TimingStats()
    # configure local logging to print to file and stderr
    log_file = local_output_dir / "run.local.log"
    file_log_handler = logging.FileHandler(log_file)
    file_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    rich_log_handler = RichHandler(log_time_format="%X")
    if hasattr(rich_log_handler, "_log_render"):
        rich_log_handler._log_render.level_width = 2
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_log_handler)
    root_logger.addHandler(rich_log_handler)
    LOG.info("Starting experiment %s with comment: %s", args.experiment, args.comment)
    LOG.info("Local log file: %s", log_file)

    port = args.port
    if "@" in args.remote:
        username, hostname = args.remote.split("@")
    else:
        username = None
        hostname = args.remote

    ssh_client = tools.ssh.ssh_connect(username=username, hostname=hostname, port=port)

    def remote_exec_command(command, **kwargs):
        return tools.ssh.remote_exec_command(ssh_client, command, **kwargs)

    def rsync_local_to_remote(local_path, remote_path, **kwargs):
        return tools.ssh.rsync_local_to_remote(
            local_path,
            remote_path,
            args.remote,
            port,
            exclude_from=RSYNC_IGNORE_FILEPATH,
            **kwargs,
        )

    LOG.info("Syncing files to remote")
    remote_exec_command(f"mkdir -p {remote_output_dir}")
    rsync_local_to_remote(TOOLS_DIR, remote_experiment_dir)
    rsync_local_to_remote(local_experiment_dir, remote_experiment_dir)
    with build_deterministic_ml() as wheel:
        rsync_local_to_remote(wheel, remote_experiment_dir)

    LOG.info("Setting up remote environment")
    with ts.timed("remote_env_setup"):
        prepare_env(remote_exec_command, remote_experiment_dir, local_experiment_dir.name)

    LOG.info("Gathering system info")
    in_env_cmd = f"""
    set -exo pipefail
    
    cd {remote_experiment_dir}
    export PATH=$HOME/.cargo/bin:$PATH
    source .venv/bin/activate;
    """

    with ts.timed("gathering_sysinfo"):
        remote_exec_command(
            f"{in_env_cmd} python -m deterministic_ml._internal.sysinfo > {remote_output_dir / 'sysinfo.yaml'}"
        )

    LOG.info("Running experiment code on remote")

    try:
        with ts.timed("running_experiment"):
            remote_exec_command(
                f"{in_env_cmd} python -m {local_experiment_dir.name} {remote_output_dir}"
                f" | tee {remote_output_dir / 'stdout.txt'}"
            )
    finally:
        LOG.info("Syncing output back to local")

        tools.ssh.rsync_remote_to_local(
            remote_output_dir,
            local_output_dir,
            args.remote,
            port,
            exclude_from=RSYNC_IGNORE_FILEPATH,
        )

        with (local_output_dir / "experiment.yaml").open("w") as f:
            yaml.dump(
                {
                    "experiment": args.experiment,
                    "experiment_hash": tools.exp.get_experiment_hash(args.experiment),
                    "comment": args.comment,
                    "timestamp": timestamp,
                    "slug": slug,
                    "run_id": exp_run_id,
                    "time_stats": ts.timings,
                },
                f,
            )

    LOG.info("Done")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        LOG.error(
            "Command failed: %r stdout: %r stderr: %r status: %r",
            e.cmd,
            e.stdout,
            e.stderr,
            e.returncode,
        )
        raise
