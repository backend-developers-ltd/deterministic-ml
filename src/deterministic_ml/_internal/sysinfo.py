import csv
import platform
import re
import shutil
import subprocess
import sys


def run_cmd(cmd):
    proc = subprocess.run(cmd, shell=True, capture_output=True, check=False, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"run_cmd error {cmd=!r} {proc.returncode=} {proc.stdout=!r} {proc.stderr=!r}")
    return proc.stdout


def get_machine_specs():
    """
    Get machine specs using various system commands.

    Heavily inspired by https://github.com/backend-developers-ltd/ComputeHorde/blob/e8c0f720c02cf3308627b2dae43b899e253b0b54/executor/app/src/compute_horde_executor/executor/management/commands/run_executor.py#L212
    MIT Licensed https://github.com/backend-developers-ltd/ComputeHorde/blob/e8c0f720c02cf3308627b2dae43b899e253b0b54/LICENSE
    """
    data = {}

    data["docker_support"] = {
        "runc": False,
        "nvidia": False,
    }
    if shutil.which("docker"):
        for runtime in ["runc", "nvidia"]:
            try:
                data["docker_support"][runtime] = (
                    subprocess.check_output(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "--runtime",
                            runtime,
                            "busybox:stable-musl",
                            "echo",
                            "works",
                        ],
                        text=True,
                        stderr=subprocess.DEVNULL,
                    ).strip()
                    == "works"
                )
            except subprocess.CalledProcessError:
                pass

    data["gpu"] = {"count": 0, "details": []}
    nvidia_cmd = "nvidia-smi --query-gpu=name,driver_version,name,memory.total,compute_cap,power.limit,clocks.gr,clocks.mem --format=csv"  # noqa: E501
    if data["docker_support"]["nvidia"]:
        nvidia_cmd = f"docker run --rm --runtime=nvidia --gpus all ubuntu:24.04 {nvidia_cmd}"
    try:
        nvidia_cmd_output = run_cmd(nvidia_cmd)
        csv_data = csv.reader(nvidia_cmd_output.splitlines())
        header = [x.strip() for x in next(csv_data)]
        for row in csv_data:
            row = [x.strip() for x in row]
            gpu_data = dict(zip(header, row))
            data["gpu"]["details"].append(
                {
                    "name": gpu_data["name"],
                    "driver": gpu_data["driver_version"],
                    "capacity": gpu_data["memory.total [MiB]"].split(" ")[0],
                    "cuda": gpu_data["compute_cap"],
                    "power_limit": gpu_data["power.limit [W]"].split(" ")[0],
                    "graphics_speed": gpu_data["clocks.current.graphics [MHz]"].split(" ")[0],
                    "memory_speed": gpu_data["clocks.current.memory [MHz]"].split(" ")[0],
                }
            )
        data["gpu"]["count"] = len(data["gpu"]["details"])
    except Exception as exc:
        # print(f'Error processing scraped gpu specs: {exc}', flush=True)
        data["gpu_scrape_error"] = repr(exc)

    data["cpu"] = {"count": 0, "model": "", "clocks": []}
    try:
        lscpu_output = run_cmd("lscpu")
        data["cpu"]["model"] = re.search(r"Model name:\s*(.*)$", lscpu_output, re.M).group(1)
        data["cpu"]["count"] = int(re.search(r"CPU\(s\):\s*(.*)", lscpu_output).group(1))

        cpu_data = run_cmd('lscpu --parse=MHZ | grep -Po "^[0-9,.]*$"').splitlines()
        data["cpu"]["clocks"] = [float(x) for x in cpu_data]
    except Exception as exc:
        data["cpu_scrape_error"] = repr(exc)

    data["ram"] = {}
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()

        for name, key in [
            ("MemAvailable", "available"),
            ("MemFree", "free"),
            ("MemTotal", "total"),
        ]:
            data["ram"][key] = int(re.search(rf"^{name}:\s*(\d+)\s+kB$", meminfo, re.M).group(1))
        data["ram"]["used"] = data["ram"]["total"] - data["ram"]["free"]
    except Exception as exc:
        data["ram_scrape_error"] = repr(exc)

    data["hard_disk"] = {}
    try:
        disk_usage = shutil.disk_usage(".")
        data["hard_disk"] = {
            "total": disk_usage.total // 1024,  # in kiB
            "used": disk_usage.used // 1024,
            "free": disk_usage.free // 1024,
        }
    except Exception as exc:
        data["hard_disk_scrape_error"] = repr(exc)

    data["os"] = ""
    try:
        data["os"] = run_cmd('lsb_release -d | grep -Po "Description:\\s*\\K.*"').strip()
    except Exception as exc:
        data["os_scrape_error"] = repr(exc)

    return data


def get_python_env_specs():
    if shutil.which("uv") is None:
        pip_cmd = [sys.executable, "-m", "pip"]
    else:
        pip_cmd = ["uv", "pip"]

    package_list = (
        subprocess.check_output(
            [*pip_cmd, "freeze"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        .strip()
        .split("\n")
    )

    data = {
        "version": sys.version,
        "packages": package_list,
    }

    return data


def get_system_info():
    """Gather system information."""
    system_info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    try:
        dpkg_packages = (
            subprocess.check_output(
                [
                    "dpkg-query",
                    "-W",
                    "-f",
                    "${Package}==${Version}\n",
                ],
                text=True,
            )
            .strip()
            .splitlines()
        )
    except subprocess.CalledProcessError:
        pass
    else:
        system_info["dpkg_packages"] = dpkg_packages

    return system_info


def cuda_info():
    try:
        import torch
    except ImportError:
        return {}
    else:
        return {
            "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
        }


def get_specs():
    return {
        "machine": get_machine_specs(),
        "python": get_python_env_specs(),
        "system": get_system_info(),
        "cuda": cuda_info(),
    }


def _main():
    specs = get_specs()
    try:
        import yaml
    except ImportError:
        import json

        json.dump(specs, sys.stdout, indent=2)
    else:
        yaml.safe_dump(specs, sys.stdout, sort_keys=True)


if __name__ == "__main__":
    _main()
