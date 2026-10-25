// Keep every table's columns where they are: Streamlit's tables let you drag a column header to reorder the
// columns, with no setting to turn it off. A click on a header still sorts the column; only the drag is stopped,
// by hiding the mouse's movement from the table while a header is held down.
// Runs in a hidden component frame and works on the page around it (views/common.py: page_style).
(function () {
  const w = window.parent, d = w.document;
  if (w.__orTableLock) return;  // one set of listeners per page, however many times Streamlit reruns
  w.__orTableLock = true;

  const HEADER = 36;  // the header row's height in Streamlit tables (px)
  let held = false;   // a header is being pressed

  const onHeader = (e) => {
    // presses land on the table's scroll layer, which sits over the canvas the table is drawn on
    const table = e.target.closest && e.target.closest('[data-testid="stDataFrame"]');
    const grid = table && table.querySelector("canvas");
    if (!grid) return false;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - grid.getBoundingClientRect().top;
    return y >= 0 && y < HEADER;
  };
  const press = (e) => { held = onHeader(e); };
  const release = () => { held = false; };
  const move = (e) => { if (held) e.stopPropagation(); };  // no movement = no drag, so the press stays a click

  // listen on the window, in the capture phase, so these run before the table's own listeners
  for (const type of ["pointerdown", "mousedown", "touchstart"]) w.addEventListener(type, press, { capture: true });
  for (const type of ["pointerup", "mouseup", "touchend", "touchcancel"]) {
    w.addEventListener(type, release, { capture: true });
  }
  for (const type of ["pointermove", "mousemove", "touchmove"]) w.addEventListener(type, move, { capture: true });
})();
