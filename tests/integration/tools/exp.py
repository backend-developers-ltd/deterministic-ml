import dataclasses
import hashlib
import logging
import pathlib
from collections.abc import Iterable

import yaml

LOG = logging.getLogger(__name__)

_TEST_TOP_PATH = pathlib.Path(__file__).parent.parent

EXP_DIR_PATH = _TEST_TOP_PATH / "experiments"
RESULTS_DIR_PATH = _TEST_TOP_PATH / "results"


def get_experiment_dir(experiment_name: str) -> pathlib.Path:
    exp_dir = EXP_DIR_PATH / experiment_name
    if exp_dir.exists():
        return exp_dir
    else:
        raise FileNotFoundError(f"Experiment directory '{experiment_name}' not found in {EXP_DIR_PATH.absolute()!r}")


def get_experiment_hash(experiment_name: str) -> str:
    exp_dir = get_experiment_dir(experiment_name)
    hasher = hashlib.blake2b()
    for file_path in sorted(exp_dir.glob("*.*")):
        extension = file_path.suffix.lower()
        if extension in {".pyc", ".pyo", ".md"}:
            continue
        with file_path.open("rb") as f:
            hasher.update(f.read())
    return f"exp_hash_v1:{hasher.hexdigest()[:6]}"


@dataclasses.dataclass
class ExperimentRun:
    run_id: str
    output: dict
    sysinfo: dict
    output_dir_path: pathlib.Path


def get_experiment_runs(experiment_name: str) -> Iterable[ExperimentRun]:
    runs_outputs = (RESULTS_DIR_PATH / experiment_name).glob("*/output.yaml")

    for run_output in runs_outputs:
        run_id = run_output.parent.name
        with run_output.open() as f:
            output_data = yaml.safe_load(f)
        with (run_output.parent / "sysinfo.yaml").open() as f:
            sysinfo_data = yaml.safe_load(f)
        yield ExperimentRun(
            run_id=run_id,
            output=output_data,
            sysinfo=sysinfo_data,
            output_dir_path=run_output.parent,
        )
