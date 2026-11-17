#!/usr/bin/env python
"""Headless report regeneration harness (dev tool).

Regenerates the OsdagBridge design report PDF without launching the GUI,
so requirement changes can be verified in a compiled PDF with one command.

Flow:
  1. Load baseline_inputs.osi  (flat YAML dict saved from the GUI)
  2. solve_extend_basic_input_dict()  (same pre-design step the GUI runs)
  3. First run:  PlateGirderBridge().set_input()/design()  -> cache results
     Later runs: reuse tools/.report_cache.pkl  (skip analysis entirely)
  4. build_report_payload() + generate_report()  -> Report_<label>.pdf/.tex

Usage:
  python tools/regen_report.py --label after_r6
  python tools/regen_report.py --label fresh --no-cache   # force re-analysis

Notes:
  - figure_data is empty: chapters render placeholder boxes instead of CAD
    figures.  A/B comparisons must use this harness on BOTH branches so
    conditions match.
  - design-log entries are cached too, so Chapter 8 is identical between
    a fresh-design run and a cached run.
"""

import argparse
import os
import pickle
import sys
import time

# Headless matplotlib before anything imports it (design pipeline may plot).
os.environ.setdefault("MPLBACKEND", "Agg")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

CACHE_PATH = os.path.join(REPO, "tools", ".report_cache.pkl")
OSI_PATH = os.path.join(REPO, "baseline_inputs.osi")

# All chapter keys from ReportOptionsDialog._REPORT_CHAPTERS (all ticked).
ALL_SECTIONS = [
    "exec_summary",
    "project_info",
    "input_parameters",
    "loads",
    "analysis",
    "design_checks",
    "drawings",
    "quantities",
    "standards",
    "design_log_window",
    "references",
]


def run_design(inputs_path=OSI_PATH):
    """Execute the full analysis/design pipeline headlessly.

    Returns (post_design_inputs, output_dict, success_log_entries).
    Mirrors PlateGirderBridge.generate_design_report() preparation:
      - input_dict snapshot after design
      - output_dict with injected 'analysis_summary' (Ch.4 tables)
    """
    import yaml

    from osdagbridge.core.bridge_types.plate_girder.defaults import (
        solve_extend_basic_input_dict,
    )
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
        PlateGirderBridge,
    )
    from osdagbridge.core.utils.logger import bridge_logger

    with open(inputs_path, "r", encoding="utf-8") as fh:
        inputs = yaml.safe_load(fh)
    if not isinstance(inputs, dict):
        raise SystemExit(f"OSI file is not a dict: {inputs_path}")

    # Same pre-design layout solve the GUI performs.
    solve_extend_basic_input_dict(inputs)

    print(f"[harness] running design from {inputs_path} ...", flush=True)
    t0 = time.time()
    bridge = PlateGirderBridge()
    bridge.set_input(inputs)
    bridge.design()
    elapsed = time.time() - t0
    print(f"[harness] design finished in {elapsed:.1f}s", flush=True)

    post_inputs = dict(bridge.input_dict)
    output_dict = dict(bridge.output_dict)  # MappingProxyType -> dict

    # Replicate generate_design_report()'s Ch.4 injection
    # (plategirderbridge.py:976-983).
    lc_sum = getattr(bridge, "_lc_summary", None)
    rxn_sum = getattr(bridge, "_reaction_summary", None)
    if lc_sum is not None or rxn_sum is not None:
        output_dict["analysis_summary"] = {
            "load_cases": lc_sum or {},
            "reactions": rxn_sum or {},
        }

    # Capture Ch.8 design-log lines while the logger still holds them.
    log_entries = bridge_logger.get_success_log()
    return post_inputs, output_dict, log_entries


def load_cache(cache_path):
    with open(cache_path, "rb") as fh:
        return pickle.load(fh)


def save_cache(payload_tuple, cache_path):
    with open(cache_path, "wb") as fh:
        pickle.dump(payload_tuple, fh, protocol=pickle.HIGHEST_PROTOCOL)


def regen(label, use_cache=True, project_name="OsdagBridge", inputs_path=OSI_PATH):
    # A non-default OSI gets its own cache slot so runs with different
    # inputs can never poison the baseline cache (it has no key check).
    if os.path.abspath(inputs_path) == os.path.abspath(OSI_PATH):
        cache_path = CACHE_PATH
    else:
        stem = os.path.splitext(os.path.basename(inputs_path))[0]
        cache_path = os.path.join(REPO, "tools", f".report_cache_{stem}.pkl")

    if use_cache and os.path.exists(cache_path):
        inputs, output_dict, log_entries = load_cache(cache_path)
        print(f"[harness] cache hit: {cache_path}", flush=True)
    else:
        inputs, output_dict, log_entries = run_design(inputs_path)
        try:
            save_cache((inputs, output_dict, log_entries), cache_path)
            print(f"[harness] cache written: {cache_path}", flush=True)
        except Exception as exc:  # non-picklable values — not fatal
            print(f"[harness] WARNING: cache write failed ({exc}); "
                  f"next run will re-analyze", flush=True)

    from osdagbridge.core.reports.report_generator import (
        ReportMetadata,
        ReportOptions,
        ReportRequest,
        build_report_payload,
        generate_report,
    )

    request = ReportRequest(
        metadata=ReportMetadata(
            project_name=project_name,
            project_location="",
            designer="",
            client="",
            company="",
        ),
        options=ReportOptions(
            sections=list(ALL_SECTIONS),
            include_figures=True,
            include_toc=True,
            include_pdf=True,
        ),
        output_dir=REPO,
        file_stem=f"Report_{label}",
    )

    # Fresh copies: generate_report mutates inputs (quantity injection).
    payload = build_report_payload(request, dict(inputs), dict(output_dict))
    # Deterministic Chapter 8 whether or not design ran in this process.
    payload.log_entries = list(log_entries)
    payload.figure_data = {}

    result = generate_report(payload, request)
    if not result.pdf_path or not os.path.exists(result.pdf_path):
        raise SystemExit(f"[harness] FAILED: no PDF at {result.pdf_path}")
    print(f"[harness] PDF : {result.pdf_path}", flush=True)
    print(f"[harness] TEX : {result.tex_path}", flush=True)
    return result


def main():
    ap = argparse.ArgumentParser(description="Headless OsdagBridge report regen")
    ap.add_argument("--label", required=True,
                    help="output stem: Report_<label>.pdf/.tex (repo root)")
    ap.add_argument("--no-cache", action="store_true",
                    help="force a fresh analysis/design run")
    ap.add_argument("--project-name", default="OsdagBridge",
                    help="header project name (keep constant for A/B diffs)")
    ap.add_argument("--inputs", default=OSI_PATH,
                    help="OSI inputs file (default: baseline_inputs.osi; "
                         "custom files get their own cache slot)")
    args = ap.parse_args()

    regen(args.label, use_cache=not args.no_cache,
          project_name=args.project_name, inputs_path=args.inputs)


if __name__ == "__main__":
    main()
