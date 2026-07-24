// Shared graph engine (ADR-008): ONE module drives both surfaces -- the History
// page's #graph-page and the front page's #home-graph -- so lens/scale behavior
// parity holds by construction. Relocated from graph.html's inline script, not
// rewritten: each page configures the engine through its mount's data-view /
// data-scale attributes; without a mount (empty record, A18 kin) nothing runs.
//
// Shell rendering only. Raw lens: the server windows entries (pure core) and
// returns exactly the stored ones; missing days become nulls on the daily grid,
// so uPlot draws honest gaps -- no zeros, no interpolation (spanGaps: false).
// Trend lens: the server smooths over the FULL record and windows the OUTPUT
// (ADR-004); the line covers every day on the grid, so no gaps exist to draw.
(function () {
  const page =
    document.getElementById("graph-page") || document.getElementById("home-graph");
  if (page === null) return; // no graph area offered: the front page stays simple

  const DAY_MS = 86400000;

  // Device-local day (A5, extended to reads by fix-device-day-reads): the
  // phone frames "today" for the window; the server validates and bounds
  // the claim, so the 1W week never loses its oldest day after the UTC
  // rollover of an ordinary evening.
  function deviceLocalDay() {
    const now = new Date();
    const pad = (part) => String(part).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  }

  const chartHost = document.getElementById("chart");
  const emptyInvite = document.getElementById("empty-invite");
  let chart = null;

  function dailyGridSeries(entries) {
    const weightByDay = new Map(entries.map((e) => [e.date, e.weight_kg]));
    const dayStamps = entries.map((e) => Date.parse(e.date + "T00:00:00Z")).sort((a, b) => a - b);
    const xs = [];
    const ys = [];
    for (let t = dayStamps[0]; t <= dayStamps[dayStamps.length - 1]; t += DAY_MS) {
      const isoDay = new Date(t).toISOString().slice(0, 10);
      xs.push(t / 1000);
      ys.push(weightByDay.has(isoDay) ? weightByDay.get(isoDay) : null);
    }
    return [xs, ys];
  }

  function trendGridSeries(points) {
    return [
      points.map((p) => Date.parse(p.date + "T00:00:00Z") / 1000),
      points.map((p) => p.trend_kg),
    ];
  }

  // Single palette (US-009, ADR-007 decision 3): every chart color is read from
  // the theme's --chart-* tokens at build time, so the canvas always matches the
  // scheme the page currently wears. No color literals live in this module.
  function paletteTokens() {
    const styles = getComputedStyle(document.documentElement);
    const token = (name) => styles.getPropertyValue(name).trim();
    return { axis: token("--chart-axis"), grid: token("--chart-grid"),
             raw: token("--chart-raw"), trend: token("--chart-trend") };
  }

  function themedAxis(palette, extra) {
    return Object.assign(
      { stroke: palette.axis, grid: { stroke: palette.grid }, ticks: { stroke: palette.grid } },
      extra,
    );
  }

  function renderChart(data, lineOptionsFor) {
    if (chart !== null) chart.destroy();
    const palette = paletteTokens();
    chart = new uPlot(
      {
        width: Math.min(document.body.clientWidth - 32, 800),
        height: 320,
        series: [{}, lineOptionsFor(palette)],
        axes: [themedAxis(palette, {}), themedAxis(palette, { label: "kg" })],
      },
      data,
      chartHost,
    );
  }

  function clearChart() {
    if (chart !== null) { chart.destroy(); chart = null; }
  }

  // The first-log invite lives on the History page only; the front page never
  // mounts the engine over an empty record, so there is nothing to invite.
  function showInvite(inviting) {
    if (emptyInvite !== null) emptyInvite.hidden = !inviting;
  }

  async function showRaw(scale) {
    const history = await (
      await fetch(`/entries?scale=${encodeURIComponent(scale)}&today=${deviceLocalDay()}`)
    ).json();
    showInvite(history.invite_first_log);
    if (history.entries.length === 0) return clearChart();
    renderChart(dailyGridSeries(history.entries), (palette) => ({
      label: "kg",
      stroke: palette.raw,
      spanGaps: false,
      points: { show: true },
    }));
  }

  async function showTrend(scale) {
    const trend = await (
      await fetch(`/trend?scale=${encodeURIComponent(scale)}&today=${deviceLocalDay()}`)
    ).json();
    showInvite(trend.points.length === 0);
    if (trend.points.length === 0) return clearChart();
    renderChart(trendGridSeries(trend.points), (palette) => ({
      label: "trend kg",
      stroke: palette.trend,
      width: 2,
    }));
  }

  async function showGraph(scale) {
    page.dataset.scale = scale;
    for (const button of document.querySelectorAll("#scale-picker button")) {
      button.setAttribute("aria-pressed", String(button.dataset.window === scale));
    }
    if (page.dataset.view === "trend") await showTrend(scale);
    else await showRaw(scale);
  }

  // One-tap lens toggle (US-005): flips the view, keeps selected_time_scale --
  // toggling never resets the chosen window.
  async function showView(view) {
    page.dataset.view = view;
    for (const button of document.querySelectorAll("#view-toggle button")) {
      button.setAttribute("aria-pressed", String(button.dataset.lens === view));
    }
    await showGraph(page.dataset.scale);
  }

  for (const button of document.querySelectorAll("#scale-picker button")) {
    button.addEventListener("click", () => showGraph(button.dataset.window));
  }
  for (const button of document.querySelectorAll("#view-toggle button")) {
    button.addEventListener("click", () => showView(button.dataset.lens));
  }
  // Mid-session scheme flip (US-009): re-render through the existing showGraph,
  // so the selected lens (page.dataset.view) and time scale survive by construction.
  matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => showGraph(page.dataset.scale));
  showView(page.dataset.view);
})();
