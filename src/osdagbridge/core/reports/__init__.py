"""Reports package."""
from .report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportFigures,
    ReportPayload,
    ReportPayloadValidationError,
    ReportResult,
    LatexPreflightError,
    REPORT_SECTION_KEYS,
    build_report_payload,
    generate_report,
    preflight_latex,
)

__all__ = [
    "ReportMetadata", "ReportOptions", "ReportRequest",
    "ReportFigures", "ReportPayload", "ReportPayloadValidationError",
    "ReportResult", "REPORT_SECTION_KEYS",
    "LatexPreflightError", "preflight_latex",
    "build_report_payload", "generate_report",
]
