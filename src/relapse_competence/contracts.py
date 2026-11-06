"""Fail-fast contracts.

Two distinct failure modes, deliberately not conflated:

``LayerDependencyError``
    A required dependency, dataset, or mode is unavailable. Raised at the
    *start* of a stage. Any degraded path must be opted into explicitly via
    an environment flag or an explicit argument -- never taken silently.

``LayerContractError``
    A stage ran but did not satisfy its output contract. Never overridable.
    This is always a bug, not a configuration choice.

The distinction matters for this project specifically: the predecessor
benchmark in another repository silently downgraded to a hard-coded
projection when an import failed, and published the projected numbers as a
validation result. See ``docs/ROADMAP.md`` for the write-up.
"""

from __future__ import annotations

import os
from typing import Final

ALLOW_PROJECTION_ENV: Final = "RELAPSE_COMPETENCE_ALLOW_PROJECTION"
"""Set to ``1`` to permit emitting projected (non-simulated) figures."""


class LayerDependencyError(RuntimeError):
    """A required dependency or mode is unavailable.

    The message should name the exact remediation, following the pattern
    already used elsewhere in this account's tooling.
    """


class LayerContractError(RuntimeError):
    """A stage violated its declared output contract. Always a bug."""


def projection_allowed() -> bool:
    """Whether emitting projected figures has been explicitly permitted."""
    return os.environ.get(ALLOW_PROJECTION_ENV, "").strip() in {"1", "true", "TRUE", "yes"}


def require(condition: bool, message: str) -> None:
    """Raise :class:`LayerContractError` when ``condition`` is false."""
    if not condition:
        raise LayerContractError(message)


def require_dependency(condition: bool, message: str) -> None:
    """Raise :class:`LayerDependencyError` when ``condition`` is false."""
    if not condition:
        raise LayerDependencyError(message)


def require_projection_permission() -> None:
    """Guard for any code path that would emit a projected rather than measured figure.

    Raises :class:`LayerDependencyError` unless the caller has explicitly set
    ``RELAPSE_COMPETENCE_ALLOW_PROJECTION=1``.
    """
    require_dependency(
        projection_allowed(),
        "Refusing to emit a projected figure. Either run the simulation, or set "
        f"{ALLOW_PROJECTION_ENV}=1 to acknowledge that the numbers are assumptions, "
        "not measurements.",
    )
