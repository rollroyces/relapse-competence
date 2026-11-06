"""Contract and calibration tests.

These encode the two rules that matter most in this project:

* a projected figure cannot be emitted without an explicit opt-in;
* every calibration constant carries a source.
"""

from __future__ import annotations

import os

import pytest

from relapse_competence.calibration import ALL_ANCHORS, calibration_provenance
from relapse_competence.config import SimulationConfig
from relapse_competence.contracts import (
    ALLOW_PROJECTION_ENV,
    LayerContractError,
    LayerDependencyError,
    require,
    require_dependency,
    require_projection_permission,
)
from relapse_competence.report import build_report


def test_every_anchor_has_a_source() -> None:
    for anchor in ALL_ANCHORS:
        assert anchor.source.strip(), f"anchor {anchor.key} has no source"
        assert anchor.value == anchor.value  # not NaN


def test_anchor_keys_are_unique() -> None:
    keys = [a.key for a in ALL_ANCHORS]
    assert len(keys) == len(set(keys))


def test_calibration_provenance_is_json_serialisable() -> None:
    import json

    payload = calibration_provenance()
    assert payload
    json.dumps(payload)


def test_require_raises_contract_error() -> None:
    with pytest.raises(LayerContractError):
        require(False, "boom")
    require(True, "fine")


def test_require_dependency_raises_dependency_error() -> None:
    with pytest.raises(LayerDependencyError):
        require_dependency(False, "missing")
    require_dependency(True, "fine")


def test_projection_requires_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ALLOW_PROJECTION_ENV, raising=False)
    with pytest.raises(LayerDependencyError):
        require_projection_permission()

    monkeypatch.setenv(ALLOW_PROJECTION_ENV, "1")
    require_projection_permission()


def test_build_report_refuses_projected_without_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ALLOW_PROJECTION_ENV, raising=False)
    config = SimulationConfig()
    with pytest.raises(LayerDependencyError):
        build_report(mode="projected", config=config, payload={"x": 1}, claim_scope="s")


def test_build_report_refuses_empty_payload() -> None:
    config = SimulationConfig()
    with pytest.raises(LayerContractError):
        build_report(mode="simulated", config=config, payload={}, claim_scope="s")


def test_build_report_stamps_mode_and_provenance() -> None:
    config = SimulationConfig()
    report = build_report(
        mode="simulated",
        config=config,
        payload={"x": 1},
        claim_scope="test",
    )
    assert report["metadata"]["mode"] == "simulated"
    assert report["results"] == {"x": 1}
    assert report["calibration"]
    assert "config" in report
    assert os.path.basename(report["metadata"]["generated_at"]) != ""
