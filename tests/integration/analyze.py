#!/usr/bin/env python3
import argparse
import collections
import hashlib
import logging

import tools.exp
import yaml
from rich import print

LOG = logging.getLogger(__name__)


def hash_output(output: dict) -> str:
    hasher = hashlib.blake2b()
    json_str = yaml.dump(output, sort_keys=True)
    hasher.update(json_str.encode("utf8"))
    return hasher.hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="Experiment name")
    args = parser.parse_args()

    experiment_name = args.experiment.split("/")[-1]

    runs_outputs = sorted(
        tools.exp.get_experiment_runs(experiment_name),
        key=lambda run: run.run_id,
    )
    print(f"Found {len(runs_outputs)} runs with output.yaml for experiment {experiment_name!r}")

    runs_by_hash = collections.defaultdict(list)
    for run_output in runs_outputs:
        output_hash = hash_output(run_output.output)
        runs_by_hash[output_hash].append(run_output)

    print(f"Found {len(runs_by_hash)} unique outputs for {len(runs_outputs)} runs")
    for group_no, (output_hash, runs) in enumerate(runs_by_hash.items()):
        print(f"[bold]Group {group_no}[/bold] hash={output_hash[:6]} runs={len(runs)}")
        for run in runs:
            print(f"  - Run: {run.run_id} ({run.output_dir_path})")
            print(f"    - {run.sysinfo['cuda']}")
            print(f"    - {run.sysinfo['machine']['gpu']}")
