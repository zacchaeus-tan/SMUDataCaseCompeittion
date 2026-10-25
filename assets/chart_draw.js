// Draw each line chart from left to right the first time it comes on screen, and again whenever a filter changes
// what it shows (styles: assets/app.css). Scrolling away and back doesn't replay it.
// Runs in a hidden component frame and works on the page around it (views/common.py: page_style).
(function () {
  const w = window.parent, d = w.document;
  if (w.__orChartDraw) return;  // one watcher per page, however many times Streamlit reruns
  w.__orChartDraw = true;

  const waiting = new Set();
  // Streamlit may swap in a new chart element when the data changes (e.g. a filter), so remember each chart by page
  // and position, with a fingerprint of the data it last drew: same data = already drawn, new data = draw again
  const drawn = new Map();
  const keyOf = (chart) => w.location.pathname + "#" +
    [...d.querySelectorAll('[data-testid="stMain"] [data-testid="stPlotlyChart"]')].indexOf(chart);
  const dataOf = (chart) => {
    const p = chart.querySelector(".js-plotly-plot");
    return ((p && p._fullData) || []).map((t) => {  // _fullData: the y values decoded from Streamlit's binary form
      const y = t.y ? Array.from(t.y) : [];
      return `${t.name || ""}:${y.length}:${y[0]}:${y[y.length - 1]}:${t.x ? t.x[0] : ""}`;
    }).join("|");
  };

  // a chart counts as on screen once a third of it (or a third of the window, for tall charts) is visible
  const onScreen = (chart) => {
    const r = chart.getBoundingClientRect();
    if (!r.height) return false;
    const shown = Math.min(r.bottom, w.innerHeight) - Math.max(r.top, 0);
    return shown >= Math.min(r.height, w.innerHeight) / 3;
  };

  const play = (chart) => {
    waiting.delete(chart);
    drawn.set(keyOf(chart), dataOf(chart));
    chart.dataset.orDrawn = "1";
    chart.classList.remove("or-wait", "or-play");
    void chart.offsetWidth;  // restart the animation if it was still running
    chart.classList.add("or-play");
    // once drawn, drop the animation so a redraw with the same data (e.g. a resize) shows straight away
    const done = () => chart.classList.remove("or-play");
    chart.addEventListener("animationend", done, { once: true });
    w.setTimeout(done, 1300);  // backstop in case the end event never arrives (animation is 1.1s)
  };

  const check = () => {
    for (const chart of waiting) {
      if (!chart.isConnected) waiting.delete(chart);
      else if (onScreen(chart)) play(chart);
    }
  };

  // a filter change makes Streamlit redraw the page in steps, and charts briefly shift position or show stale data;
  // hide a changed chart straight away, but only decide whether it really changed once the page has settled
  const settling = new Map();
  const settle = (chart) => {
    settling.delete(chart);
    if (!chart.isConnected) return;
    if (drawn.get(keyOf(chart)) === dataOf(chart)) {  // a false alarm: show it as it was
      chart.classList.remove("or-wait");
      chart.dataset.orDrawn = "1";
    } else {
      waiting.add(chart);
      check();
    }
  };

  // hold back every new or changed line chart until it's in view; runs before the browser paints, so nothing flashes
  const scan = () => {
    d.querySelectorAll('[data-testid="stPlotlyChart"]').forEach((chart) => {
      if (waiting.has(chart) || !chart.querySelector(".cartesianlayer .scatterlayer")) return;
      const key = keyOf(chart), data = dataOf(chart);
      if (!data) return;  // Plotly hasn't finished drawing it yet
      if (settling.has(chart)) {  // still changing: wait for it to stop
        w.clearTimeout(settling.get(chart));
        settling.set(chart, w.setTimeout(() => settle(chart), 250));
        return;
      }
      if (drawn.get(key) === data) { chart.dataset.orDrawn = "1"; return; }  // nothing new to draw
      delete chart.dataset.orDrawn;  // otherwise app.css keeps showing the old drawing
      chart.classList.add("or-wait");
      if (drawn.has(key)) settling.set(chart, w.setTimeout(() => settle(chart), 250));  // a filter changed it
      else waiting.add(chart);  // first time on this page
    });
    check();
  };

  new w.MutationObserver(scan).observe(d.body, { childList: true, subtree: true });
  // the page scrolls inside Streamlit's main panel, not the window, so listen on the whole document
  d.addEventListener("scroll", check, { capture: true, passive: true });
  w.addEventListener("resize", check, { passive: true });
  w.setInterval(() => { if (waiting.size) check(); }, 300);  // backstop: never leave a chart hidden
  scan();
})();
