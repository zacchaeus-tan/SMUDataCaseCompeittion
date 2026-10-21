"""
Monthly demand forecasting by country x product.

Baseline (today):  6-month moving average of past purchase-order units.
OneRecord model:   "business-calendar" regression, fitted on log units across all 15 series at once:
                       log(units) = level[series] + trend[series] + known calendar events
                   Events are things a diagnostics distributor already knows: dengue season (Product A,
                   by country), the hospital year-end budget push (Nov/Dec), the January lull, and public
                   holidays (Lunar New Year, Tet, Songkran, Hari Raya / Lebaran). Few parameters, so it
                   learns from 12-18 months of history where a full seasonal model cannot.
Both are scored by a rolling backtest: forecast 1-3 months ahead from each origin Apr-Sep 2026.
Accuracy metric: WAPE = sum |forecast - actual| / sum actual (lower is better).
"""
import numpy as np
import pandas as pd

DENGUE = {"SG": (6, 7, 8), "MY": (6, 7, 8, 9), "TH": (6, 7, 8, 9), "ID": (1, 2, 3, 4), "VN": (7, 8, 9, 10)}
HOLIDAYS = {  # year-month of major public-holiday disruption
    "SG": {"2026-02", "2027-02"},
    "MY": {"2025-04", "2026-02", "2026-03", "2027-02", "2027-03"},
    "TH": {"2025-04", "2026-04", "2027-04"},
    "ID": {"2025-04", "2026-03", "2027-03"},
    "VN": {"2026-02", "2027-02"},
}
EVENT_NAMES = ["Dengue season (Product A)", "December budget flush", "November", "January lull",
               "Public holiday month"]
TREND_SHRINK = 10.0  # strong shrinkage: 12-18 months can't support a confident per-series trend


def add_months(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:])
    m0 = y * 12 + m - 1 + k
    return f"{m0 // 12}-{m0 % 12 + 1:02d}"


def series(po: pd.DataFrame) -> pd.DataFrame:
    """Units by (country, product) x month."""
    return po.groupby(["country", "product", "month"]).quantity.sum().unstack(fill_value=0).sort_index(axis=1)


def _events(cc, product, ym):
    m = int(ym[5:])
    return np.array([float(product == "A" and m in DENGUE[cc]), float(m == 12), float(m == 11), float(m == 1),
                     float(ym in HOLIDAYS[cc])])


def fit_calendar_model(Y: pd.DataFrame):
    keys, months = list(Y.index), list(Y.columns)
    S, T, E = len(keys), len(months), len(EVENT_NAMES)

    def feat(si, ym):
        x = np.zeros(2 * S + E)
        x[si] = 1
        x[S + si] = (_gap(months[0], ym) - T) / 12  # years relative to end of history
        x[2 * S:] = _events(*keys[si], ym)
        return x

    rows, ys = [], []
    for si in range(S):
        for ym in months:
            v = Y.iat[si, months.index(ym)]
            if v > 0:
                rows.append(feat(si, ym))
                ys.append(np.log(v))
    X, y = np.array(rows), np.array(ys)
    penalty = np.r_[np.zeros(S), np.full(S, TREND_SHRINK), np.full(E, 0.1)]
    beta = np.linalg.solve(X.T @ X + np.diag(penalty), X.T @ y)
    sigma2 = (y - X @ beta).var()

    def predict(si, ym):
        return float(np.exp(feat(si, ym) @ beta + sigma2 / 2))

    effects = dict(zip(EVENT_NAMES, np.round(np.exp(beta[2 * S:]) - 1, 3)))
    return predict, effects


def _gap(a, b):
    return (int(b[:4]) * 12 + int(b[5:])) - (int(a[:4]) * 12 + int(a[5:]))


def moving_average(history: np.ndarray, window=6):
    return float(history[-window:].mean())


def backtest(Y: pd.DataFrame, first_origin="2026-04", horizon=3):
    """Rolling-origin backtest. Returns long DataFrame of forecasts vs actuals for both methods."""
    months = list(Y.columns)
    rows = []
    for o in range(months.index(first_origin), len(months)):
        train = Y.iloc[:, :o]
        predict, _ = fit_calendar_model(train)
        for si, (cc, p) in enumerate(Y.index):
            for h in range(horizon):
                if o + h >= len(months):
                    break
                ym = months[o + h]
                rows.append(dict(country=cc, product=p, origin=months[o], month=ym, horizon=h + 1,
                                 actual=Y.iat[si, o + h], baseline_ma6=moving_average(train.iloc[si].values),
                                 calendar_model=predict(si, ym)))
    return pd.DataFrame(rows)


def wape(df: pd.DataFrame, col: str) -> float:
    return float((df[col] - df.actual).abs().sum() / df.actual.sum())


def accuracy_table(bt: pd.DataFrame) -> pd.DataFrame:
    out = bt.groupby(["country", "product"]).apply(
        lambda g: pd.Series({"MA6 error": wape(g, "baseline_ma6"), "Model error": wape(g, "calendar_model")}),
        include_groups=False).reset_index()
    out["Improvement"] = 1 - out["Model error"] / out["MA6 error"]
    return out


def forecast_ahead(Y: pd.DataFrame, n=3) -> pd.DataFrame:
    predict, effects = fit_calendar_model(Y)
    last = Y.columns[-1]
    rows = []
    for si, (cc, p) in enumerate(Y.index):
        ma6 = moving_average(Y.iloc[si].values)
        for k in range(1, n + 1):
            ym = add_months(last, k)
            rows.append(dict(country=cc, product=p, month=ym, baseline_ma6=ma6, calendar_model=predict(si, ym)))
    return pd.DataFrame(rows), effects
