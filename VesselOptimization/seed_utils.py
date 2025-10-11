"""
Centralized random seeding utilities to guarantee deterministic behavior across
our optimization pipeline. Use `set_global_seed` before running any algorithm to
ensure reproducibility for identical datasets and configuration.
"""
from __future__ import annotations

import os
import random
from typing import Optional

import numpy as np

DEFAULT_SEED = 2025
_CURRENT_SEED = DEFAULT_SEED
_ENV_KEYS = ("LOGISTICS_RANDOM_SEED", "LOGISTICS_SEED", "GLOBAL_SEED")


def _coerce_seed(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _seed_from_environment() -> Optional[int]:
    for key in _ENV_KEYS:
        env_value = os.getenv(key)
        if env_value is not None:
            coerced = _coerce_seed(env_value)
            if coerced is not None:
                return coerced
    return None


def resolve_seed(seed: Optional[int] = None) -> int:
    """Resolve the seed to use, checking explicit arg, env vars, then default."""
    candidate = _coerce_seed(seed)
    if candidate is not None:
        return candidate

    env_seed = _seed_from_environment()
    if env_seed is not None:
        return env_seed

    return DEFAULT_SEED


def set_global_seed(seed: Optional[int] = None, *, quiet: bool = True) -> int:
    """Seed Python, NumPy, and related randomness sources.

    Args:
        seed: Optional override. If not provided, environment variables are
            inspected before falling back to `DEFAULT_SEED`.
        quiet: When False, emit a console message noting the active seed.

    Returns:
        The integer seed that was ultimately applied.
    """
    global _CURRENT_SEED

    resolved = resolve_seed(seed)
    random.seed(resolved)
    np.random.seed(resolved)

    # Setting PYTHONHASHSEED post-start does not change the active interpreter
    # state, but we persist it so child processes (if any) inherit the value.
    os.environ["PYTHONHASHSEED"] = str(resolved)

    _CURRENT_SEED = resolved

    if not quiet:
        print(f"[seed] Global RNG seeded with {resolved}")

    return resolved


def get_current_seed() -> int:
    """Return the most recently applied global seed."""
    return _CURRENT_SEED


def reseed_for_phase(phase: str, *, offset: int = 0, quiet: bool = True) -> int:
    """Derive a deterministic seed for a named phase and apply it.

    This helps keep different pipeline stages separated while still being
    reproducible. For example, `reseed_for_phase("simulation")` keeps the
    simulation RNG sequence stable without interfering with optimization.
    """
    base = get_current_seed()
    derived = (abs(hash((phase, base))) + offset) % (2 ** 32)
    return set_global_seed(derived, quiet=quiet)


__all__ = [
    "DEFAULT_SEED",
    "get_current_seed",
    "resolve_seed",
    "reseed_for_phase",
    "set_global_seed",
]
