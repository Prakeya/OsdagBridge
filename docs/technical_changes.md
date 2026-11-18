# Technical Changes — Report Generator Enhancements

Branch: `feature/report-generator-enhancements` (vs. `d74f56d fix: Z,Sa/g,Ah,Av in Report`)
Scope: R1–R6 (commit `9b054d0`) + extras E1–E7 (uncommitted until handover).
LaTeX emitted at runtime; all changes are Python + tests + docs.

## 1. How to reproduce / verify

```bash
# full report build (headless, no GUI): writes Report_<label>.pdf/.tex
conda run -n osdagbridge-env python tools/regen_report.py --label After --no-cache

# dynamism proof: second build with a different vehicle selection
conda run -n osdagbridge-env python tools/regen_report.py \
    --inputs baseline_70r.osi --label after_r3b_70r --no-cache
```

Notes:
- `pdflatex` is not on PATH; `report_generator.py` uses the bundled TeX Live 2025
  (`osdag_latex_env`, `report_generator.py:841-853`).
- `--inputs <path>` selects any OSi file; cache is per-OSI
  (`.report_cache.pkl`, `.report_cache_<stem>.pkl`) — the cache stores the raw
  tuple `(inputs, output_dict, log_entries)` with **no input-key validation**, so a
  custom OSi must not reuse the default slot.
- Deliverable PDFs: `Report_Before.pdf` (43 pp, GUI baseline run — no `.tex`
  captured) and `Report_After.pdf` (45 pp, final build, `.tex` kept alongside).

## 2. Requirement status

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| R1 | Repeating headers on all tables (`\endfirsthead`/`\endhead`) | Done, verified | `evidence/r1_before_tbl3_7_bare_continuation.png`, `evidence/r1_after_tbl3_7_header_repeat.png`, `evidence/r1_before_tbl5_1_mangled.png`, `evidence/r1_after_tbl5_1_clean.png` |
| R2 | Fix multirow label sitting on the footer rule (G3) | Done, verified | `evidence/r2_before_g3_on_footer.png`, `evidence/r2_after_g3_on_row.png` |
| R3 | Split Ch.3 loading table (vehicle actions vs footpath) + show dynamism | Done, verified | `evidence/r3_table3_70r_only.png`, `evidence/r3_table3_8_vehicles.png` |
| R4 | Chart on p36 (UR) + caption "Table 5.22" → "Table 5.29" | Done, verified | `evidence/r4_ur_chart_caption_5_22.png`, `evidence/r4_ur_chart_caption_5_29_fixed.png` |
| R5 | Material charts in Ch.7 (steel breakdown, concrete vs rebar) + ED in BOQ | Done, verified | `evidence/r5_chapter7_charts.png`, `evidence/r5_after_ch7_ed_row.png`, `evidence/r5_before_ch7_no_charts.png` |
| R6 | Single source of truth for styles (`styles.py`) | Done, verified | regen output byte-identical to baseline; 0 style literals outside `styles.py` |
| — | Table 2.7 units (values were metres, labelled mm) | Done, verified | `evidence/fix_before_units_1_12mm.png`, `evidence/fix_after_units_1120mm.png` |
| — | Executive summary must report computed outcomes (not hardcoded "pass") | Done, verified | `evidence/fix_before_exec_hardcoded_pass.png`, `evidence/fix_after_exec_computed.png` |
| E1 | PASS/FAIL cellcolor badges in Ch.5 status columns | Done, verified | `evidence/e1_*.png` |
| E2 | Reference / clause column in Ch.5 check tables | Done, verified | `evidence/e2_*.png` |
| E3 | Vector PDF charts (no raster PNGs) | Done, verified | `evidence/e3_vector_charts_pdfimages.txt` |
| E4 | Governing load-combination column on demand/UR rows | Done, verified | `evidence/e4_after_tbl5_{3,4,5,6}_governing_lc.png`, `e4_governing_lc_verification.txt` |
| E7 | Pre-flight LaTeX diagnostic (fail fast, actionable) | Done, verified | `evidence/e7_preflight_verification.txt` |
| E5 | 2D elevation + isometric static vector figures side-by-side; no media9/U3D | Done, verified | `evidence/e5_after_side_by_side_pair.png`, `e5_vector_views_verification.txt` |
| E6 | Light `ReportPayload` validation + `tests/unit/` golden `.tex` | Done, verified | `evidence/e6_payload_validation_golden_tex.txt`, `tests/unit/golden/*.tex` |

Evidence PNGs are 100-dpi renders of the delivered PDFs, in `docs/evidence/`.
E1–E7 implementation details: section 7 below.

## 3. Per-requirement implementation

### R1 — repeating table headers
All generated tables use the `longtable` header pattern:

```latex
\endfirsthead   % header on first page of table
\endhead        % header repeated on every continuation page
```

50/50 tables in the final `.tex` contain both, including the Ch.7 BOQ table
(Table 7.1). Pure insertion — no table content was modified.
Focus cases: Table 3.7/3.8 (load combinations) and Table 5.1 (girder section
properties). Before: continuation page starts mid-table with a blank girder
column; After: `Girder | Property | Value` header repeats and the `G3` multirow
label is beside its own group.

### R2 — G3 multirow vs. footer rule
The defect only manifests when R1 headers + data multirow are combined (true
only from the R1 build onward), so before/after is proven across builds:
`Report_after_r1.pdf` p21 (G3 drawn on the green footer rule) vs
`Report_After.pdf` p21 (G3 beside "Elastic Critical Moment").
Fix in `chap5.py`: 15 data multirow labels (UR summary etc.) were replaced with
plain `\makecell` label-on-first-row. Footer-band scan: 0 hits in the final
build; p29–31 sweep also clean.

### R3 — loading table split + dynamism
`chap3.py` now emits two tables:
- **Vehicle Actions (per IRC 6)** — one row per vehicle class with columns:
  vehicle class / impact factor / braking / centrifugal.
  Per-vehicle impact factor from `_impact_cell()` (`chap3.py:97`):
  Class A → `1+Cl.208.2`, 70R/AA/SV → `1+Cl.208.3`, Fatigue → `---`,
  custom → N/A. Braking is lane-based (108.69 kN for all rows); centrifugal is
  `N/A (straight alignment)` (engine fix retained from earlier).
- **Footpath (IRC 6 Cl. 206)** — no. of footpaths + footpath live load.

The old prose strings `vehicles_str`/`impact_factor_str` were removed.
Table numbers after Ch.3 shifted (Wind 3.4→3.5, Load Combinations 3.7→3.8, …);
no `\label`/`\ref` for tables exists, so no references broke.

Dynamism proof (two independent fresh builds):
- `Report_after_r3b.pdf` — default inputs → **8 vehicle rows**.
- `Report_after_r3b_70r.pdf` (`--inputs baseline_70r.osi`, only `70r_wheeled: true`)
  → **1 row** (`Class 70R (Wheeled)`, impact 1.100) and only 11.2 s.

### R4 — UR chart + caption fix
Chart row for the UR plot (§5.5) is emitted on p36 (`Girder 1.32` visible).
Stale caption string `Table 5.22` → `Table 5.29` in 4 places
(`chap5.py:862,1691,1702,1785`; Table 5.22 = Reinforcement Detailing).
Diff vs. the previous build: exactly 10 added lines (chart row only).

### R5 — material charts + ED in BOQ
- `report_utils.py` — `_mt_bar_png()` (`:167`) and
  `build_material_charts_pngs()` (`:213`) render two PNGs from
  `calculate_material_quantities()` using the non-pyplot backend
  (`matplotlib.figure.Figure` + `FigureCanvasAgg`):
  - Steel: Girders 7.34 / Cross bracing 0.17 / End diaphragm 0.10 / Shear studs 0.10 MT
  - Deck: Concrete 64.38 / Rebar 3.09 MT (concrete excluded from steel by design)
- `report_generator.py` — quantities are computed before the temp figure loop so
  both charts join `payload.figure_data` in the same pass; written to
  `tmp_dir/images/` **before** `ch7_quantities(payload.inputs, fig_paths)` runs.
- `chap7.py` — `ch7_quantities(input_dict, fig_paths=None)`; two `_fig_embed`
  calls after Table 7.1 (`0.8\textwidth`).
- BOQ row **2(d) End Diaphragm – Members**: new `steel_ed_*` keys computed in
  `boq_generator.py` (mass 15.04 kg/m × spacing 1.7167 m × 4 members →
  single 0.0258 MT, total 0.10 MT; volume via mass/7850), rendered by
  `chap7.py:32`.

### R6 — style single source of truth
All colour/font/spacing/column-type literals live in `reports/styles.py`
(imported by `report_generator.py:122`).
Regenerating without any code change produced a byte-identical `.tex` to the
GUI baseline; grep confirms zero style literals outside `styles.py`.

## 4. Additional fixes found during review

1. **Table 2.7 units** — dimensions were metres formatted to 3 dp but labelled mm
   (`1.12 mm`). `_dim_row` in `chap2.py:257` now multiplies by 1000
   (`1120 mm & 8 mm & 340 mm, 16 mm`).
2. **Executive summary outcomes** — `executive_summary.py` hardcoded
   `"Girder design pass"` even for failing designs. Replaced with computed
   `_outcome()`/`girder_outcome` (`:182-192`) driven by member efficiencies;
   worst-case failures now reported (e.g. "Girder design fail (Fatigue Normal
   Stress)").
3. **`defaults.py` stomping explicit `False`** —
   `_update_loading_tab_defaults` (`defaults.py:260`) overwrote keys that were
   explicitly set (e.g. `loading.live_load.irc.70r_wheeled: false` became `true`
   on every re-solve), contradicting its own "fill keys that are None" contract.
   The local `_update` helper now uses a None-guard. Proof of no regression:
   fresh baseline build still returns all 8 vehicle flags `True`; 70R-only build
   keeps `70r_wheeled: true`, others `false`.
4. **Harness cache correctness** — `tools/regen_report.py` gained `--inputs`,
   `run_design(inputs_path)`, `load_cache/save_cache(cache_path)` and per-OSI
   cache slots, because the cache never validates that cached inputs match the
   requested file.

## 5. Reported issues NOT reproducible in the final build

| Claim | Verification performed | Result |
|---|---|---|
| Table 5.29 note shows mangled LaTeX (e.g. unclosed `$`) | Inspected source (`chap5.py`), the generated `Report_After.tex`, and `pdftotext -raw/-layout/-table` of the final PDF, plus a 100-dpi visual render of p36 | Clean in all four — no mangled output present |
| `一` (CJK em dash) glyph appears in the report | Searched every `.py` source and both final PDFs; rendered every page at 100 dpi | Present only in stale `__pycache__/chap5.cpython-312*.pyc` (old bytecode); current sources and PDFs render a normal em dash — |

## 6. Known limitations / not addressed

- **Ch.6 `[PLACEHOLDER: …]` figures** (13 CAD-only views): the headless run has
  no CAD session. E5 added always-on static vector elevation + isometric
  (Figures 6.1–6.2); the remaining 13 placeholders fill when the GUI exports
  figures into `payload.figure_data`. PLACEHOLDER list is byte-identical
  E4→E5→E6.
- **Footer page count off-by-one**: footers show `Page n of N` where `N` is one
  less than the physical page count (pre-existing on the baseline, unchanged).
- **141 manual-compile pdflatex errors** (baseline, unchanged through E1–E7):
  47× `Misplaced \noalign` + 47× `Misplaced \omit` + 47× `Extra alignment tab`.
  The bundled compiler used by `generate_report` still produces a valid PDF.
- **Table numbering shifts** in Ch.3 (consequence of the required split); no
  cross-references exist, so nothing broke.
- Historical mangled row in old Table 5.1 renders (`r1_before_tbl5_1_mangled.png`)
  is preserved deliberately as the defect evidence.

## 7. Extras E1–E7 (user checklist)

Order of completion: **E1 → E2 → E3 → E4 → E7 → E5 → E6** (E7 pulled ahead of
E5; all seven verified before this doc update).

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| E1 | PASS/FAIL cellcolor badges in Ch.5 status columns | Done, verified | `evidence/e1_*.png` |
| E2 | Reference / clause column in Ch.5 check tables | Done, verified | `evidence/e2_*.png` |
| E3 | Vector PDF charts (no raster PNGs) | Done, verified | `evidence/e3_vector_charts_pdfimages.txt` |
| E4 | Governing load-combination column on demand/UR rows | Done, verified | `evidence/e4_after_tbl5_{3,4,5,6}_governing_lc.png`, `e4_governing_lc_verification.txt` |
| E7 | Pre-flight LaTeX diagnostic (fail fast, actionable) | Done, verified | `evidence/e7_preflight_verification.txt` |
| E5 | 2D elevation + isometric static vector figures side-by-side; no media9/U3D | Done, verified | `evidence/e5_after_side_by_side_pair.png`, `e5_vector_views_verification.txt` |
| E6 | Light `ReportPayload` validation + `tests/unit/` golden `.tex` | Done, verified | `evidence/e6_payload_validation_golden_tex.txt`, `tests/unit/golden/*.tex` |

### E1 — PASS/FAIL badges
`styles.py`: `COLOR_SAFE`/`COLOR_UNSAFE`/`COLOR_BADGE_DEFS`/`status_cell`/`ur_cell`.
`chap5.py::_badge_status()` colours `PASS` green, `FAIL` red; `WARN`/`N/A`
pass through uncoloured. Neutral statuses intentionally uncoloured.

### E2 — Reference column
`styles.py`: `CLAUSE_REFS` dict + `clause_ref()` helper. ~20 Ch.5 tables gained
a `Reference` column (spec widths, `tabcolsep` tightened, per-cell `footnotesize`).
Deck flexure kept `---` (clause not traceable to a single engine check id).
Clause strings verified against the engine-emitted text for each check id.

### E3 — vector charts
`styles.CHART_FORMAT = "pdf"`; `_fig_bytes()` helper; renamed
`build_ur_chart`/`build_material_charts` (drop the old `_png` suffix).
Writer uses `attr + '.' + styles.CHART_FORMAT`. `pdfimages -list` on the
delivered PDF shows only the title-page logo raster — charts are vector XObjects.

### E4 — Governing LC column
`chap5.py`: helper `_gov_lc(check_ids, girder=None, label_contains=None)`
(~line 250) resolves the governing combination from
`design_results.per_lc` / per-girder check entries (keys are `id`, not
`check_id`). Demand/UR rows of Tables 5.3–5.6 carry a 7th column
`Governing LC (ULS)`; capacity/property rows show `---`.
Governing LCs observed: flexure `{1}` / shear `{2}` / interaction `{3,4}` →
`ACCIDENTAL_1: 1.0DL + 1.0DW + 0.75LL`; LTB `{5}` + label contains
"Construction" → `1.0 DL` (check id 5 is shared by two LTB variants — label
filter required). `_gov_lc_in_522` delegates to `_gov_lc` so Table 5.29 rows
stay byte-identical (regression check).
Four longtable specs widened to 7 columns; max new overfull on those tables
42.36 pt (< 47.8 pt off-paper limit).

### E7 — pre-flight diagnostic
`report_generator.py`: `LatexPreflightError`, `_required_sty_packages()`
(regex-parses `preamble()`, 24 packages, cannot drift), `preflight_latex(compiler)`
checks binary (`isfile`+`X_OK` or `which`) then `kpsewhich` (sibling of
compiler, then PATH; if `kpsewhich` absent the package scan is skipped rather
than false-positive). Called in `generate_report` right after
`logger.info("Compiler: …")`, before `os.makedirs`. On failure returns
`ReportResult(pdf_path=None, tex_path=None, error=…)` with a multi-line
actionable message ("Fix: install TeX Live/MiKTeX…" / "tlmgr install …").
UI failure dialog (`template_page.py`) prefers `result.error` over the generic
causes text. No bundler fallback — never auto-installs.

### E5 — elevation + isometric (static vector)
`report_utils.py`: `_bridge_geometry()` (span, girder count/spacing/overhang,
girder depth from `steeldesign.details.total_depth` (mm→m) or section input,
deck thickness mm→m, transverse bracing stations ~every 10 m),
`_draw_elevation()` (2D side view: deck slab, girder silhouette, bracing
markers, support triangles, span/height dimensions),
`_draw_isometric()` (3D wireframe: deck outline, girder chords, bracing
frames, supports; `view_init(elev=22, azim=-58)`),
`build_bridge_views()` → `{"bridge_elevation": PDF bytes,
"bridge_isometric": PDF bytes}` via `matplotlib.figure.Figure` (no pyplot,
backend-independent, same pattern as `build_ur_chart`).
`report_generator.generate_report` fills these keys only if absent (CAD may
supply its own). `chap6.py::_sec_cell` gained a `width` parameter (default
`0.31\textwidth` preserved for the 3-column CB/ED rows); `elev_iso_row` places
the pair at `0.48\textwidth` + `\hfill` as Figures 6.1–6.2 in §6.1.
Verified: 0 `media9`/`U3D`/`/3D` in both `.tex` and `.pdf` bytes;
`pdfimages -list` shows only the title-page logo (charts/views are vector);
page 43 renders the pair side-by-side; no overfull in the minipage region.

### E6 — payload validation + golden TEX
`ReportPayloadValidationError(ValueError)` + `REPORT_SECTION_KEYS` (11 keys —
matches UI `report_options._REPORT_CHAPTERS` and harness `ALL_SECTIONS`).
`ReportPayload.validate()` (stdlib dataclass, **not** Pydantic) collects every
failed check into one message: non-empty `project_name`; non-empty
`options.sections` of known string keys; `include_*` are bool; `inputs` /
`analysis_summary` / `output_dict` are dict; `design_checks` / `log_entries`
are list; `figures` is `ReportFigures`; `figure_data` values are `bytes|None`.
`generate_report` calls `payload.validate()` first; a validation failure
returns `ReportResult(error=…)` without assembling any document.
`tests/unit/test_report_payload_validation.py` (10 cases) +
`tests/unit/test_report_golden_tex.py` (6 cases; 5 golden `.tex` files under
`tests/unit/golden/`: `preamble`, `title_page`, `ch3_loads`,
`ch6_bridge_views`, `executive_summary`). Goldens compare `.tex` only, never
PDFs; regenerate with `UPDATE_GOLDEN=1 python -m pytest
tests/unit/test_report_golden_tex.py`.

```bash
conda run -n osdagbridge-env pytest tests/unit -q
# 19 passed
```

## 8. Pre-existing defects (documented, not fixed)

| Defect | Notes |
|--------|-------|
| Footer off-by-one | `Page N-1 of M-1` on every page; present on the baseline |
| 141 pdflatex errors on manual compile | 47× each of `Misplaced \noalign`, `Misplaced \omit`, `Extra alignment tab`; bundled compiler still emits a valid PDF |
| 442 pt overfull | Ch.4 `fbox` figure box |
| 51.05 / 48.20 pt overfull ×3 each | Ch.2 girder property tables |
| 50.94 pt overfull | Ch.10 IS-codes table |
| 13 Ch.6 PLACEHOLDER figures | CAD-only views; fill from the GUI |
| "Note: 3. Limit" artefact | Cosmetic string in Ch.3 |

## 9. Deferred future work

- Pydantic migration of the report payload/options dataclasses
- Branding: logo/stamp placement beyond the current title-page logos
- i18n of report strings
- CI wiring for `pytest tests/unit`
- Zip-export fallback for the compiled report
- Interactive 3D PDF (would require media9/U3D — explicitly out of scope for E5)

## 10. Deliverables

- `Report_Before.pdf` (43 pp) — untouched baseline (GUI run).
- `Report_After.pdf` (45 pp) — R1–R6 final build.
- `Report_E1.pdf` … `Report_E6.pdf` — per-extras incremental builds
  (E6 is the cumulative deliverable: 51 pp).
- `docs/evidence/*` — before/after renders + verification `.txt` for R1–R6 and E1–E7.
- `tests/unit/` — payload validation + golden `.tex` suite (E6).
- This document: `docs/technical_changes.md`.
