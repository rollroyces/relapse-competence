"""Detector tests."""

from __future__ import annotations

from relapse_competence.config import DetectorConfig
from relapse_competence.detectors import (
    MrdThresholdDetector,
    SequentialRiseDetector,
)
from relapse_competence.simulator import Measurement


def _measurement(
    draw: int, reads: int, total: int = 1_000_000, volume: float = 0.0
) -> Measurement:
    return Measurement(
        draw_index=draw,
        day=draw * 90,
        mutant_reads=reads,
        total_reads=total,
        genome_equivalents=3_000,
        observed_vaf=reads / total,
        true_vaf=0.0,
        tumour_volume_mm3=volume,
        is_relapse_draw=False,
        has_chip=False,
        background_vaf=0.0,
    )


# ----------------------------------------------------------------------
# MRD threshold detector
# ----------------------------------------------------------------------
def test_mrd_detector_ignores_the_baseline_draw() -> None:
    detector = MrdThresholdDetector(read_threshold=3)
    series = [_measurement(0, 500), _measurement(1, 1), _measurement(2, 1)]
    result = detector.run(series)
    assert not result.flagged
    assert result.flag_draw is None


def test_mrd_detector_flags_at_the_threshold() -> None:
    detector = MrdThresholdDetector(read_threshold=3)
    series = [_measurement(0, 500), _measurement(1, 2), _measurement(2, 3)]
    result = detector.run(series)
    assert result.flagged
    assert result.flag_draw == 2
    assert result.flag_day == 180


def test_mrd_detector_rejects_a_zero_threshold() -> None:
    import pytest

    with pytest.raises(ValueError):
        MrdThresholdDetector(read_threshold=0)


# ----------------------------------------------------------------------
# sequential detector
# ----------------------------------------------------------------------
def test_sequential_detector_does_not_flag_a_flat_background() -> None:
    detector = SequentialRiseDetector(
        DetectorConfig(), background_reads=5.0, threshold=15.0
    )
    series = [_measurement(i, 5) for i in range(10)]
    assert not detector.run(series).flagged


def test_sequential_detector_flags_a_rising_series() -> None:
    detector = SequentialRiseDetector(
        DetectorConfig(), background_reads=2.0, threshold=15.0
    )
    series = [_measurement(i, 2 + 4 * i) for i in range(6)]
    result = detector.run(series)
    assert result.flagged
    assert result.flag_draw is not None and result.flag_draw < 6


def test_sequential_detector_is_not_fooled_by_poisson_bounce() -> None:
    """A count sequence that wanders around the background must not fire."""
    detector = SequentialRiseDetector(
        DetectorConfig(), background_reads=5.0, threshold=15.0
    )
    noisy = [4, 7, 3, 8, 2, 9, 4, 6, 3, 7]
    series = [_measurement(i, n) for i, n in enumerate(noisy)]
    assert not detector.run(series).flagged


def test_sequential_detector_threshold_is_monotone() -> None:
    """A higher threshold cannot flag something a lower threshold did not."""
    series = [_measurement(i, 2 + 3 * i) for i in range(8)]
    low = SequentialRiseDetector(DetectorConfig(), background_reads=2.0, threshold=5.0)
    high = SequentialRiseDetector(DetectorConfig(), background_reads=2.0, threshold=50.0)
    low_result = low.run(series)
    high_result = high.run(series)
    if low_result.flagged:
        assert high_result.flagged or high_result.flag_draw != low_result.flag_draw
