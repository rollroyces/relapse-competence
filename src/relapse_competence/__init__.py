"""relapse-competence.

Longitudinal cfDNA modelling for the relapse-competent state, with an
executable evidence chain.

The package is deliberately small. It contains:

* a ground-truth simulator that reproduces the Poisson floor of ctDNA detection
  instead of assuming it away (:mod:`relapse_competence.simulator`);
* two detectors matched to the two clinical regimes
  (:mod:`relapse_competence.detectors`);
* a benchmark engine with held-out threshold selection
  (:mod:`relapse_competence.benchmark`);
* fail-fast contracts and a mode stamp on every result
  (:mod:`relapse_competence.contracts`, :mod:`relapse_competence.report`).

Research and education use only. Not a clinical assay, not a medical device.
"""

from __future__ import annotations

from .config import DetectorConfig, PatientArm, Regime, SimulationConfig
from .contracts import LayerContractError, LayerDependencyError
from .detectors import DetectorResult, MrdThresholdDetector, SequentialRiseDetector
from .simulator import LongitudinalSimulator, Measurement, PatientTrajectory

__version__ = "0.1.0"

__all__ = [
    "DetectorConfig",
    "DetectorResult",
    "LayerContractError",
    "LayerDependencyError",
    "LongitudinalSimulator",
    "Measurement",
    "MrdThresholdDetector",
    "PatientArm",
    "PatientTrajectory",
    "Regime",
    "SequentialRiseDetector",
    "SimulationConfig",
    "__version__",
]
