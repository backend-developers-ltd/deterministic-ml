# deterministic-ml
&nbsp;[![Continuous Integration](https://github.com/backend-developers-ltd/deterministic-ml/workflows/Continuous%20Integration/badge.svg)](https://github.com/backend-developers-ltd/deterministic-ml/actions?query=workflow%3A%22Continuous+Integration%22)&nbsp;[![License](https://img.shields.io/pypi/l/deterministic_ml.svg?label=License)](https://pypi.python.org/pypi/deterministic_ml)&nbsp;[![python versions](https://img.shields.io/pypi/pyversions/deterministic_ml.svg?label=python%20versions)](https://pypi.python.org/pypi/deterministic_ml)&nbsp;[![PyPI version](https://img.shields.io/pypi/v/deterministic_ml.svg?label=PyPI%20version)](https://pypi.python.org/pypi/deterministic_ml)

## Usage

> [!IMPORTANT]
> This package uses [ApiVer](#versioning), make sure to import `deterministic_ml.v1`.


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

### Release process

Run `nox -s make_release -- X.Y.Z` where `X.Y.Z` is the version you're releasing and follow the printed instructions.
