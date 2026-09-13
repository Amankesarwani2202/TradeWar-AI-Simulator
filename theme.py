import streamlit as st
from plotly.graph_objs import Figure


LIGHT_COLORS = {
    "background": "#FFFFFF",
    "secondary": "#F0F2F6",
    "text": "#31333F",
    "muted": "#6B7280",
    "border": "#D1D5DB",
    "grid": "#E5E7EB",
}

DARK_COLORS = {
    "background": "#0E1117",
    "secondary": "#262730",
    "text": "#FAFAFA",
    "muted": "#B8C0CC",
    "border": "#3B4252",
    "grid": "#343B4A",
}


def is_dark_theme():
    try:
        return st.context.theme.base == "dark"
    except Exception:
        try:
            return st.get_option("theme.base") == "dark"
        except Exception:
            return False


def get_theme_colors():
    return DARK_COLORS if is_dark_theme() else LIGHT_COLORS


def apply_plotly_theme(fig: Figure) -> Figure:
    """Apply the app theme to Plotly figures without overriding explicit colors."""
    colors = get_theme_colors()

    fig.update_layout(
        paper_bgcolor=colors["background"],
        plot_bgcolor=colors["background"],
        font=dict(color=colors["text"]),
        title_font=dict(color=colors["text"]),
        legend=dict(font=dict(color=colors["text"])),
    )

    try:
        fig.update_xaxes(
            title_font=dict(color=colors["text"]),
            tickfont=dict(color=colors["text"]),
            gridcolor=colors["grid"],
            zerolinecolor=colors["grid"],
            linecolor=colors["border"],
        )
        fig.update_yaxes(
            title_font=dict(color=colors["text"]),
            tickfont=dict(color=colors["text"]),
            gridcolor=colors["grid"],
            zerolinecolor=colors["grid"],
            linecolor=colors["border"],
        )
    except Exception:
        pass

    for trace in fig.data:
        for attr in ("textfont", "insidetextfont", "outside_textfont"):
            try:
                current = getattr(trace, attr, None)
                if current is not None:
                    current_json = current.to_plotly_json() if hasattr(current, "to_plotly_json") else dict(current)
                    # Respect an explicit trace text color; otherwise use the theme.
                    if "color" not in current_json:
                        current_json["color"] = colors["text"]
                    setattr(trace, attr, current_json)
            except Exception:
                pass

        try:
            cb = getattr(getattr(trace, "marker", None), "colorbar", None)
            if cb is not None:
                title_text = cb.title.text if cb.title and cb.title.text else ""
                cb.title = dict(text=title_text, font=dict(color=colors["text"]))
                cb.tickfont = dict(color=colors["text"])
                cb.outlinecolor = colors["border"]
        except Exception:
            pass

        try:
            cb = getattr(trace, "colorbar", None)
            if cb is not None:
                title_text = cb.title.text if cb.title and cb.title.text else ""
                cb.title = dict(text=title_text, font=dict(color=colors["text"]))
                cb.tickfont = dict(color=colors["text"])
                cb.outlinecolor = colors["border"]
        except Exception:
            pass

    for annotation in list(fig.layout.annotations) if fig.layout.annotations else []:
        # Preserve explicit annotation colors (for example the per-cell colors
        # used by the Historical Data Lab correlation matrix). Only apply the
        # theme color when an annotation did not specify one itself.
        try:
            existing_font = annotation.font.to_plotly_json() if annotation.font else {}
            if "color" not in existing_font:
                existing_font["color"] = colors["text"]
                annotation.font = existing_font
        except Exception:
            try:
                if not annotation.font or annotation.font.color is None:
                    annotation.font.color = colors["text"]
            except Exception:
                pass

    return fig


def patch_streamlit_plotly_chart():
    """Apply our figure theme and disable Streamlit's second chart theme layer."""
    if getattr(st, "_trade_war_plotly_theme_patched", False):
        return

    original_plotly_chart = st.plotly_chart

    def themed_plotly_chart(figure_or_data, *args, **kwargs):
        if isinstance(figure_or_data, Figure):
            figure_or_data = apply_plotly_theme(figure_or_data)
            kwargs["theme"] = None
        return original_plotly_chart(figure_or_data, *args, **kwargs)

    st.plotly_chart = themed_plotly_chart
    st._trade_war_plotly_theme_patched = True
