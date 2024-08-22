from deterministic_ml._internal.sysinfo import get_machine_specs, get_specs


def test_get_machine_specs():
    machine_specs = get_machine_specs()
    assert machine_specs.keys() == {
        "docker_support",
        "gpu",
        "gpu_scrape_error",
        "cpu",
        "ram",
        "hard_disk",
        "os",
    }
    assert machine_specs["cpu"]["count"] > 0
    assert machine_specs["ram"]["total"] > 0
    assert machine_specs["os"]


def test_get_specs():
    specs = get_specs()
    assert specs.keys() == {
        "cuda",
        "machine",
        "python",
        "system",
    }
