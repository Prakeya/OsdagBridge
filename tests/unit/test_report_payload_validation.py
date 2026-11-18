"""E6 — light structural validation for ReportPayload (stdlib dataclass)."""
import pytest

from osdagbridge.core.reports import (
    ReportFigures,
    ReportMetadata,
    ReportOptions,
    ReportPayload,
    ReportPayloadValidationError,
    REPORT_SECTION_KEYS,
)


def _meta():
    return ReportMetadata(
        project_name="Golden Bridge",
        project_location="",
        designer="",
        client="",
        company="",
        report_date="2026-01-01",
    )


def _opts(sections=None):
    return ReportOptions(
        sections=sections if sections is not None else ["loads", "analysis"],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )


def _payload(**overrides):
    base = dict(
        metadata=_meta(),
        options=_opts(),
        inputs={"geometry.span": 20.0},
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        log_entries=[],
        output_dict={},
        figure_data={},
    )
    base.update(overrides)
    return ReportPayload(**base)


def test_valid_payload_passes():
    _payload().validate()  # must not raise


def test_empty_project_name_rejected():
    p = _payload(metadata=ReportMetadata(
        project_name="  ", project_location="", designer="",
        client="", company=""))
    with pytest.raises(ReportPayloadValidationError) as ei:
        p.validate()
    assert "project_name" in str(ei.value)


def test_empty_sections_rejected():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(options=_opts(sections=[])).validate()
    assert "options.sections" in str(ei.value)


def test_unknown_section_key_rejected():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(options=_opts(sections=["loads", "no_such_section"])).validate()
    assert "no_such_section" in str(ei.value)


def test_non_string_section_rejected():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(options=_opts(sections=["loads", 42])).validate()
    assert "non-string" in str(ei.value)


def test_wrong_types_rejected():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(inputs="not-a-dict").validate()
    msg = str(ei.value)
    assert "inputs" in msg
    assert "dict" in msg


def test_figure_data_must_be_bytes():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(figure_data={"plan": "not-bytes"}).validate()
    assert "figure_data" in str(ei.value)


def test_figure_data_none_is_allowed():
    _payload(figure_data={"plan": None}).validate()


def test_all_reported_errors_collected():
    with pytest.raises(ReportPayloadValidationError) as ei:
        _payload(
            metadata=ReportMetadata(
                project_name="", project_location="", designer="",
                client="", company=""),
            options=_opts(sections=["bogus"]),
            inputs=[1, 2],
        ).validate()
    msg = str(ei.value)
    assert "project_name" in msg
    assert "bogus" in msg
    assert "inputs" in msg


def test_report_section_keys_match_harness_contract():
    # tools/regen_report.py ALL_SECTIONS must stay in sync with REPORT_SECTION_KEYS.
    assert "loads" in REPORT_SECTION_KEYS
    assert "design_checks" in REPORT_SECTION_KEYS
    assert "drawings" in REPORT_SECTION_KEYS
