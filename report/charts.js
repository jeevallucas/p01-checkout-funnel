// Charts and tables for the report pages. Observable Plot is passed in from each page's OJS
// runtime, so this module has no imports of its own. Colours follow docs/design-brief.md.

export const COLORS = {
  ink: "#202124",
  rule: "#D8DEE4",
  context: "#9AA3AD",
  mobile: "#0072B2",
  coupon: "#007A5E",
  drop: "#D55E00",
  dropText: "#A84300",
};

export const STEP_LABELS = new Map([
  ["view_item", "View an item"],
  ["add_to_cart", "Add to cart"],
  ["begin_checkout", "Begin checkout"],
  ["add_shipping_info", "Add shipping details"],
  ["add_payment_info", "Add payment details"],
  ["purchase", "Purchase"],
]);

const STEP_ORDER = [...STEP_LABELS.values()];
const LABEL_FONT_PX = 13;
const MISSING = "—";

const percentFormat = new Intl.NumberFormat("en-US", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const usdFormat = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});
const countFormat = new Intl.NumberFormat("en-US");

// Formatters print a dash instead of "NaN" when a data file did not load.
const guard = (format) => (value) => (Number.isFinite(value) ? format(value) : MISSING);
export const formatPercent = guard((value) => percentFormat.format(value));
export const formatUsd = guard((value) => usdFormat.format(value));
export const formatCount = guard((value) => countFormat.format(value));
export const formatPoints = guard((share) => {
  const points = Math.abs(share * 100).toFixed(1);
  if (points === "0.0") return "0.0";
  return share < 0 ? `−${points}` : `+${points}`;
});
export const intervalText = (low, high) => `${formatPercent(low)} to ${formatPercent(high)}`;

// Loads every CSV a page needs without throwing, so one failed file shows one clear message
// instead of an error in every cell. `files` maps a name to a FileAttachment.
export async function loadResults(files) {
  const loaded = await Promise.all(
    Object.entries(files).map(async ([name, file]) => {
      try {
        return { name, rows: await file.csv({ typed: true }) };
      } catch {
        return { name, rows: [], failed: file.name };
      }
    }),
  );
  return {
    data: Object.fromEntries(loaded.map(({ name, rows }) => [name, rows])),
    missing: loaded.filter((entry) => entry.failed).map((entry) => entry.failed),
  };
}

export function dataAlert(missing) {
  const alert = document.createElement("div");
  if (missing.length === 0) return alert;
  alert.className = "data-error";
  alert.setAttribute("role", "alert");
  const heading = document.createElement("p");
  heading.className = "data-error-title";
  heading.textContent = "Some numbers on this page did not load.";
  const detail = document.createElement("p");
  const command = document.createElement("code");
  command.textContent = "quarto render report";
  detail.append(
    `The browser could not read ${missing.join(", ")}. Reload the page. If the dashes stay, ` +
      "the site build is missing those files; rebuild it with ",
    command,
    ".",
  );
  alert.append(heading, detail);
  return alert;
}

export function stopShare(conversion, stepName) {
  const rows = conversion.filter((row) => row.step_name === stepName);
  const entered = rows.reduce((sum, row) => sum + row.sessions_entered, 0);
  const reached = rows.reduce((sum, row) => sum + row.sessions_reached, 0);
  return 1 - reached / entered;
}

// Wrap width for chart labels, in ems, so long labels break instead of running off a phone.
const labelEms = (width, margins = 24) => Math.floor((width - margins) / LABEL_FONT_PX);

const halo = { stroke: "white", strokeWidth: 4, paintOrder: "stroke" };

function figure({ title, subtitle, legend, plot }) {
  const element = document.createElement("figure");
  element.className = "chart";
  const heading = document.createElement("p");
  heading.className = "chart-title";
  heading.textContent = title;
  const note = document.createElement("p");
  note.className = "chart-subtitle";
  note.textContent = subtitle;
  element.append(heading, note);
  if (!plot) {
    const empty = document.createElement("p");
    empty.className = "chart-empty";
    empty.textContent = "This chart needs data that did not load; see the message at the top.";
    element.append(empty);
    return element;
  }
  if (legend) {
    const key = document.createElement("div");
    key.className = "chart-legend";
    for (const { label, color } of legend) {
      const item = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.style.background = color;
      item.append(swatch, label);
      key.append(item);
    }
    element.append(key);
  }
  // The chart is one image to assistive technology; its numbers are in the table below it.
  plot.setAttribute("role", "img");
  for (const group of plot.querySelectorAll("g[aria-label]")) group.removeAttribute("aria-label");
  element.append(plot);
  return element;
}

function intervalTitle(label, rate, low, high, detail) {
  return `${label}: ${formatPercent(rate)} (95% interval ${intervalText(low, high)})${
    detail ? `, ${detail}` : ""
  }`;
}

// The bold element: mobile and desktop step conversion, with the step to fund marked.
export function stepLadder(Plot, conversion, { width, highlightStep, title, subtitle }) {
  const devices = [
    { key: "mobile", label: "Mobile", color: COLORS.mobile, dy: -5 },
    { key: "desktop", label: "Desktop", color: COLORS.context, dy: 5 },
  ];
  const rows = conversion
    .filter((row) => devices.some((device) => device.key === row.device_category))
    .map((row) => ({ ...row, step: STEP_LABELS.get(row.step_name) }));
  const legend = devices.map(({ label, color }) => ({ label, color }));
  if (rows.length === 0) return figure({ title, subtitle });
  const stop = formatPercent(stopShare(conversion, highlightStep));
  const narrow = width < 560;
  const labels = STEP_ORDER.map((step) => {
    const highlighted = step === STEP_LABELS.get(highlightStep);
    const suffix = narrow ? `${stop} stop here` : `${stop} stop here on every device`;
    return { step, text: highlighted ? `${step}: ${suffix}` : step, highlighted };
  });
  const ticks = narrow ? 5 : 10;
  const plot = Plot.plot({
    width,
    height: STEP_ORDER.length * 58 + 48,
    marginLeft: 8,
    marginRight: 16,
    marginTop: 24,
    marginBottom: 40,
    ariaLabel: title,
    ariaDescription: subtitle,
    x: {
      domain: [0, 1],
      tickFormat: "%",
      ticks,
      label: "Sessions at the previous step that reach this step",
      labelAnchor: "left",
      labelArrow: "none",
    },
    y: { domain: STEP_ORDER, axis: null, paddingInner: 0, paddingOuter: 0.1 },
    marks: [
      Plot.barX(
        labels.filter((label) => label.highlighted),
        { y: "step", x1: 0, x2: 1, fill: COLORS.drop, fillOpacity: 0.09 },
      ),
      Plot.gridX({ stroke: COLORS.rule, strokeOpacity: 1, ticks }),
      Plot.ruleX([0], { stroke: COLORS.ink }),
      ...devices.flatMap((device) => {
        const deviceRows = rows.filter((row) => row.device_category === device.key);
        return [
          Plot.ruleY(deviceRows, {
            y: "step",
            x1: "conversion_low",
            x2: "conversion_high",
            stroke: device.color,
            strokeWidth: 2,
            dy: device.dy,
          }),
          Plot.dot(deviceRows, {
            y: "step",
            x: "conversion",
            r: 5,
            fill: device.color,
            stroke: "white",
            strokeWidth: 2,
            dy: device.dy,
            title: (row) =>
              intervalTitle(
                `${device.label}, ${row.step}`,
                row.conversion,
                row.conversion_low,
                row.conversion_high,
                `${formatCount(row.sessions_reached)} of ${formatCount(row.sessions_entered)} sessions`,
              ),
          }),
        ];
      }),
      // Plot's fontWeight is a constant, so highlighted and plain labels are separate marks.
      ...[true, false].map((highlighted) =>
        Plot.text(
          labels.filter((label) => label.highlighted === highlighted),
          {
            y: "step",
            x: 0,
            dx: 4,
            dy: -21,
            text: "text",
            textAnchor: "start",
            lineWidth: labelEms(width),
            fill: highlighted ? COLORS.dropText : COLORS.ink,
            fontWeight: highlighted ? 600 : 400,
            ...halo,
          },
        ),
      ),
    ],
  });
  return figure({ title, subtitle, legend, plot });
}

// Mobile minus desktop, with a zero line: every interval crossing zero means no clear gap.
export function gapChart(Plot, gaps, { width, title, subtitle }) {
  const rows = gaps.map((row) => ({ ...row, step: STEP_LABELS.get(row.step_name) }));
  if (rows.length === 0) return figure({ title, subtitle });
  const plot = Plot.plot({
    width,
    height: STEP_ORDER.length * 50 + 48,
    marginLeft: 8,
    marginRight: 16,
    marginTop: 24,
    marginBottom: 40,
    ariaLabel: title,
    ariaDescription: subtitle,
    x: {
      domain: [-0.05, 0.05],
      tickFormat: formatPoints,
      ticks: 5,
      label: "Mobile minus desktop, percentage points",
      labelAnchor: "left",
      labelArrow: "none",
    },
    y: { domain: STEP_ORDER, axis: null, paddingOuter: 0.1 },
    marks: [
      Plot.gridX({ stroke: COLORS.rule, strokeOpacity: 1, ticks: 5 }),
      Plot.ruleX([0], { stroke: COLORS.ink }),
      Plot.ruleY(rows, {
        y: "step",
        x1: "gap_low",
        x2: "gap_high",
        stroke: COLORS.mobile,
        strokeWidth: 2,
      }),
      Plot.dot(rows, {
        y: "step",
        x: "gap",
        r: 5,
        fill: COLORS.mobile,
        stroke: "white",
        strokeWidth: 2,
        title: (row) =>
          `${row.step}: ${formatPoints(row.gap)} points (95% interval ${formatPoints(
            row.gap_low,
          )} to ${formatPoints(row.gap_high)})`,
      }),
      Plot.text(rows, {
        y: "step",
        x: -0.05,
        dx: 4,
        dy: -17,
        text: "step",
        textAnchor: "start",
        fill: COLORS.ink,
        ...halo,
      }),
    ],
  });
  return figure({ title, subtitle, plot });
}

export const SEGMENT_LABELS = new Map([
  ["all first-time buyers", "All first-time buyers"],
  ["coupon", "Coupon at first purchase"],
  ["no coupon", "No coupon"],
  ["paid search", "Paid search"],
  ["direct", "Direct"],
  ["organic", "Organic search"],
  ["referral", "Referral"],
  ["unknown", "Medium unknown"],
]);

export const segmentLabel = (segment) => SEGMENT_LABELS.get(segment) ?? segment;

// Repeat purchase by segment for one follow-up window, against the all-buyer rate.
export function repeatChart(Plot, cohorts, { width, windowDays, title, subtitle }) {
  const windowRows = cohorts.filter((row) => row.window_days === windowDays);
  const overall = windowRows.find((row) => row.split === "all");
  const rows = windowRows
    .filter((row) => row.split !== "all")
    .map((row) => ({ ...row, label: segmentLabel(row.segment) }));
  if (!overall || rows.length === 0) return figure({ title, subtitle });
  // An empty band separates the coupon split from the medium split.
  const spacer = " ";
  const couponLabels = ["Coupon at first purchase", "No coupon"];
  const order = [
    ...couponLabels,
    spacer,
    ...[...SEGMENT_LABELS.values()].filter(
      (label) => !couponLabels.includes(label) && rows.some((row) => row.label === label),
    ),
  ];
  const colorOf = (row) => (row.segment === "coupon" ? COLORS.coupon : COLORS.context);
  const plot = Plot.plot({
    width,
    height: order.length * 46 + 64,
    marginLeft: 8,
    marginRight: 16,
    marginTop: 36,
    marginBottom: 40,
    ariaLabel: title,
    ariaDescription: subtitle,
    x: {
      domain: [0, 0.15],
      tickFormat: "%",
      ticks: 5,
      label: `First-time buyers who bought again within ${windowDays} days`,
      labelAnchor: "left",
      labelArrow: "none",
    },
    y: { domain: order, axis: null, paddingOuter: 0.1 },
    marks: [
      Plot.gridX({ stroke: COLORS.rule, strokeOpacity: 1, ticks: 5 }),
      Plot.ruleX([0], { stroke: COLORS.ink }),
      Plot.ruleX([overall.repeat_rate], { stroke: COLORS.ink, strokeWidth: 1 }),
      Plot.text([overall], {
        x: "repeat_rate",
        frameAnchor: "top",
        dy: -24,
        dx: 4,
        textAnchor: "start",
        text: (row) => `All first-time buyers ${formatPercent(row.repeat_rate)}`,
        fill: COLORS.ink,
      }),
      Plot.ruleY(rows, {
        y: "label",
        x1: "repeat_rate_low",
        x2: "repeat_rate_high",
        stroke: colorOf,
        strokeWidth: 2,
      }),
      Plot.dot(rows, {
        y: "label",
        x: "repeat_rate",
        r: 5,
        fill: colorOf,
        stroke: "white",
        strokeWidth: 2,
        title: (row) =>
          intervalTitle(
            row.label,
            row.repeat_rate,
            row.repeat_rate_low,
            row.repeat_rate_high,
            `${formatCount(row.repeat_buyers)} of ${formatCount(row.first_time_buyers)} buyers`,
          ),
      }),
      ...[true, false].map((isCoupon) =>
        Plot.text(
          rows.filter((row) => (row.segment === "coupon") === isCoupon),
          {
            y: "label",
            x: 0,
            dx: 4,
            dy: -16,
            text: (row) => `${row.label} (${formatCount(row.first_time_buyers)} buyers)`,
            textAnchor: "start",
            lineWidth: labelEms(width),
            fill: isCoupon ? COLORS.coupon : COLORS.ink,
            fontWeight: isCoupon ? 600 : 400,
            ...halo,
          },
        ),
      ),
    ],
  });
  return figure({ title, subtitle, plot });
}

// The smallest payment-step lift an A/B test detects, all devices against mobile only, at the
// 92-day average traffic and at January's quieter pace.
export function testReachChart(Plot, tests, { width, weeks, title, subtitle }) {
  const rows = tests
    .filter((row) => row.test_weeks === weeks)
    .map((row) => ({
      ...row,
      label: `${row.scope === "all devices" ? "All devices" : "Mobile only"}, ${row.traffic_pace}`,
      color: row.scope === "all devices" ? COLORS.drop : COLORS.mobile,
      highlighted: row.scope === "all devices",
    }));
  if (rows.length === 0) return figure({ title, subtitle });
  const plot = Plot.plot({
    width,
    height: rows.length * 58 + 48,
    marginLeft: 8,
    marginRight: 72,
    marginTop: 28,
    marginBottom: 40,
    ariaLabel: title,
    ariaDescription: subtitle,
    x: {
      domain: [0, 10],
      ticks: 5,
      label: "Smallest detectable lift, percentage points",
      labelAnchor: "left",
      labelArrow: "none",
    },
    y: {
      domain: rows.map((row) => row.label),
      axis: null,
      paddingInner: 0.6,
      paddingOuter: 0.3,
    },
    marks: [
      Plot.gridX({ stroke: COLORS.rule, strokeOpacity: 1, ticks: 5 }),
      Plot.barX(rows, {
        y: "label",
        x: "detectable_lift_points",
        fill: "color",
        title: (row) =>
          `${row.label}: ${row.detectable_lift_points.toFixed(1)} points with ${formatCount(
            row.sessions_per_arm,
          )} sessions per arm`,
      }),
      Plot.ruleX([0], { stroke: COLORS.ink }),
      ...[true, false].map((highlighted) =>
        Plot.text(
          rows.filter((row) => row.highlighted === highlighted),
          {
            y: "label",
            x: 0,
            dx: 4,
            dy: -18,
            text: "label",
            textAnchor: "start",
            lineWidth: labelEms(width, 80),
            fill: highlighted ? COLORS.dropText : COLORS.ink,
            fontWeight: highlighted ? 600 : 400,
            ...halo,
          },
        ),
      ),
      Plot.text(rows, {
        y: "label",
        x: "detectable_lift_points",
        dx: 6,
        text: (row) => `${row.detectable_lift_points.toFixed(1)} points`,
        textAnchor: "start",
        fill: COLORS.ink,
      }),
    ],
  });
  return figure({
    title,
    subtitle,
    legend: [
      { label: "All devices", color: COLORS.drop },
      { label: "Mobile only", color: COLORS.mobile },
    ],
    plot,
  });
}

// A plain table: columns are { label, value(row), numeric }. The caption sits outside the
// scrolling region so it stays readable when a wide table scrolls sideways on a phone.
export function dataTable({ caption, columns, rows, highlight = () => false }) {
  const block = document.createElement("div");
  block.className = "table-block";
  const captionId = `table-${caption.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  const heading = document.createElement("p");
  heading.className = "table-caption";
  heading.id = captionId;
  heading.textContent = caption;
  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.tabIndex = 0;
  wrap.setAttribute("role", "region");
  wrap.setAttribute("aria-labelledby", captionId);
  const table = document.createElement("table");
  table.className = "data-table";
  table.setAttribute("aria-labelledby", captionId);
  const headRow = table.createTHead().insertRow();
  for (const column of columns) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = column.label;
    if (column.numeric) cell.className = "numeric";
    headRow.append(cell);
  }
  const body = table.createTBody();
  for (const row of rows) {
    const tableRow = body.insertRow();
    if (highlight(row)) tableRow.className = "highlight";
    for (const column of columns) {
      const cell = tableRow.insertCell();
      cell.textContent = column.value(row);
      if (column.numeric) cell.className = "numeric";
    }
  }
  if (rows.length === 0) {
    const cell = body.insertRow().insertCell();
    cell.colSpan = columns.length;
    cell.textContent = "No rows: the data for this table did not load.";
  }
  wrap.append(table);
  const hint = document.createElement("span");
  hint.className = "scroll-hint";
  hint.textContent = " Scroll sideways for more columns.";
  heading.append(hint);
  block.append(heading, wrap);
  // Show the hint only while the table is wider than its container; re-checked on resize.
  new ResizeObserver(() => {
    block.classList.toggle("scrolls", wrap.scrollWidth > wrap.clientWidth + 1);
  }).observe(wrap);
  return block;
}
