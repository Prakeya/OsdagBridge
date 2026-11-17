from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')




def build_ur_chart_png(summary):
    """Render the §5.5 utilization-ratio chart to PNG bytes.

    summary: [(label, ur), ...] — worst UR per member family (see
    chap5.ur_overall_summary). Uses matplotlib Figure + Agg canvas directly
    (no pyplot) so it is backend-independent and safe inside the GUI app.
    Returns PNG bytes, or None when there is nothing to plot.
    """
    if not summary:
        return None
    try:
        from io import BytesIO
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        labels = [str(s[0]) for s in summary]
        vals = [float(s[1]) for s in summary]

        fig = Figure(figsize=(7.0, 0.85 * len(labels) + 1.5), facecolor="white")
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        colors = ["#c0392b" if v > 1.0 else "#2e7d32" for v in vals]
        ypos = list(range(len(labels)))
        ax.barh(ypos, vals, color=colors, edgecolor="#333333", height=0.6, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.invert_yaxis()

        ax.axvline(1.0, color="#c0392b", linestyle="--", linewidth=1.2, zorder=4)
        ax.text(1.0, -0.72, "UR = 1.0", color="#c0392b", fontsize=9,
                ha="center", va="bottom")

        for i, v in enumerate(vals):
            ax.text(v + 0.015, i, f"{v:.2f}", va="center", ha="left", fontsize=9)

        ax.set_xlabel("Utilization ratio (Demand / Capacity)", fontsize=10)
        ax.set_xlim(0.0, max(1.25, max(vals) * 1.3 if vals else 1.25))
        ax.grid(axis="x", linestyle=":", alpha=0.5, zorder=0)
        ax.tick_params(axis="x", labelsize=9)
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, facecolor="white")
        return buf.getvalue()
    except Exception:
        return None


def _mt_bar_png(items, xlabel):
    """Horizontal bar chart of (label, MT) pairs -> PNG bytes (or None).

    Same Figure + Agg canvas pattern as build_ur_chart_png (no pyplot,
    backend-independent). Value labels keep tiny bars readable next to
    dominant ones (e.g. girders vs shear studs).
    """
    items = [(str(lbl), float(v)) for lbl, v in items if v is not None]
    if not items:
        return None
    try:
        from io import BytesIO
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        labels = [i[0] for i in items]
        vals = [i[1] for i in items]

        fig = Figure(figsize=(7.0, 0.85 * len(labels) + 1.5), facecolor="white")
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        ypos = list(range(len(labels)))
        ax.barh(ypos, vals, color="#2e7d32", edgecolor="#333333", height=0.6, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.invert_yaxis()

        peak = max(vals) if vals else 1.0
        offset = peak * 0.02 if peak > 0 else 0.01
        for i, v in enumerate(vals):
            ax.text(v + offset, i, f"{v:.2f} MT", va="center", ha="left", fontsize=9)

        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_xlim(0.0, peak * 1.25 if peak > 0 else 1.0)
        ax.grid(axis="x", linestyle=":", alpha=0.5, zorder=0)
        ax.tick_params(axis="x", labelsize=9)
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, facecolor="white")
        return buf.getvalue()
    except Exception:
        return None


def build_material_charts_pngs(quantities):
    """Chapter 7 material charts -> {"steel_chart": bytes|None, "deck_chart": bytes|None}.

    quantities: the dict from boq.calculate_material_quantities; the *_wt_total
    entries are total-weight strings in MT. The steel chart covers the
    structural-steel items (girders, cross bracing, end diaphragm, shear
    studs); concrete items (deck, barrier) are excluded by design.
    """

    def _f(key):
        try:
            return float(quantities.get(key))
        except (TypeError, ValueError):
            return None

    steel = []
    girder_mt = _f("steel_girders_wt_total")
    if girder_mt is not None:
        steel.append(("Girders", girder_mt))

    cb_parts = [_f(k) for k in ("bracing_top_wt_total",
                                "bracing_bot_wt_total",
                                "bracing_diag_wt_total")]
    if any(v is not None for v in cb_parts):
        steel.append(("Cross bracing", sum(v for v in cb_parts if v is not None)))

    ed_mt = _f("steel_ed_wt_total")
    if ed_mt is not None:
        steel.append(("End diaphragm", ed_mt))

    stud_mt = _f("shear_studs_wt_total")
    if stud_mt is not None:
        steel.append(("Shear studs", stud_mt))

    deck = [("Concrete (M40)", _f("concrete_deck_wt_total")),
            ("Reinforcement (Fe 500)", _f("rebar_deck_wt_total"))]

    return {
        "steel_chart": _mt_bar_png(steel, "Structural steel quantity (MT)"),
        "deck_chart": _mt_bar_png(deck, "Deck material quantity (MT)"),
    }
