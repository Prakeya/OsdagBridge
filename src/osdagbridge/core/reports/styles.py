# =============================================================================
# OsdagBridge Report — Centralized Style System (single source of truth)
#
# R6: page geometry, fonts, colors, table styles, header/footer theme, and
# cell padding live HERE.  report_generator.preamble() and every chap*.py
# module import from this file — no scattered hardcoded formatting.
#
# Invariants:
#   - The LaTeX emitted by these constants/functions must stay byte-identical
#     to the historical inline values (verified by diffing regenerated .tex
#     against the baseline during refactors).
#   - Dense-table overrides (TIGHT/COMPACT/NARROW) exist because some tables
#     are genuinely narrower; their VALUES are still defined only here.
# =============================================================================

# ── Page geometry & fonts ────────────────────────────────────────────────────
DOCUMENTCLASS = r"\documentclass[12pt,a4paper]{report}"
GEOMETRY_PACKAGE = r"\usepackage[a4paper, margin=1in]{geometry}"
FONT_SIZE_PT = 12
BODY_STRETCH = "1.15"          # \setstretch value (fonts)
PAGESTYLE_MAIN = "\\pagestyle{main}\n\\setstretch{" + BODY_STRETCH + "}"

# ── Figures (E3) ─────────────────────────────────────────────────────────────
# matplotlib savefig format for the report charts (UR chart, material charts).
# "pdf" = vector output — crisp at any zoom, text stays selectable; "png" =
# raster fallback (renderer dpi applies).  The writer in report_generator
# appends this extension when copying figure bytes to tmp images/.
CHART_FORMAT = "pdf"

# ── Colors ───────────────────────────────────────────────────────────────────
OSDAG_GREEN_HEX = "91B014"     # brand green (head/foot rules, success log)
OSDAG_GREEN = "osdagGreen"     # LaTeX color name
COLOR_DEFS = "\\definecolor{" + OSDAG_GREEN + "}{HTML}{" + OSDAG_GREEN_HEX + "}"

# Semantic status text — single source for PASS/FAIL rendering.
PASS_TEX = "PASS"
FAIL_TEX = r"\textcolor{red}{FAIL}"
PASS_BLACK_TEX = r"\textcolor{black}{PASS}"  # used where PASS must contrast on dark rows

# ── Pass/Fail cell badges (E1) ──────────────────────────────────────────────
# colortbl \cellcolor fills for table Status/UR cells. Threshold is identical
# to the UR chart in report_utils.build_ur_chart: UR <= 1.0 -> green (safe),
# UR > 1.0 -> red (unsafe). Fills are light so black text stays readable.
COLOR_SAFE = "statusSafe"       # green cell fill (PASS)
COLOR_UNSAFE = "statusUnsafe"   # red cell fill (FAIL)
COLOR_SAFE_HEX = "C6EFCE"
COLOR_UNSAFE_HEX = "FFC7CE"
COLOR_BADGE_DEFS = (
    "\\definecolor{" + COLOR_SAFE + "}{HTML}{" + COLOR_SAFE_HEX + "}\n"
    "\\definecolor{" + COLOR_UNSAFE + "}{HTML}{" + COLOR_UNSAFE_HEX + "}"
)


def status_cell(ok, text=None):
    """Green PASS / red FAIL \\cellcolor badge for table status cells (E1)."""
    if ok:
        return "\\cellcolor{" + COLOR_SAFE + "}" + ("PASS" if text is None else text)
    return "\\cellcolor{" + COLOR_UNSAFE + "}" + ("FAIL" if text is None else text)


def ur_cell(ur, fmt="{:.2f}"):
    """UR value in a green/red cell — same <= 1.0 rule as the UR chart (E1)."""
    f = float(ur)
    return status_cell(f <= 1.0, fmt.format(f))


# ── Verified clause references (E2) ──────────────────────────────────────────
# HARD RULE: every entry must be traceable from the calculation code. Sources:
#   - girder checks: engine checks[].clause via designer._add_check
#     (designer.py:2140-2419) and plategirderbridge.py
#   - shear connectors: designer.py Cl.606.x checks + plategirderbridge.py:1064
#   - deck slab: deckdesign.py (docstrings / log strings with clause numbers)
#   - cross bracing / end diaphragm members: osdag_core Compression_bolted /
#     Tension_bolted run through connect.run_calculation (MODULE_CLASS_MAP)
# Never add a clause that the calculation code does not emit. Keys with no
# traceable clause are simply absent — clause_ref() returns "---" for them.
CLAUSE_REFS = {
    # Girder ULS/SLS checks — engine check_id clauses (IRC 22 / IRC 24 / IS 800)
    "moment":       "IRC 22:2015 Cl.603.3.1; IS 800:2007 Cl.8.2.1",
    "shear":        "IRC 22:2015 Cl.603.3.3.2; IS 800:2007 Cl.8.4",
    "interaction":  "IRC 22:2015 Cl.603.3.3.3",
    "ltb":          "IRC 22:2015 Cl.603.3.3.1; IS 800:2007 Cl.8.2.2",
    "int_stiff":    "IRC 24:2010 Cl.509.7.2; IS 800:2007 Cl.8.7.2",
    "brg_stiff":    "IRC 24:2010 Cl.509.7.3; IS 800:2007 Cl.8.7.3",
    "deflection":   "IRC 22:2015 Cl.604.3.2",
    "stress":       "IRC 22:2015 Cl.604.3.1; IRC 112 Cl.12.2.1",
    "fatigue":      "IRC 22:2015 Cl.605",
    # Shear connectors — engine Cl.606.x (designer.py:1324/1376/2245-2284)
    "sc_capacity":  "IRC 22:2015 Cl.606.3.1, 606.3.2",
    "sc_sl1":       "IRC 22:2015 Cl.606.4.1",
    "sc_sl2":       "IRC 22:2015 Cl.606.4.1.1",
    "sc_sr":        "IRC 22:2015 Cl.606.4.2",
    "sc_max":       "IRC 22:2015 Cl.606.9",
    "sc_ts":        "IRC 22:2015 Cl.606.10",
    "sc_detail":    "IRC 22:2015 Cl.606.6",
    # Cross bracing / end diaphragm members — osdag_core member design
    "cb_compression": "IS 800:2007 Cl.7.1.2",
    "cb_tension":     "IS 800:2007 Cl.6.1, 6.2",
    # Deck slab — deckdesign.py (only clauses the code actually cites)
    "deck_punching":  "IRC 112:2020 Cl.10.4",
    "deck_oneway":    "IRC 112:2020 Eq.10.1, Cl.10.3.2",
    "deck_crack":     "IRC 112:2020 Cl.12.3.2, 12.3.4; IRC 22:2015 Cl.604.4",
    # Section classification — is800_2007.py:21/40/58 (Table 2, Cl.3.7)
    "classification": "IS 800:2007 Table 2, Cl.3.7",
}


def clause_ref(key):
    """Verified clause string for a CLAUSE_REFS key; '---' when not traceable."""
    return CLAUSE_REFS.get(key, "---")


def red_tex(text):
    """Wrap arbitrary text in the standard alert red (UR > 1.0, failures)."""
    return r"\textcolor{red}{" + str(text) + "}"


def tabcolsep(value):
    """LaTeX line: \\setlength{\\tabcolsep}{value} — chapters never hardcode."""
    return "\\setlength{\\tabcolsep}{" + value + "}"


def arraystretch(value):
    """LaTeX line: \\renewcommand{\\arraystretch}{value}."""
    return "\\renewcommand{\\arraystretch}{" + value + "}"


# Log-line severity colors (Chapter 8 design log).
LOG_INFO_COLOR = "blue"
LOG_ERROR_COLOR = "red"
LOG_SUCCESS_COLOR = OSDAG_GREEN

# ── Table styles: cell padding, row height, rules ────────────────────────────
TABCOLSEP = "6pt"              # default cell padding (both sides)
ARRAYSTRETCH = "1.12"          # default row height multiplier
LT_PRE = "0pt"                 # longtable skips
LT_POST = "6pt"
ARRAYRULEWIDTH = "0.5pt"       # table rule thickness
EXTRAROWHEIGHT = "0.6pt"       # extra row height for legibility

# Dense-table overrides (per-table narrow layouts)
TABCOLSEP_TIGHT = "4pt"        # chap2, chap5
TABCOLSEP_COMPACT = "3.5pt"    # chap7, chap8
TABCOLSEP_NARROW = "3pt"       # chap4
ARRAYSTRETCH_DENSE = "1.25"    # chap4 dense tables

TABLE_SPACING = (
    "% Table layout and spacing: consistent padding, row height, and longtable pre/post skips\n"
    "\\setlength{\\tabcolsep}{" + TABCOLSEP + "}\n"
    "\\renewcommand{\\arraystretch}{" + ARRAYSTRETCH + "}\n"
    "\\setlength{\\LTpre}{" + LT_PRE + "}\n"
    "\\setlength{\\LTpost}{" + LT_POST + "}\n"
    "% Table rules (outline thickness) and small extra row height for clarity\n"
    "\\setlength{\\arrayrulewidth}{" + ARRAYRULEWIDTH + "}\n"
    "\\setlength{\\extrarowheight}{" + EXTRAROWHEIGHT + "}"
)

# Page-bottom threshold: start a table only if this many baselines remain.
NEEDSPACE_ROWS = r"5\baselineskip"
NEEDSPACE_GUARDS = (
    "% Prevent tables from overflowing past the page bottom:\n"
    "% if fewer than 5 baseline-skips remain, break to the next page first.\n"
    "\\BeforeBeginEnvironment{table}{\\needspace{" + NEEDSPACE_ROWS + "}}\n"
    "\\BeforeBeginEnvironment{longtable}{\\needspace{" + NEEDSPACE_ROWS + "}}"
)

# ── Caption style ────────────────────────────────────────────────────────────
CAPTION_SETUP = (
    "\\captionsetup{\n"
    "    labelfont=bf,\n"
    "    justification=raggedright,\n"
    "    singlelinecheck=false,\n"
    "    format=plain\n"
    "}"
)

# ── Column types (table alignment helpers) ───────────────────────────────────
COLUMN_TYPES = (
    "\\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{#1}}\n"
    "\\newcolumntype{C}[1]{>{\\centering\\arraybackslash}p{#1}}\n"
    "\\newcolumntype{R}[1]{>{\\raggedleft\\arraybackslash}p{#1}}"
)

# ── Custom commands / software-default marker ────────────────────────────────
CUSTOM_COMMANDS = (
    "% Custom Commands\n"
    "\\newcommand{\\placeholder}[1]{\\textit{\\textless #1\\textgreater}}\n"
    "\\newcommand{\\todo}[1]{\\colorbox{yellow}{TODO: #1}}\n"
)

SDSTAR_COMMANDS = (
    "% Software-default asterisk\n"
    "\\newcommand{\\sdstar}{\\textsuperscript{*}}\n"
    "\\newbool{hasSDonPage}\n"
    "\\boolfalse{hasSDonPage}\n"
    "\\newcommand{\\markSD}{\\global\\booltrue{hasSDonPage}}\n"
    "\\renewcommand{\\sdstar}{\\textsuperscript{*}\\markSD{}}\n"
    "\\AddToHook{shipout/before}{\\global\\boolfalse{hasSDonPage}}"
)

# ── Header / footer theme (fancyhdr) ─────────────────────────────────────────
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_RIGHT = r"Page \thepage\ of \pageref{LastPage}"
HEADRULE = r"\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}"


def _footrule_tex():
    """Footrule with the '* Software default value' note when marked on page."""
    return (
        "\\renewcommand{\\footrule}{%\n"
        "    \\ifbool{hasSDonPage}{%\n"
        "      \\vspace{-20pt}%\n"
        "      \\hbox to \\headwidth{\\textcolor{black}{\\footnotesize\\textit{* Software default value}}\\hfil}%\n"
        "      \\vspace{4pt}%\n"
        "    }{%\n"
        "      \\vspace{-8pt}%\n"
        "    }%\n"
        "    \\color{osdagGreen}\\hrule width\\headwidth height 1pt \\vspace{6pt}%\n"
        "  }"
    )


def page_styles(project_name_tex, job_number_tex, report_date_tex, report_version_tex):
    """Return the fancyhdr page-style blocks (main / plain / firstpage).

    All header/footer text, rules, and colors are defined here — chapters and
    preamble never hardcode them.
    """
    head_l = "\\fancyhead[L]{" + project_name_tex + " $|$ " + job_number_tex + "}"
    head_r = "\\fancyhead[R]{" + report_date_tex + " $|$ " + report_version_tex + "}"
    foot_l = "\\fancyfoot[L]{" + FOOTER_LEFT + "}"
    foot_r = "\\fancyfoot[R]{" + FOOTER_RIGHT + "}"

    main_and_plain = (
        "  \\fancyhf{}\n"
        "  " + head_l + "\n"
        "  " + head_r + "\n"
        "  " + foot_l + "\n"
        "  " + foot_r + "\n"
        "  \\renewcommand{\\headrule}{" + HEADRULE + "}\n"
        "  " + _footrule_tex() + "\n"
        "}"
    )

    firstpage = (
        "\\fancypagestyle{firstpage}{\n"
        "  \\fancyhf{}\n"
        "  \\renewcommand{\\headrulewidth}{0pt}\n"
        "  " + foot_l + "\n"
        "  " + foot_r + "\n"
        "  \\renewcommand{\\footrule}{\\vspace{-8pt}\\color{osdagGreen}\\hrule width\\headwidth height 1pt \\vspace{6pt}}\n"
        "}"
    )

    return (
        "\\fancypagestyle{main}{\n" + main_and_plain + "\n"
        "\\fancypagestyle{plain}{\n" + main_and_plain + "\n"
        + firstpage
    )
