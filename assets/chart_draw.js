// Draw each line chart from left to right once, the first time it comes on screen (styles: assets/app.css).
// Runs in a hidden component frame and works on the page around it (views/common.py: page_style).
(function () {
  const w = window.parent, d = w.document;
  if (w.__orChartDraw) return;  // one watcher per page, however many times Streamlit reruns
  w.__orChartDraw = true;

  const waiting = new Set();
  // Streamlit may swap in a new chart element when the data changes (e.g. a filter), so remember drawn charts by
  // page and position, not by element: a chart that has drawn once never draws again until the page is reloaded
  const drawn = new Set();
  const keyOf = (chart) => w.location.pathname + "#" +
    [...d.querySelectorAll('[data-testid="stMain"] [data-testid="stPlotlyChart"]')].indexOf(chart);

  // a chart counts as on screen once a third of it (or a third of the window, for tall charts) is visible
  const onScreen = (chart) => {
    const r = chart.getBoundingClientRect();
    if (!r.height) return false;
    const shown = Math.min(r.bottom, w.innerHeight) - Math.max(r.top, 0);
    return shown >= Math.min(r.height, w.innerHeight) / 3;
  };

  const play = (chart) => {
    waiting.delete(chart);
    drawn.add(keyOf(chart));
    chart.dataset.orDrawn = "1";
    chart.classList.remove("or-wait");
    chart.classList.add("or-play");
    // once drawn, drop the animation so a later redraw (e.g. a filter change) shows straight away
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

  // hold back every new line chart until it's in view; runs before the browser paints, so nothing flashes
  const scan = () => {
    d.querySelectorAll('[data-testid="stPlotlyChart"]').forEach((chart) => {
      if (chart.dataset.orDrawn || waiting.has(chart)) return;
      if (!chart.querySelector(".cartesianlayer .scatterlayer")) return;
      if (drawn.has(keyOf(chart))) { chart.dataset.orDrawn = "1"; return; }  // a redraw of a chart already shown
      chart.classList.add("or-wait");
      waiting.add(chart);
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
