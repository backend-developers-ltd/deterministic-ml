import random

import numpy
import pytest
import torch
from deterministic_ml._internal.deterministic import set_deterministic


@pytest.mark.parametrize(
    "seed, expected_sequence",
    [
        (0, [(864, 394), (684, 559), (44, 239)]),
        (42, [(654, 114), (102, 435), (542, 67)]),
    ],
)
def test_set_deterministic__random_sequence(seed, expected_sequence):
    set_deterministic(seed)

    int_range = 0, 1000

    sequence = [
        (
            random.randint(*int_range),
            random.randint(*int_range),
        ),
        (
            numpy.random.randint(*int_range),
            numpy.random.randint(*int_range),
        ),
        tuple(torch.randint(*int_range, (2,), dtype=torch.int).tolist()),
    ]
    assert sequence == expected_sequence
