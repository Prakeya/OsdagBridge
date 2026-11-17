# Technical Changes — Report Generator Enhancements

Branch: `feature/report-generator-enhancements` (vs. `d74f56d fix: Z,Sa/g,Ah,Av in Report`)
Scope: `12 files changed, +814 / −203` (all Python; LaTeX emitted at runtime).

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

All 17 evidence PNGs are 100-dpi renders of the delivered PDFs, in `docs/evidence/`.

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

- **Ch.6 `[PLACEHOLDER: …]` figures**: the headless run has no CAD session, so
  generated-section/cross-section figures are placeholders. Regenerating from
  the GUI (which exports figures into `payload.figure_data`) fills them.
- **Footer page count off-by-one**: footers show `Page n of N` where `N` is one
  less than the physical page count (pre-existing on the baseline, unchanged).
- **Table numbering shifts** in Ch.3 (consequence of the required split); no
  cross-references exist, so nothing broke.
- Historical mangled row in old Table 5.1 renders (`r1_before_tbl5_1_mangled.png`)
  is preserved deliberately as the defect evidence.

## 7. Deliverables

- `Report_Before.pdf` (43 pp) — untouched baseline (GUI run).
- `Report_After.pdf` (45 pp) — final build; all cumulative checks pass:
  50/50 table headers, 3 chart PNGs embedded, 8 vehicle rows, BOQ 2(d) row,
  `1120 mm`, computed executive outcomes, no `\mathit`-raw/`一` artefacts.
- `docs/evidence/*.png` — 17 before/after renders cited above.
- This document: `docs/technical_changes.md`.
