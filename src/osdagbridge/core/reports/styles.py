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

# ── Colors ───────────────────────────────────────────────────────────────────
OSDAG_GREEN_HEX = "91B014"     # brand green (head/foot rules, success log)
OSDAG_GREEN = "osdagGreen"     # LaTeX color name
COLOR_DEFS = "\\definecolor{" + OSDAG_GREEN + "}{HTML}{" + OSDAG_GREEN_HEX + "}"

# Semantic status text — single source for PASS/FAIL rendering (feeds E1).
PASS_TEX = "PASS"
FAIL_TEX = r"\textcolor{red}{FAIL}"
PASS_BLACK_TEX = r"\textcolor{black}{PASS}"  # used where PASS must contrast on dark rows


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
