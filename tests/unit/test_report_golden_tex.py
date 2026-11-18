"""E6 — golden .tex regression cases (compare TEX only, never PDFs).

Each case builds a deterministic LaTeX fragment with fixed metadata /
relative figure paths and compares against tests/unit/golden/*.tex.

Regenerate goldens after an intentional change:
    UPDATE_GOLDEN=1 python -m pytest tests/unit/test_report_golden_tex.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from osdagbridge.core.reports import (
    ReportFigures,
    ReportMetadata,
    ReportOptions,
    ReportPayload,
)
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap6 import ch6_drawings
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.reports.report_generator import (
    ReportDataBridge,
    preamble,
    title_page,
)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def _assert_matches_golden(name: str, actual: str) -> None:
    """Write or compare a golden .tex file (normalized newlines)."""
    actual = actual.replace("\r\n", "\n")
    path = GOLDEN_DIR / name
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(
            f"missing golden {path} — run: "
            f"UPDATE_GOLDEN=1 python -m pytest tests/unit/test_report_golden_tex.py")
    expected = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert actual == expected, (
        f"golden mismatch: {name}\n"
        f"--- expected ({len(expected)} chars) ---\n{expected[:2000]}\n"
        f"--- actual ({len(actual)} chars) ---\n{actual[:2000]}"
    )


def _meta() -> ReportMetadata:
    return ReportMetadata(
        project_name="Golden Project",
        project_location="Mumbai",
        designer="Test Designer",
        client="FOSSEE",
        company="IIT Bombay",
        report_date="2026-01-01",
        job_number="JOB-001",
        subtitle="Rev 0",
    )


def test_golden_preamble():
    tex = preamble("Golden Project", "JOB-001", "2026-01-01", "Rev 0")
    _assert_matches_golden("preamble.tex", tex)


def test_golden_title_page():
    # Logos omitted so the golden stays independent of packaged image paths.
    tex = title_page(_meta(), osdag_logo=None, org_logo=None)
    _assert_matches_golden("title_page.tex", tex)


def test_golden_ch3_loads():
    # Minimal IRC live-load fixture: Class A + 70R wheeled, 20 m span.
    inputs = {
        "geometry.span": 20.0,
        "geometry.carriageway_width": 7.5,
        "typical_section.lane_details.lane_table_count": 2,
        "typical_section.no_of_footpaths": 1,
        "loading.live_load.irc.class_a": True,
        "loading.live_load.irc.70r_wheeled": True,
        "loading.live_load.footpath_pressure.mode": "IRC",
        "loading.live_load.footpath_pressure.value": 4.0,
        "loading.live_load.irc.aa_wheeled": False,
        "loading.live_load.irc.aa_tracked": False,
        "loading.live_load.irc.70r_tracked": False,
        "loading.live_load.irc.class_sv": False,
        "loading.live_load.irc.70r_bogie": False,
        "loading.live_load.irc.class_fatigue": False,
        "loading.live_load.custom_vehicles": None,
    }
    tex = ch3_loads(inputs)
    assert tex, "ch3_loads returned empty TEX"
    _assert_matches_golden("ch3_loads.tex", tex)


def test_golden_ch6_bridge_views():
    # Relative paths only — no /tmp absolute paths in goldens.
    fig_paths = {
        "bridge_elevation": "images/bridge_elevation.pdf",
        "bridge_isometric": "images/bridge_isometric.pdf",
    }
    tex = ch6_drawings(fig_paths)
    assert "bridge_elevation.pdf" in tex
    assert "bridge_isometric.pdf" in tex
    assert "Longitudinal Elevation" in tex
    assert "Isometric View" in tex
    _assert_matches_golden("ch6_bridge_views.tex", tex)


def test_golden_executive_summary():
    inputs = {
        "geometry.span": 20.0,
        "geometry.carriageway_width": 7.5,
        "typical_section.no_of_girders": 3,
        "typical_section.girder_spacing": 1.7167,
        "typical_section.deck_thickness": 250.0,
        "structural_steel.designation": "FE 500",
    }
    output = {}
    fig_paths = {}  # placeholders only — deterministic
    tex = executive_summary(inputs, output, fig_paths)
    assert tex, "executive_summary returned empty TEX"
    _assert_matches_golden("executive_summary.tex", tex)


def test_payload_validate_accepts_golden_shapes():
    """Smoke: payload built like the golden fixtures validates cleanly."""
    payload = ReportPayload(
        metadata=_meta(),
        options=ReportOptions(
            sections=["exec_summary", "loads", "analysis", "design_checks",
                      "drawings", "quantities", "references"],
            include_figures=True,
            include_toc=True,
            include_pdf=True,
        ),
        inputs={"geometry.span": 20.0},
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        log_entries=[],
        output_dict={},
        figure_data={"bridge_elevation": b"%PDF-1.4", "plan": None},
    )
    payload.validate()
