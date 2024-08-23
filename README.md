# Deterministic ML Models execution using Python frameworks
&nbsp;[![Continuous Integration](https://github.com/backend-developers-ltd/deterministic-ml/workflows/Continuous%20Integration/badge.svg)](https://github.com/backend-developers-ltd/deterministic-ml/actions?query=workflow%3A%22Continuous+Integration%22)&nbsp;[![License](https://img.shields.io/pypi/l/deterministic_ml.svg?label=License)](https://pypi.python.org/pypi/deterministic_ml)&nbsp;[![python versions](https://img.shields.io/pypi/pyversions/deterministic_ml.svg?label=python%20versions)](https://pypi.python.org/pypi/deterministic_ml)&nbsp;[![PyPI version](https://img.shields.io/pypi/v/deterministic_ml.svg?label=PyPI%20version)](https://pypi.python.org/pypi/deterministic_ml)

This project is two-part:
* documentation that describes how to ensure deterministic execution of ML models across different frameworks
* a Python package that provides utilities that help to ensure deterministic execution of ML models across different frameworks and versions

Currently supported frameworks and inference engines: CUDA-based, PyTorch, vLLM.

The goal is to be able to reproduce exactly the same results on another machine using the same software.
This means, finding a balance between performance and hardware restrictions without compromising reproducibility.
I.e. if limiting to a single GPU model and vRAM size is required to achieve reproducibility, then it is also acceptable solution, especially if otherwise it would require "dumbing down" other cards just to achieve the same results.

## Experiment results so far

Through [Integration testing](docs/MANUAL_INTEGRATION_TESTING.md) we can see that the output of the model can be achieved in a deterministic way.

Here is the summary of the results for vLLM running llama3 model:
* each card GPU model (combined with its vRAM configuration) has a different output, but is consistent across runs
* the output is consistent across different CUDA versions (more testing is needed here, only small range was tested)
* GPU interface (SXM4, PCIe) does not affect the output
* A100 80GB and A100X 80GB produce the same output
* 2x A100 40GB do not produce the same output as 1x A100 80GB
* driver versions 535.129.03 and 555.58.02 produce the same output

To learn more about this particular example, please refer to the [Integration testing](docs/MANUAL_INTEGRATION_TESTING.md) documentation and the [tests/integration/experiments/vllm_llama_3_70b_instruct_awq](tests/integration/experiments/vllm_llama_3_70b_instruct_awq) experiment code.

## Usage

> [!IMPORTANT]
> This package uses [ApiVer](#versioning), make sure to import `deterministic_ml.v1`.


```
pip install deterministic_ml[vllm]  # pick the right extra for your use case, e.g. [vllm] or [torch]
```


## Versioning

This package uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
TL;DR you are safe to use [compatible release version specifier](https://packaging.python.org/en/latest/specifications/version-specifiers/#compatible-release) `~=MAJOR.MINOR` in your `pyproject.toml` or `requirements.txt`.

Additionally, this package uses [ApiVer](https://www.youtube.com/watch?v=FgcoAKchPjk) to further reduce the risk of breaking changes.
This means, the public API of this package is explicitly versioned, e.g. `deterministic_ml.v1`, and will not change in a backwards-incompatible way even when `deterministic_ml.v2` is released.

Internal packages, i.e. prefixed by `deterministic_ml._` do not share these guarantees and may change in a backwards-incompatible way at any time even in patch releases.


## Development


Pre-requisites:
- [pdm](https://pdm.fming.dev/)
- [nox](https://nox.thea.codes/en/stable/)
- [docker](https://www.docker.com/) and [docker compose plugin](https://docs.docker.com/compose/)


Ideally, you should run `nox -t format lint` before every commit to ensure that the code is properly formatted and linted.
Before submitting a PR, make sure that tests pass as well, you can do so using:
```
nox -t check # equivalent to `nox -t format lint test`
```

If you wish to install dependencies into `.venv` so your IDE can pick them up, you can do so using:
```
pdm install --dev
```

## Contributing

Contributions are welcome, especially ones that add to [docs/IMPROVING_CONSITENCY.md](docs/IMPROVING_CONSITENCY.md) docs expanding the list of recommendations for improving the consistency of inference results when using various python frameworks.
