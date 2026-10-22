"""Shared design tokens and layout constants for the generated SVGs.

Every SVG only reads colors through CSS custom properties. The dark and the
light file differ by nothing but the values defined here.
"""

FONT_STACK = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

# Width shared by the header and the contribution graph (px).
TOTAL_W = 880
RADIUS = 8

TOKENS = {
    "dark": {
        "--bg": "#0d1117",
        "--surface": "#161b22",
        "--border": "#30363d",
        "--text": "#e6edf3",
        "--text-muted": "#9198a1",
        "--accent": "#58a6ff",
    },
    "light": {
        "--bg": "#ffffff",
        "--surface": "#f6f8fa",
        "--border": "#d0d7de",
        "--text": "#1f2328",
        "--text-muted": "#59636e",
        "--accent": "#0969da",
    },
}

# Green scale for the contribution heatmap, same idea as GitHub's.
HEAT = {
    "dark": ["#21262d", "#0e4429", "#006d32", "#26a641", "#39d353"],
    "light": ["#e1e5ea", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
}


def root_css(variant: str, extra: dict | None = None) -> str:
    """The :root rule that defines the tokens of one variant."""
    items = dict(TOKENS[variant])
    if extra:
        items.update(extra)
    body = "".join(f"{k}:{v};" for k, v in items.items())
    return f":root{{{body}}}"


def heat_tokens(variant: str) -> dict:
    return {f"--heat-{i}": c for i, c in enumerate(HEAT[variant])}


# Reduced motion: no animation at all, the final state is the base style.
REDUCED_MOTION_CSS = "@media (prefers-reduced-motion: reduce){*{animation:none !important}}"
