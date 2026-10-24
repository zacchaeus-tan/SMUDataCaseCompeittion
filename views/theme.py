"""One palette for the whole app. Charts and CSS take their colours from here (CSS mirrors them in assets/app.css)."""

# brand
PRIMARY = "#0f766e"       # deep teal: sidebar, headers
NAVY = "#0b2545"          # text on light, active nav
ACCENT = "#14b8a6"        # bright teal: highlights, buttons
PAGE = "#f7fafc"
CARD = "#ffffff"
TEXT = "#334155"
MUTED = "#94a3b8"

# meaning (fixed on every page)
GOOD = "#16a34a"          # growth
BAD = "#dc2626"           # decline, drop-offs, value at risk
WARN = "#f59e0b"          # pending: MDM setups, enquiries
FORECAST = "#f97316"      # forecast line (dashed)
FORECAST_BAND = "rgba(20, 184, 166, 0.15)"   # forecast range: accent teal at 15%
BASELINE = MUTED          # today's rolling-average forecast (dotted)

# products. A and B are hard to tell apart for colour-blind readers, so product lines are always labelled directly
PRODUCT = {"A": "#2563eb", "B": "#7c3aed", "C": "#0891b2"}

# growth heatmap: red decline, grey no change, green growth; every cell also shows its % as text
GROWTH_SCALE = [[0, BAD], [0.5, "#f1f5f9"], [1, GOOD]]
