# Manual integration testing

This document describes how we test whenever we are able to achieve deterministic results for particular experiment scenarios against tested hardware and software configurations.

1) For each hardware configuration:
   1) Create target machine \[manual\]
   2) Run the target experiment scenario on the target machine.
      `./run.py vllm_llama_3_70b_instruct_awq -n machine_name username@host -p ssh_port`
   3) Destroy the target machine \[manual\]
2) Analyze the results \[manual\] 

## Initial local setup

```bash
pdm install -G test
```

## Choosing experiment scenario

Either use already defined scenario in [tests/integration/experiments](../tests/integration/experiments), e.g. 
`vllm_llama_3_70b_instruct_awq` or create a new one.

Each scenario may define target machine environment initial setup steps, including:
* `setup.sh` - Shell script executed on the target machine, for example, installing binary dependencies.
* `requirements.txt` - Python packages installed on the target machine in dedicated python virtual environment.

And must include:
* `__main__.py` - Main experiment script, which is executed on the target machine taking as first argument the output directory to which `output.yaml` file should be saved.

## Running the experiment scenario


### Run experiment against N target machines

Repeat following for a number of target machines.
You may want to even mix some of configurations, e.g. different GPU models, different CUDA versions, etc. to get a better understanding what influences the determinism of output.

### Create target machine

You can use service cheap GPU machines like ones provided by [vast.ai](https://vast.ai/), [paperspace](https://www.paperspace.com/) etc.
Please note that for one-off experiment, services like vast.ai are more cost-effective since they are billed per minute and not per hour.
See [Compute Providers document](COMPUTE_PROVIDERS.md) for more information.

Example machine configuration: vast.io, on-demand, 1x NVIDIA A100 80GB, 100GB disk with Ubuntu-based template +CUDA drivers installed.

### Run the experiment scenario

In [tests/integration/experiments](../tests/integration/experiments) directory, run

```bash
./run.py vllm_llama_3_70b_instruct_awq -c target_comment username@host -p ssh_port
```

### Destroy the target machine

Destroy the target machine to avoid unnecessary costs.


## Analyzing the results

Results are stored in [`results` directory](../tests/integration/results).
They are grouped by experiment scenario, then target machine name and timestamp.

Each result contains:
* `experiment.log` - Experiment log output.
* `output.yaml` - Experiment output in YAML format. This is the most important file to analyze.
* `sysinfo.yaml` - System information of the target machine, used to cluster results by hardware configuration.

You can use `./analyze.py` script to analyze the results.

```bash
./analyze.py vllm_llama_3_70b_instruct_awq 
```
