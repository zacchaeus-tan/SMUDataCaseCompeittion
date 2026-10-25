// Keep every table's columns where they are: Streamlit's tables let you drag a column header to reorder the
// columns, with no setting to turn it off. Swallow presses on the header row before the table sees them.
// Runs in a hidden component frame and works on the page around it (views/common.py: page_style).
(function () {
  const w = window.parent, d = w.document;
  if (w.__orTableLock) return;  // one listener per page, however many times Streamlit reruns
  w.__orTableLock = true;

  const HEADER = 36;  // the header row's height in Streamlit tables (px)
  const block = (e) => {
    // presses land on the table's scroll layer, which sits over the canvas the table is drawn on
    const table = e.target.closest && e.target.closest('[data-testid="stDataFrame"]');
    const grid = table && table.querySelector("canvas");
    if (!grid) return;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - grid.getBoundingClientRect().top;
    if (y >= 0 && y < HEADER) { e.stopPropagation(); e.preventDefault(); }
  };
  for (const type of ["pointerdown", "mousedown", "touchstart"]) {
    d.addEventListener(type, block, { capture: true, passive: false });
  }
})();
