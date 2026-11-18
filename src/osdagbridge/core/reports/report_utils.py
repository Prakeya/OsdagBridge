from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_SPAN,
)
from osdagbridge.core.reports import styles


def _fig_bytes(fig):
    """Render a matplotlib Figure in styles.CHART_FORMAT and return the bytes.

    E3: chart output format lives in styles.CHART_FORMAT ("pdf" = vector).
    The canvas is attached here so the three chart builders share one path —
    PDF uses backend_pdf (vector), anything else falls back to Agg.
    """
    from io import BytesIO
    fmt = styles.CHART_FORMAT
    if fmt == "pdf":
        from matplotlib.backends.backend_pdf import FigureCanvasPdf
        FigureCanvasPdf(fig)
    else:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        FigureCanvasAgg(fig)
    buf = BytesIO()
    fig.savefig(buf, format=fmt, dpi=150, facecolor="white")
    return buf.getvalue()


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




def build_ur_chart(summary):
    """Render the §5.5 utilization-ratio chart (format = styles.CHART_FORMAT).

    summary: [(label, ur), ...] — worst UR per member family (see
    chap5.ur_overall_summary). Uses matplotlib Figure directly (no pyplot)
    so it is backend-independent and safe inside the GUI app; the canvas is
    attached at save time by _fig_bytes. Returns figure bytes, or None when
    there is nothing to plot.
    """
    if not summary:
        return None
    try:
        from matplotlib.figure import Figure

        labels = [str(s[0]) for s in summary]
        vals = [float(s[1]) for s in summary]

        fig = Figure(figsize=(7.0, 0.85 * len(labels) + 1.5), facecolor="white")
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

        return _fig_bytes(fig)
    except Exception:
        return None


def _mt_bar(items, xlabel):
    """Horizontal bar chart of (label, MT) pairs -> figure bytes (or None).

    Same Figure pattern as build_ur_chart (no pyplot, backend-independent).
    Value labels keep tiny bars readable next to dominant ones (e.g. girders
    vs shear studs).
    """
    items = [(str(lbl), float(v)) for lbl, v in items if v is not None]
    if not items:
        return None
    try:
        from matplotlib.figure import Figure

        labels = [i[0] for i in items]
        vals = [i[1] for i in items]

        fig = Figure(figsize=(7.0, 0.85 * len(labels) + 1.5), facecolor="white")
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

        return _fig_bytes(fig)
    except Exception:
        return None


def build_material_charts(quantities):
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
        "steel_chart": _mt_bar(steel, "Structural steel quantity (MT)"),
        "deck_chart": _mt_bar(deck, "Deck material quantity (MT)"),
    }


def _bridge_geometry(inputs, output_dict=None):
    """Idealized superstructure geometry (metres) from report inputs.

    Returns dict with span, n_girders, spacing, overhang, girder_depth,
    deck_thickness, y_girders (list of lateral positions, centred),
    deck_half_width, bracing_x (transverse station positions).
    """
    def _f(d, k, default):
        try:
            v = (d or {}).get(k, default)
            return float(v) if v not in (None, "") else float(default)
        except (TypeError, ValueError):
            return float(default)

    span = _f(inputs, KEY_SPAN, 20.0)
    n = int(_f(inputs, KEY_TS_NO_OF_GIRDERS, 3))
    n = max(1, n)
    spacing = _f(inputs, KEY_TS_GIRDER_SPACING, 2.5)
    overhang = _f(inputs, KEY_TS_DECK_OVERHANG, 0.0)
    deck_t = _f(inputs, KEY_TS_DECK_THICKNESS, 250.0) / 1000.0  # mm → m

    # Girder depth: design results first (mm), then section input (m).
    depth = None
    if output_dict:
        try:
            d = float(output_dict.get("steeldesign.details.total_depth"))
            if d > 50:  # looks like millimetres
                depth = d / 1000.0
            elif d > 0:
                depth = d
        except (TypeError, ValueError):
            depth = None
    if depth is None:
        depth = _f(inputs, "member_properties.girder_details.section_input.depth", 1.12)
    if depth <= 0:
        depth = 1.12

    y0 = -(n - 1) * spacing / 2.0
    y_girders = [y0 + i * spacing for i in range(n)]
    deck_half = (n - 1) * spacing / 2.0 + overhang

    # Transverse stations: ends + internal cross-bracing (mid-span for short
    # spans, else ~every 10 m — matches DEFAULT_CROSS_BRACING_SPACING).
    brace_xs = [0.0, span]
    internal = max(1, int(round(span / 10.0)))
    for i in range(1, internal + 1):
        x = span * i / (internal + 1)
        if 1e-6 < x < span - 1e-6:
            brace_xs.append(x)
    brace_xs = sorted(set(round(x, 6) for x in brace_xs))

    return {
        "span": span,
        "n_girders": n,
        "spacing": spacing,
        "overhang": overhang,
        "girder_depth": depth,
        "deck_thickness": deck_t,
        "y_girders": y_girders,
        "deck_half_width": deck_half,
        "bracing_x": brace_xs,
    }


def _draw_elevation(ax, g):
    """2D longitudinal elevation (side view) on a matplotlib 2D axes."""
    from matplotlib.patches import Rectangle

    span = g["span"]
    d = g["girder_depth"]
    dt = g["deck_thickness"]
    z_top = d + dt

    # Deck slab
    ax.add_patch(Rectangle(
        (0.0, d), span, dt, facecolor="#b0c4de", edgecolor="#334455",
        linewidth=1.0, zorder=2))
    # Girder body (side silhouette — all girders project to the same line)
    ax.add_patch(Rectangle(
        (0.0, 0.0), span, d, facecolor="#e8e8e8", edgecolor="#333333",
        linewidth=1.2, zorder=3))
    # Flange lines
    ax.plot([0, span], [0, 0], color="#333333", lw=1.4, zorder=4)
    ax.plot([0, span], [d, d], color="#333333", lw=1.0, zorder=4)

    # Transverse bracing stations (vertical markers through the web)
    for x in g["bracing_x"]:
        ax.plot([x, x], [0.08 * d, d - 0.08 * d], color="#666666",
                lw=0.8, ls="--", zorder=4)

    # Supports (triangles at bearing points)
    s = 0.55  # triangle half-width, m
    h = 0.45  # triangle height, m
    for x in (0.0, span):
        ax.fill([x - s, x + s, x], [-h, -h, 0.0],
                color="#555555", zorder=5)
    # Ground / bearing line
    ax.plot([-0.15 * span, 1.15 * span], [-h, -h], color="#333333",
            lw=1.2, zorder=5)

    # Span dimension
    y_dim = -h - 0.22 * d
    ax.annotate("", xy=(span, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="#222222", lw=1.0))
    ax.text(span / 2, y_dim - 0.12 * d, f"L = {span:g} m",
            ha="center", va="top", fontsize=9)

    # Height dimension (girder + deck)
    x_dim = -0.06 * span
    ax.annotate("", xy=(x_dim, 0.0), xytext=(x_dim, z_top),
                arrowprops=dict(arrowstyle="<->", color="#222222", lw=1.0))
    ax.text(x_dim - 0.01 * span, z_top / 2, f"{z_top:.2f} m",
            ha="right", va="center", fontsize=8, rotation=90)

    ax.set_xlim(-0.14 * span, 1.14 * span)
    ax.set_ylim(-h - 0.55 * d, z_top + 0.35 * d)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Distance along span (m)", fontsize=9)
    ax.set_ylabel("Elevation (m)", fontsize=9)
    ax.set_title("Longitudinal Elevation (2D)", fontsize=10, pad=6)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.tick_params(labelsize=8)


def _draw_isometric(ax, g):
    """Static isometric wireframe of the superstructure on a 3D axes."""
    span = g["span"]
    d = g["girder_depth"]
    dt = g["deck_thickness"]
    z_top = d + dt
    half = g["deck_half_width"]
    ys = g["y_girders"]

    # Deck top surface outline
    deck_corners_x = [0, span, span, 0, 0]
    deck_corners_y = [-half, -half, half, half, -half]
    ax.plot(deck_corners_x, deck_corners_y, [z_top] * 5,
            color="#334455", lw=1.4)

    # Deck bottom edge (on girder tops)
    ax.plot(deck_corners_x, deck_corners_y, [d] * 5,
            color="#667788", lw=0.8, ls="--")

    # Girders: top and bottom chords + end verticals
    for y in ys:
        ax.plot([0, span], [y, y], [0, 0], color="#222222", lw=1.6)
        ax.plot([0, span], [y, y], [d, d], color="#444444", lw=1.2)
        for x in (0.0, span):
            ax.plot([x, x], [y, y], [0, d], color="#444444", lw=1.0)

    # Transverse bracing stations (top + bottom cross lines between edge girders)
    y_min, y_max = min(ys), max(ys)
    for x in g["bracing_x"]:
        ax.plot([x, x], [y_min, y_max], [0, 0], color="#888888", lw=0.9)
        ax.plot([x, x], [y_min, y_max], [d, d], color="#888888", lw=0.9)
        # End frames: verticals at edge girders
        for y in (y_min, y_max):
            ax.plot([x, x], [y, y], [0, d], color="#888888", lw=0.8)

    # Supports
    for x in (0.0, span):
        for y in ys:
            ax.scatter([x], [y], [0], color="#555555", s=18, zorder=5)

    ax.set_xlim(-0.05 * span, 1.05 * span)
    ax.set_ylim(-half * 1.15, half * 1.15)
    ax.set_zlim(-0.25 * span, 0.45 * span)
    ax.set_box_aspect((span, 2 * half, span * 0.55))
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    ax.set_title("Isometric View", fontsize=10, pad=4)


def build_bridge_views(inputs, output_dict=None):
    """E5: static vector 2D elevation + isometric of the bridge superstructure.

    Pure matplotlib (Figure, no pyplot / no CAD / no media9 / no U3D).
    Format = styles.CHART_FORMAT ("pdf" = vector). Returns
    {"bridge_elevation": bytes, "bridge_isometric": bytes}; each value is
    None when the figure could not be built.
    """
    out = {"bridge_elevation": None, "bridge_isometric": None}
    try:
        from matplotlib.figure import Figure
        g = _bridge_geometry(inputs, output_dict)

        fig1 = Figure(figsize=(6.4, 3.2), facecolor="white")
        _draw_elevation(fig1.add_subplot(111), g)
        fig1.tight_layout()
        out["bridge_elevation"] = _fig_bytes(fig1)

        fig2 = Figure(figsize=(5.6, 4.0), facecolor="white")
        _draw_isometric(fig2.add_subplot(111, projection="3d"), g)
        out["bridge_isometric"] = _fig_bytes(fig2)
    except Exception:
        return out
    return out
