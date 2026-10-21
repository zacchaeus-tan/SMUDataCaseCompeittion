"""Regional business view: growth, forecasting, sales actions, inbound triage, data quality, business case."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from onerecord import classify, process
from onerecord.config import COUNTRIES, CURRENT, PRIOR_YEAR, PRODUCTS

from . import common as c

COLORS = {"A": "#2a6fdb", "B": "#e07b39", "C": "#5b9a68"}


def _definition():
    st.info(f"**Growth measure:** year-on-year change in purchase-order **units**, "
            f"{CURRENT[0]}–{CURRENT[1]} vs {PRIOR_YEAR[0]}–{PRIOR_YEAR[1]} (same six months, so seasonality "
            f"cancels). **Momentum:** last 3 months vs the same 3 months a year earlier. Counts **customer orders "
            f"only** — enquiries, follow-ups and master-data requests are excluded (see *Orders vs enquiries*).")


# --------------------------------------------------------------------------- growth
def growth():
    st.title("Five-country growth · Products A, B, C")
    _definition()
    g = c.regional()["growth"]
    g["country_name"] = g.country.map(COUNTRIES)

    tot_now, tot_prev = g.units_now.sum(), g.units_prev.sum()
    val_now, val_prev = g.value_now.sum(), g.value_prev.sum()
    k = st.columns(4)
    k[0].metric("Units, Apr–Sep 2026", f"{tot_now:,.0f}", c.pct(tot_now / tot_prev - 1))
    k[1].metric("Order value (SGD)", f"{val_now / 1e6:,.2f}M", c.pct(val_now / val_prev - 1))
    k[2].metric("Active customers", f"{c.regional()['clean'].query('month >= @CURRENT[0]').customer_id.nunique()}",
                help="Real customers after merging duplicate records")
    best = g.loc[g[g["product"] != "C"].unit_growth.idxmax()]
    k[3].metric("Fastest growing (A/B)", f"{best.country} · {best['product']}", c.pct(best.unit_growth))

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("##### Year-on-year unit growth")
        m = g.pivot(index="country", columns="product", values="unit_growth").reindex(c.COUNTRY_ORDER)
        fig = px.imshow(m, text_auto="+.0%", color_continuous_scale="RdYlGn", zmin=-0.3, zmax=0.3, aspect="auto",
                        labels=dict(color="YoY"))
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        st.caption("Product C (equipment) sells only ~30–50 units per country per half-year — read its growth "
                   "as directional; value-based or rolling-12-month views are steadier.")
    with right:
        st.markdown("##### Country × product table")
        t = g[["country", "product", "units_now", "unit_growth", "momentum_3m", "value_now", "customers_now"]].copy()
        st.dataframe(t, hide_index=True, width="stretch", height=330, column_config={
            "units_now": st.column_config.NumberColumn("Units", format="%d"),
            "unit_growth": st.column_config.NumberColumn("YoY", format="percent"),
            "momentum_3m": st.column_config.NumberColumn("3-mo momentum", format="percent"),
            "value_now": st.column_config.NumberColumn("Value SGD", format="%.0f"),
            "customers_now": st.column_config.NumberColumn("Customers"),
        })

    st.markdown("##### Monthly units")
    prod = st.radio("Product", list(PRODUCTS), horizontal=True, format_func=lambda p: c.PRODUCT_LABEL[p])
    mm = c.regional()["monthly"].query("product == @prod")
    fig = px.line(mm, x="month", y="quantity", color="country", markers=True,
                  category_orders={"country": c.COUNTRY_ORDER})
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="units", xaxis_title="")
    st.plotly_chart(fig, width="stretch")

    st.markdown("##### What it means")
    vn_b = g[(g.country == "VN") & (g["product"] == "B")].iloc[0]
    drops = c.regional()["compare"]["clean_drop"]
    vn_drop_val = drops[drops.country == "VN"].value_at_risk_per_q.sum()
    st.markdown(
        f"- **Malaysia and Indonesia lead growth** (A and B up ~20–30% YoY) — prioritise stock cover and sales "
        f"capacity there ahead of the Dec budget flush and ID's Jan–Apr dengue season.\n"
        f"- **Vietnam Product B is down {abs(vn_b.unit_growth):.0%}** although the market is growing: the drop is "
        f"concentrated in a few large labs that are ordering far less (≈ S${vn_drop_val:,.0f} per quarter at risk). "
        f"It is a **retention** problem, not a demand problem → see *Sales actions*.\n"
        f"- **Singapore is mature** (single-digit growth, equipment declining) — growth there comes from cross-selling "
        f"into existing accounts rather than new ones.")


# --------------------------------------------------------------------------- forecasting
def forecasting():
    st.title("Forecasting · better than the 6-month average")
    f = c.forecasts()
    bt, acc = f["backtest"], f["accuracy"]
    from onerecord.forecast import wape
    ab = bt[bt["product"] != "C"]
    k = st.columns(4)
    k[0].metric("Today: 6-month average", f"{wape(ab, 'baseline_ma6'):.1%} error")
    k[1].metric("OneRecord calendar model", f"{wape(ab, 'calendar_model'):.1%} error",
                f"{wape(ab, 'calendar_model') / wape(ab, 'baseline_ma6') - 1:+.0%}", delta_color="inverse")
    k[2].metric("Series improved", f"{(acc[acc['product'] != 'C'].Improvement > 0).sum()} of 10", help="Products A and B")
    k[3].metric("Horizon tested", "1–3 mo", help="Rolling origins Apr–Sep 2026; error = WAPE")
    st.caption("Error = WAPE (sum of absolute errors ÷ actual units), products A and B, forecasting 1–3 months "
               "ahead from every month Apr–Sep 2026 using only the data available at the time.")

    with st.expander("How the model works (plain English)", expanded=False):
        st.markdown(
            "The 6-month average treats every month the same, so it is always late for dengue season and the "
            "December budget flush. The OneRecord model keeps each series' level and trend and adds the **business "
            "calendar Lives Group already knows**: dengue season by country (Product A), the hospital year-end "
            "push, the January lull and public holidays (Lunar New Year, Tet, Songkran, Hari Raya). It learns *how "
            "big* each effect is from all five countries at once, which is why 12–18 months of history is enough. "
            "No black box, no model to babysit: re-run monthly, check the error report.")
        eff = pd.DataFrame({"Calendar effect": list(f["effects"]), "Learned impact on units": list(f["effects"].values())})
        st.dataframe(eff, hide_index=True, column_config={
            "Learned impact on units": st.column_config.NumberColumn(format="percent")})

    s1, s2 = st.columns(2)
    country = s1.selectbox("Country", c.COUNTRY_ORDER, index=c.COUNTRY_ORDER.index("TH"),
                           format_func=lambda k: f"{k} · {COUNTRIES[k]}")
    prod = s2.selectbox("Product", list(PRODUCTS), format_func=lambda p: c.PRODUCT_LABEL[p])
    hist = f["Y"].loc[(country, prod)]
    one = bt[(bt.country == country) & (bt["product"] == prod) & (bt.horizon == 1)]
    ahead = f["ahead"][(f["ahead"].country == country) & (f["ahead"]["product"] == prod)]
    fig = go.Figure()
    fig.add_scatter(x=hist.index, y=hist.values, name="Actual orders", mode="lines+markers", line=dict(color="#333"))
    fig.add_scatter(x=one.month, y=one.baseline_ma6, name="6-month average (back-test)", mode="lines+markers",
                    line=dict(color="#aaa", dash="dot"))
    fig.add_scatter(x=one.month, y=one.calendar_model, name="Calendar model (back-test)", mode="lines+markers",
                    line=dict(color=COLORS[prod]))
    fig.add_scatter(x=ahead.month, y=ahead.baseline_ma6, name="6-month average · next 3 months", mode="lines",
                    line=dict(color="#aaa", dash="dash"))
    fig.add_scatter(x=ahead.month, y=ahead.calendar_model, name="Calendar model · next 3 months", mode="lines+markers",
                    line=dict(color=COLORS[prod], dash="dash"))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="units",
                      legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    row = acc[(acc.country == country) & (acc["product"] == prod)].iloc[0]
    st.caption(f"{country} · {prod}: 6-month average error {row['MA6 error']:.1%} → model {row['Model error']:.1%}.")

    st.markdown("##### Accuracy by series")
    st.dataframe(acc, hide_index=True, width="stretch", column_config={
        "MA6 error": st.column_config.NumberColumn(format="percent"),
        "Model error": st.column_config.NumberColumn(format="percent"),
        "Improvement": st.column_config.NumberColumn(format="percent")})
    st.markdown(
        "**Honest read-out.** The biggest gains are Product A in ID, MY and TH, where the average misses dengue "
        "season. Singapore A gets slightly worse (its dengue effect is milder than the regional estimate — "
        "next step: a country-specific effect once more history exists). Vietnam B is poor for both: lost "
        "accounts are a customer problem, handled by the drop-off alerts, not by a calendar. Product C is too "
        "lumpy to forecast monthly — plan it from the sales pipeline instead.")


# --------------------------------------------------------------------------- actions
def actions():
    st.title("Sales actions from clean data")
    cmp = c.regional()["compare"]
    k = st.columns(4)
    k[0].metric("Customer records in SAP", cmp["raw_customers"])
    k[1].metric("Real customers", cmp["clean_customers"], f"{cmp['clean_customers'] - cmp['raw_customers']}",
                delta_color="off")
    k[2].metric("Drop-off alerts", len(cmp["clean_drop"]), f"{len(cmp['clean_drop']) - len(cmp['raw_drop'])} vs raw",
                delta_color="inverse", help="Raw records raise extra false alarms: a 'lost' customer that simply "
                                            "started ordering under a duplicate record")
    k[3].metric("Cross-sell leads", len(cmp["clean_xsell"]), f"{len(cmp['clean_xsell']) - len(cmp['raw_xsell'])} vs raw",
                delta_color="inverse", help="Raw records invent false gaps: one hospital split into an 'A-only' and "
                                            "a 'B-only' record")

    t1, t2 = st.tabs(["🚨 Customers dropping off", "➕ Cross-sell opportunities"])
    with t1:
        d = cmp["clean_drop"]
        st.markdown(f"**{len(d)} established customers** ordered ≥40% less last quarter than both the same quarter "
                    f"last year and their own recent average. Value at risk ≈ **S${d.value_at_risk_per_q.sum():,.0f} "
                    f"per quarter**.")
        st.dataframe(d[["name", "country", "units_last_q", "units_same_q_last_year", "change", "value_at_risk_per_q",
                        "last_order"]], hide_index=True, width="stretch", column_config={
            "change": st.column_config.NumberColumn("YoY", format="percent"),
            "value_at_risk_per_q": st.column_config.NumberColumn("At risk / quarter (SGD)", format="%.0f")})
        st.markdown("**Action:** account manager calls the top 10 by value within two weeks; log the reason "
                    "(competitor, budget, service issue) so patterns surface by country.")
    with t2:
        x = cmp["clean_xsell"]
        st.markdown(f"**{len(x)} customers** buy one of A/B but not the other, while most similar customers buy both. "
                    f"Estimated potential ≈ **S${x.est_value_sgd_per_year.sum() / 1e6:,.1f}M a year** if all converted.")
        st.dataframe(x[["name", "country", "segment", "buys", "missing", "peers_buying_both", "est_units_per_year",
                        "est_value_sgd_per_year"]], hide_index=True, width="stretch", column_config={
            "est_value_sgd_per_year": st.column_config.NumberColumn("Potential / year (SGD)", format="%.0f")})
        c.assumption("potential = their volume of the product they buy × the median ratio among peers who buy both. "
                     "A ceiling, not a forecast; the business case uses 10% conversion.")
        st.markdown("**Action:** bundle offer (reagents + consumables) for hospitals and labs on the list, starting "
                    "with SPD/QTS joint accounts in MY and ID where growth is strongest.")


# --------------------------------------------------------------------------- inbound
def inbound():
    st.title("Orders vs enquiries vs master-data requests")
    st.caption("The regional view counts **orders only**. This is how incoming emails get separated.")
    t = c.triage()
    main, hold = t["main"], t["holdout"]
    st.markdown("**Design:** route by channel first (dedicated order inbox, form for setup requests) → rules the "
                "MDM team can read → an off-the-shelf AI prompt for what's left → a person for anything unsure. "
                "No custom model to train or maintain.")
    k = st.columns(4)
    for i, lab in enumerate(["purchase_order", "enquiry", "follow_up", "mdm_request"]):
        k[i].metric(classify.LABELS[lab], int((main.predicted == lab).sum()))
    by = main[main.predicted != "review"].groupby(["country", "predicted"]).size().reset_index(name="emails")
    by["predicted"] = by.predicted.map(classify.LABELS)
    fig = px.bar(by, x="country", y="emails", color="predicted", category_orders={"country": c.COUNTRY_ORDER},
                 barmode="stack")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
    st.plotly_chart(fig, width="stretch")

    a, b = st.columns(2)
    with a:
        st.markdown("##### Accuracy on the mailbox sample (660 emails)")
        acc = (main.predicted == main.true_label).mean()
        st.metric("Correct", f"{acc:.0%}", help="Synthetic emails share templates with the rules — optimistic")
        st.caption("Optimistic: the synthetic emails follow patterns the rules were written for.")
    with b:
        st.markdown("##### Stress test: 24 hand-written messy emails")
        auto = hold[hold.predicted != "review"]
        st.metric("Labelled by rules", f"{len(auto)} of {len(hold)}",
                  f"{(auto.predicted == auto.true_label).mean():.0%} of those correct" if len(auto) else None,
                  delta_color="off")
        st.caption("Rules never guessed wrong — but most real-world mess goes to review. That gap is exactly "
                   "what the AI step is for.")
    st.markdown("##### Review queue (stress test)")
    cols = ["message_id", "subject", "body", "predicted", "reason", "true_label"]
    view = hold[cols].copy()
    if classify.ai_available():
        if st.button("Run AI step on the review queue", type="primary"):
            res = [classify.ai_classify(r.subject, r.body, r.attachment_name) if r.predicted == "review"
                   else (r.predicted, r.confidence, r.reason) for r in hold.itertuples()]
            st.session_state["ai_res"] = res
        if "ai_res" in st.session_state:
            view["after_ai"], _, view["ai_reason"] = zip(*st.session_state["ai_res"])
    else:
        st.caption("AI step not configured (set ANTHROPIC_API_KEY to try it). In production this is Power "
                   "Automate's AI prompt action with the same plain-English instructions.")
    st.dataframe(view, hide_index=True, width="stretch")
    with st.expander("The AI instructions (editable by the MDM team, no retraining)"):
        st.code(classify.AI_PROMPT, language="text")


# --------------------------------------------------------------------------- data quality
def quality():
    st.title("Data quality · duplicates across SPD, QTS, QTG")
    q = c.data_quality()
    cl, pairs, s = q["clusters"], q["pairs"], q["score"]
    dups = cl[cl.cluster_size > 1]
    k = st.columns(4)
    k[0].metric("Customer records", len(cl))
    k[1].metric("Duplicate records found", int((cl.record_id != cl.golden_id).sum()),
                f"{(cl.record_id != cl.golden_id).mean():.0%} of records", delta_color="off")
    k[2].metric("Sent to human review", int((pairs.decision == "review").sum()))
    k[3].metric("Duplicate item codes", len(q["item_map"]))
    st.caption(f"Validated against the synthetic answer key: precision {s['precision']:.0%}, recall {s['recall']:.0%} "
               f"({s['found_pairs']} of {s['true_pairs']} duplicate pairs). Real SAP data will be messier — "
               "the review band exists for that.")
    st.markdown("**How matching works:** compare records in the same country only · same registration number → "
                "match, different → never · otherwise cleaned-up name similarity (typos, 'Hosp.' vs 'Hospital', "
                "missing 'Pte Ltd', upper case) backed by city and address · acronyms like *NUH*. Deterministic "
                "rules and thresholds — nothing to retrain.")
    st.markdown("##### Duplicate groups")
    show = dups.sort_values(["golden_id", "created_date"])[["golden_id", "record_id", "customer_name", "country",
                                                             "created_by_entity", "created_date", "registration_no"]]
    st.dataframe(show, hide_index=True, width="stretch")
    if q["item_map"]:
        st.markdown("##### Duplicate items")
        items = c.raw()["items"].set_index("item_code")
        for dup, keep in q["item_map"].items():
            st.markdown(f"- `{dup}` *{items.loc[dup, 'description']}* is a copy of `{keep}` "
                        f"*{items.loc[keep, 'description']}* — merging them stops the dengue test looking like "
                        f"it is declining in TH/VN.")
    st.markdown("##### Why it matters")
    st.markdown("Country totals don't change when duplicates merge — every order is still counted once. What changes "
                "is **everything per customer**: the customer count, who looks 'lost' (orders moved to a new record), "
                "and who looks like an 'A-only' buyer (the B orders sit on another entity's record). "
                "See *Sales actions* for the raw-vs-clean difference.")


# --------------------------------------------------------------------------- business case
def business_case():
    st.title("Business case")
    d = c.raw()
    bd, touch = c.process_baseline()
    st.markdown("##### Today: where an 18.8-day request actually goes")
    k = st.columns(4)
    k[0].metric("Median request → SAP", f"{d['requests'].cycle_days.median():.1f} days")
    k[1].metric("Slowest 10%", f"{d['requests'].cycle_days.quantile(.9):.0f}+ days")
    k[2].metric("Bounced back at least once", f"{(d['requests'].bounces > 0).mean():.0%}")
    k[3].metric("Actual work in that time", f"{touch:.1%}", help="Everything else is waiting")
    fig = px.bar(bd, x="share", y="stage", orientation="h", text_auto=".0%")
    fig.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0), xaxis_tickformat=".0%", yaxis_title="",
                      xaxis_title="share of elapsed time")
    st.plotly_chart(fig, width="stretch")

    st.markdown("##### With OneRecord (re-simulated on the same 150 requests)")
    s = st.columns(3)
    bounce = s[0].slider("Bounces avoided by the smart form", 0.5, 1.0, 0.9, 0.05)
    notice = s[1].slider("Approver delay removed by Teams cards", 0.0, 0.7, 0.5, 0.05,
                         help="Share of each approver's wait that was 'didn't see the email'")
    esc = s[2].slider("Escalate after (business days)", 2, 6, 4)
    sim = process.simulate(d["requests"], d["steps"], bounce_avoided=bounce, notice_cut=notice,
                           escalate_after_days=esc)
    now_med, fut_med = sim.cycle_days.median(), sim.future_days.median()
    k = st.columns(3)
    k[0].metric("Median request → SAP", f"{fut_med:.1f} days", f"{fut_med - now_med:+.1f} days", delta_color="inverse")
    k[1].metric("Slowest 10%", f"{sim.future_days.quantile(.9):.1f} days",
                f"{sim.future_days.quantile(.9) - sim.cycle_days.quantile(.9):+.1f}", delta_color="inverse")
    k[2].metric("Faster", f"{1 - fut_med / now_med:.0%}")
    long = pd.concat([sim.assign(scenario="Today (email)", days=sim.cycle_days),
                      sim.assign(scenario="OneRecord", days=sim.future_days)])
    fig = px.histogram(long, x="days", color="scenario", barmode="overlay", nbins=40, opacity=0.7)
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
    st.plotly_chart(fig, width="stretch")
    c.assumption("parallel approvals use the same historical approver waits; only the levers above change. "
                 "Simulated, not measured — validate in a 4-week pilot with one entity.")

    st.markdown("##### Value and cost (first year)")
    cmp, q = c.regional()["compare"], c.data_quality()
    ncv = process.new_customer_value(d["requests"], c.regional()["clean"], q["clusters"], now_med - fut_med)
    v = st.columns(5)
    hours = v[0].number_input("MDM + approver hours saved per request", 0.0, 5.0, 1.5, 0.25)
    rate = v[1].number_input("Loaded cost per hour (SGD)", 20, 150, 50, 5)
    save_rate = v[2].slider("Drop-offs recovered", 0.0, 0.5, 0.2, 0.05)
    conv = v[3].slider("Cross-sell conversion", 0.0, 0.3, 0.1, 0.02)
    margin = v[4].slider("Gross margin on sales", 0.1, 0.6, 0.3, 0.05,
                         help="Revenue items count as gross profit, not order value")
    req_per_year = len(d["requests"]) / 1.5
    benefits = {
        "Staff time (requests × hours × rate)": req_per_year * hours * rate,
        "Gross profit pulled forward (new accounts live sooner)": ncv["pulled_forward_per_year"] * margin,
        "Gross profit kept (drop-offs recovered)": cmp["clean_drop"].value_at_risk_per_q.sum() * 4 * save_rate * margin,
        "Gross profit from cross-sell": cmp["clean_xsell"].est_value_sgd_per_year.sum() * conv * margin,
    }
    cc = st.columns(4)
    dev_weeks = cc[0].number_input("Power Platform contractor (weeks)", 0, 20, 8)
    dev_rate = cc[1].number_input("Contractor rate / week (SGD)", 1000, 8000, 4000, 250)
    da_weeks = cc[2].number_input("Data analyst (weeks)", 0, 20, 5)
    licence = cc[3].number_input("Licences + AI credits / year (SGD)", 0, 20000, 3000, 500)
    costs = {"Workflow build (contractor)": dev_weeks * dev_rate, "Analytics build": da_weeks * 3000,
             "Licences & AI credits": licence, "MDM team time (rules, training) ~4 weeks": 4 * 40 * rate}
    b, co = sum(benefits.values()), sum(costs.values())
    left, right = st.columns(2)
    left.dataframe(pd.DataFrame({"Benefit (SGD / year)": benefits}).round(0), width="stretch")
    right.dataframe(pd.DataFrame({"Cost (SGD, year 1)": costs}).round(0), width="stretch")
    k = st.columns(3)
    k[0].metric("Annual benefit", f"S${b:,.0f}")
    k[1].metric("Year-1 cost", f"S${co:,.0f}")
    k[2].metric("Payback", f"{12 * co / b:.1f} months" if b else "—")
    c.assumption("sales-driven lines are counted at gross margin, not order value; rates, hours, margin and "
                 "conversion are placeholders to agree with Lives Group. Staff time alone does NOT pay back the build — "
                 "the case rests on accounts going live faster and on sales acting on the signals clean data unlocks.")
