"""
ml/src/utils/seed.py
Deterministic seed configuration for FlowShield ML reproducibility.
"""

import os
import random
import numpy as np

DEFAULT_RANDOM_SEED: int = 26192  # Smart India Hackathon 2026 problem statement ID


def set_seed(seed: int = DEFAULT_RANDOM_SEED) -> None:
    """Sets random seed across standard library, numpy, and python hash seed."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
