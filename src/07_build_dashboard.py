"""Step 4d - Self-contained interactive HTML dashboard.

Embeds the analysis outputs directly into a single .html file with no external
requests, so it opens from disk and can be emailed as one attachment.

Run:  python src/07_build_dashboard.py
"""

import json

import pandas as pd

from config import DASHBOARD_DIR, OUTPUT_DIR, TABLE_DIR, ensure_dirs

TEMPLATE_PATH = None  # markup is generated below
OUT = DASHBOARD_DIR / "index.html"


def collect() -> dict:
    payload = json.loads((OUTPUT_DIR / "analysis_summary.json").read_text())

    def rows(name: str) -> list[dict]:
        # Convert NaN to None so the embedded payload is valid JSON, not just
        # valid JavaScript - the first month's MoM growth is legitimately absent.
        df = pd.read_csv(TABLE_DIR / f"{name}.csv")
        return df.astype(object).where(df.notna(), None).to_dict("records")

    return {
        "kpis": payload["kpis"],
        "answers": payload["answers"],
        "state": rows("sales_by_state"),
        "category": rows("sales_by_category"),
        "profit_category": rows("profit_by_category"),
        "products": rows("top_10_products"),
        "payment": rows("sales_by_payment_mode"),
        "trend": rows("monthly_sales_trend"),
        "significance": rows("significance_tests"),
    }


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>E-Commerce Sales Dashboard</title>
<style>
/* Palette from the validated reference instance. Categorical slots 1-5 and the
   surfaces below were checked with the data-viz validator in BOTH modes; the
   dark steps are chosen for the dark surface, never an automatic flip. */
:root {
  color-scheme: light;
  --surface-0:#f4f4f1; --surface-1:#fcfcfb; --surface-2:#eceae5;
  --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#8a8880;
  --rule:#e6e5e1; --grid:#e6e5e1;
  --s1:#2a78d6; --s2:#008300; --s3:#e87ba4; --s4:#eda100; --s5:#1baf7a;
  --deemph:#c9c8c2; --accent-soft:rgba(42,120,214,.10);
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --surface-0:#111110; --surface-1:#1a1a19; --surface-2:#232322;
    --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#8f8e85;
    --rule:#333331; --grid:#2e2e2c;
    --s1:#3987e5; --s2:#008300; --s3:#d55181; --s4:#c98500; --s5:#199e70;
    --deemph:#4a4a47; --accent-soft:rgba(57,135,229,.16);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface-0:#111110; --surface-1:#1a1a19; --surface-2:#232322;
  --text-primary:#ffffff; --text-secondary:#c3c2b7; --text-muted:#8f8e85;
  --rule:#333331; --grid:#2e2e2c;
  --s1:#3987e5; --s2:#008300; --s3:#d55181; --s4:#c98500; --s5:#199e70;
  --deemph:#4a4a47; --accent-soft:rgba(57,135,229,.16);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--surface-0); color:var(--text-primary);
  font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1220px;margin:0 auto;padding:32px 20px 72px}

header{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
h1{font-size:26px;line-height:1.2;margin:0 0 6px;letter-spacing:-.02em}
.sub{color:var(--text-secondary);font-size:14px;margin:0}
.theme-btn{
  background:var(--surface-1);color:var(--text-secondary);border:1px solid var(--rule);
  border-radius:8px;padding:8px 14px;font-size:13px;cursor:pointer;font-family:inherit;
}
.theme-btn:hover{color:var(--text-primary);border-color:var(--text-muted)}

.banner{
  margin:24px 0 8px;padding:16px 18px;border-radius:10px;
  background:var(--accent-soft);border:1px solid var(--rule);
  border-left:3px solid var(--s1);
}
.banner strong{display:block;margin-bottom:4px;font-size:14px}
.banner p{margin:0;font-size:13.5px;color:var(--text-secondary)}

/* 6 tiles: fits one row on desktop, halves on tablet, stacks on phone -
   never leaves a single orphan tile on its own row. */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:24px 0 8px}
@media (max-width:1080px){ .kpis{grid-template-columns:repeat(3,1fr)} }
@media (max-width:640px){ .kpis{grid-template-columns:repeat(2,1fr)} }
.kpi{background:var(--surface-1);border:1px solid var(--rule);border-radius:10px;padding:16px 18px}
.kpi .label{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-muted);margin-bottom:6px}
.kpi .value{font-size:23px;font-weight:650;letter-spacing:-.025em;line-height:1.15}
.kpi .note{font-size:12px;color:var(--text-secondary);margin-top:4px}

.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(470px,1fr));gap:18px;margin-top:18px}
.card{background:var(--surface-1);border:1px solid var(--rule);border-radius:12px;padding:20px 20px 14px;min-width:0}
.card.full{grid-column:1/-1}
.card h2{font-size:15.5px;margin:0 0 4px;letter-spacing:-.01em}
.card .cap{font-size:12.5px;color:var(--text-secondary);margin:0 0 14px}
.chart{width:100%;overflow-x:auto}
svg{display:block;max-width:100%;height:auto}

.toggle{
  background:none;border:1px solid var(--rule);color:var(--text-muted);
  border-radius:6px;padding:4px 10px;font-size:11.5px;cursor:pointer;
  font-family:inherit;margin-top:10px;
}
.toggle:hover{color:var(--text-primary)}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:10px}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--rule)}
th:first-child,td:first-child{text-align:left}
th{color:var(--text-muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.hidden{display:none}

.legend{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:10px}
.legend span{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-secondary)}
.swatch{width:11px;height:11px;border-radius:3px;flex:none}

.tip{
  position:fixed;pointer-events:none;opacity:0;transition:opacity .1s;
  background:var(--surface-1);border:1px solid var(--rule);border-radius:8px;
  padding:8px 11px;font-size:12.5px;box-shadow:0 6px 22px rgba(0,0,0,.16);
  z-index:50;max-width:260px;color:var(--text-primary);
}
.tip .t-title{font-weight:650;margin-bottom:3px}
.tip .t-row{color:var(--text-secondary);white-space:nowrap}

footer{margin-top:36px;padding-top:18px;border-top:1px solid var(--rule);
  font-size:12.5px;color:var(--text-muted)}
@media (max-width:560px){ .grid{grid-template-columns:1fr} h1{font-size:22px} }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>E-Commerce Sales Dashboard</h1>
      <p class="sub" id="sub"></p>
    </div>
    <button class="theme-btn" id="themeBtn" type="button">Toggle theme</button>
  </header>

  <div class="banner">
    <strong>Read the confidence column before acting on any ranking.</strong>
    <p id="bannerText"></p>
  </div>

  <section class="kpis" id="kpis"></section>
  <section class="grid" id="grid"></section>

  <footer>
    Built from 15,000 cleaned order records.
    Charts use a colourblind-validated palette; every ranking is accompanied by
    the statistical test that tells you whether it means anything.
  </footer>
</div>
<div class="tip" id="tip"></div>

<script>
const DATA = __DATA__;

/* ---------- formatting ---------- */
const money = v => {
  const a = Math.abs(v);
  if (a >= 1e7) return 'Rs ' + (v/1e7).toFixed(2) + ' Cr';
  if (a >= 1e5) return 'Rs ' + (v/1e5).toFixed(2) + ' L';
  if (a >= 1e3) return 'Rs ' + (v/1e3).toFixed(1) + 'K';
  return 'Rs ' + v.toFixed(0);
};
const num = v => v.toLocaleString('en-IN');
const pct = v => (v*100).toFixed(1) + '%';
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* ---------- tooltip ---------- */
const tip = document.getElementById('tip');
function showTip(e, title, rows){
  tip.innerHTML = '<div class="t-title">'+title+'</div>' +
    rows.map(r => '<div class="t-row">'+r+'</div>').join('');
  tip.style.opacity = 1;
  const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX + pad, y = e.clientY + pad;
  if (x + w > innerWidth - 8)  x = e.clientX - w - pad;
  if (y + h > innerHeight - 8) y = e.clientY - h - pad;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
const hideTip = () => tip.style.opacity = 0;

/* ---------- svg helpers ---------- */
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs){
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}
function svgRoot(w, h){
  const s = el('svg', {viewBox:`0 0 ${w} ${h}`, width:'100%', role:'img'});
  s.style.minWidth = Math.min(w, 420) + 'px';
  return s;
}
function yGrid(svg, scale, x0, x1, ticks, fmt){
  ticks.forEach(t => {
    svg.appendChild(el('line', {x1:x0, x2:x1, y1:scale(t), y2:scale(t),
      stroke:css('--grid'), 'stroke-width':1}));
    const lb = el('text', {x:x0-9, y:scale(t)+4, 'text-anchor':'end',
      fill:css('--text-muted'), 'font-size':11});
    lb.textContent = fmt(t);
    svg.appendChild(lb);
  });
}
function niceTicks(max, count){
  const raw = max / count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1,2,2.5,5,10].map(m=>m*mag).find(s => s >= raw) || mag*10;
  const out = [];
  for (let v = 0; v <= max*1.0001; v += step) out.push(v);
  return out;
}

/* ---------- chart: vertical bars (nominal -> one hue) ---------- */
function barChart(host, rows, keyF, valF, fmtV, tipRows){
  const W=620, H=300, L=76, R=18, T=14, B=54;
  const svg = svgRoot(W,H);
  const max = Math.max(...rows.map(valF));
  const y = v => T + (H-T-B) * (1 - v/(max*1.14));
  yGrid(svg, y, L, W-R, niceTicks(max*1.14, 4), fmtV);

  const bw = (W-L-R)/rows.length;
  rows.forEach((r,i) => {
    const v = valF(r), h = y(0)-y(v);
    const x = L + i*bw + bw*0.19, w = bw*0.62;
    // 4px rounded data-end, anchored square to the baseline.
    const rect = el('path', {d:
      `M${x},${y(0)} L${x},${y(v)+4} Q${x},${y(v)} ${x+4},${y(v)}
       L${x+w-4},${y(v)} Q${x+w},${y(v)} ${x+w},${y(v)+4} L${x+w},${y(0)} Z`,
      fill:css('--s1')});
    rect.style.cursor='pointer';
    rect.addEventListener('mousemove', e => showTip(e, keyF(r), tipRows(r)));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);

    const val = el('text', {x:x+w/2, y:y(v)-7, 'text-anchor':'middle',
      fill:css('--text-secondary'), 'font-size':11});
    val.textContent = fmtV(v);
    svg.appendChild(val);

    const lab = el('text', {x:x+w/2, y:H-B+20, 'text-anchor':'middle',
      fill:css('--text-secondary'), 'font-size':11});
    lab.textContent = keyF(r);
    svg.appendChild(lab);
  });
  svg.appendChild(el('line',{x1:L,x2:W-R,y1:y(0),y2:y(0),
    stroke:css('--rule'),'stroke-width':1}));
  host.appendChild(svg);
}

/* ---------- chart: horizontal bars ---------- */
function barChartH(host, rows, keyF, valF, fmtV, tipRows){
  const W=620, rowH=27, L=118, R=76, T=8;
  const H = T + rows.length*rowH + 16;
  const svg = svgRoot(W,H);
  const max = Math.max(...rows.map(valF));
  const x = v => L + (W-L-R) * (v/(max*1.05));

  rows.forEach((r,i) => {
    const v = valF(r), yy = T + i*rowH, bh = rowH*0.64;
    const bar = el('path', {d:
      `M${L},${yy} L${x(v)-4},${yy} Q${x(v)},${yy} ${x(v)},${yy+4}
       L${x(v)},${yy+bh-4} Q${x(v)},${yy+bh} ${x(v)-4},${yy+bh} L${L},${yy+bh} Z`,
      fill:css('--s1')});
    bar.style.cursor='pointer';
    bar.addEventListener('mousemove', e => showTip(e, keyF(r), tipRows(r)));
    bar.addEventListener('mouseleave', hideTip);
    svg.appendChild(bar);

    const lab = el('text', {x:L-10, y:yy+bh/2+4, 'text-anchor':'end',
      fill:css('--text-secondary'), 'font-size':11.5});
    lab.textContent = keyF(r);
    svg.appendChild(lab);

    const val = el('text', {x:x(v)+8, y:yy+bh/2+4,
      fill:css('--text-secondary'), 'font-size':11});
    val.textContent = fmtV(v);
    svg.appendChild(val);
  });
  host.appendChild(svg);
}

/* ---------- chart: line with crosshair ---------- */
function lineChart(host, rows){
  const W=1140, H=330, L=84, R=26, T=16, B=62;
  const svg = svgRoot(W,H);
  const vals = rows.map(r=>r.Total_Sales);
  const max = Math.max(...vals), mean = vals.reduce((a,b)=>a+b,0)/vals.length;
  const y = v => T + (H-T-B) * (1 - v/(max*1.18));   // zero-baseline, always
  const x = i => L + (W-L-R) * (i/(rows.length-1));

  yGrid(svg, y, L, W-R, niceTicks(max*1.18, 4), money);

  // +/-5% reference band: makes "flat" visible instead of merely asserted.
  svg.appendChild(el('rect', {x:L, y:y(mean*1.05), width:W-L-R,
    height:y(mean*0.95)-y(mean*1.05), fill:css('--s1'), opacity:.10}));
  svg.appendChild(el('line', {x1:L, x2:W-R, y1:y(mean), y2:y(mean),
    stroke:css('--text-muted'), 'stroke-width':1.5, 'stroke-dasharray':'5 4'}));
  const bl = el('text', {x:W-R, y:y(mean*1.05)-6, 'text-anchor':'end',
    fill:css('--text-muted'), 'font-size':11});
  bl.textContent = 'mean +/-5%';
  svg.appendChild(bl);

  const d = rows.map((r,i)=>`${i?'L':'M'}${x(i)},${y(r.Total_Sales)}`).join(' ');
  svg.appendChild(el('path', {d, fill:'none', stroke:css('--s1'),
    'stroke-width':2, 'stroke-linejoin':'round'}));

  rows.forEach((r,i) => {
    svg.appendChild(el('circle', {cx:x(i), cy:y(r.Total_Sales), r:4.5,
      fill:css('--s1'), stroke:css('--surface-1'), 'stroke-width':1.5}));
    if (i % 2 === 0){
      const lb = el('text', {x:x(i), y:H-B+22, 'text-anchor':'end',
        fill:css('--text-muted'), 'font-size':10.5,
        transform:`rotate(-45 ${x(i)} ${H-B+22})`});
      lb.textContent = r.Order_Month;
      svg.appendChild(lb);
    }
  });

  // Crosshair layer - hit target spans the full plot height, not just the dot.
  const cross = el('line', {x1:0,x2:0,y1:T,y2:y(0), stroke:css('--text-muted'),
    'stroke-width':1, 'stroke-dasharray':'3 3', opacity:0});
  svg.appendChild(cross);
  const band = el('rect', {x:L, y:T, width:W-L-R, height:y(0)-T,
    fill:'transparent'});
  band.style.cursor='crosshair';
  band.addEventListener('mousemove', e => {
    const box = svg.getBoundingClientRect();
    const rel = (e.clientX-box.left)/box.width*W;
    let i = Math.round((rel-L)/((W-L-R)/(rows.length-1)));
    i = Math.max(0, Math.min(rows.length-1, i));
    const r = rows[i];
    cross.setAttribute('x1', x(i)); cross.setAttribute('x2', x(i));
    cross.setAttribute('opacity', 1);
    const g = r.MoM_Growth;
    showTip(e, r.Order_Month, [
      'Sales: ' + money(r.Total_Sales),
      'Profit: ' + money(r.Total_Profit),
      'Orders: ' + num(r.Total_Orders),
      (g===null||g===undefined||isNaN(g)) ? 'MoM: n/a' : 'MoM: ' + pct(g),
    ]);
  });
  band.addEventListener('mouseleave', () => { cross.setAttribute('opacity',0); hideTip(); });
  svg.appendChild(band);
  svg.appendChild(el('line',{x1:L,x2:W-R,y1:y(0),y2:y(0),
    stroke:css('--rule'),'stroke-width':1}));
  host.appendChild(svg);
}

/* ---------- chart: significance dot plot ---------- */
function sigChart(host, rows){
  const W=1140, rowH=54, L=142, R=40, T=18;
  const H = T + rows.length*rowH + 44;
  const svg = svgRoot(W,H);
  const lo = Math.min(...rows.map(r=>r.Margin_CI_Low));
  const hi = Math.max(...rows.map(r=>r.Margin_CI_High));
  const pad = (hi-lo)*0.06;
  const x = v => L + (W-L-R) * ((v-(lo-pad))/((hi+pad)-(lo-pad)));

  svg.appendChild(el('line', {x1:x(0), x2:x(0), y1:T-4, y2:T+rows.length*rowH,
    stroke:css('--text-primary'), 'stroke-width':1.5}));
  const zl = el('text', {x:x(0), y:H-16, 'text-anchor':'middle',
    fill:css('--text-muted'), 'font-size':11});
  zl.textContent = 'zero = a tie';
  svg.appendChild(zl);

  rows.forEach((r,i) => {
    const yy = T + i*rowH + rowH*0.55;
    svg.appendChild(el('line', {x1:x(r.Margin_CI_Low), x2:x(r.Margin_CI_High),
      y1:yy, y2:yy, stroke:css('--deemph'), 'stroke-width':7,
      'stroke-linecap':'round'}));
    const dot = el('circle', {cx:x(r.Observed_Margin), cy:yy, r:6,
      fill:css('--s1'), stroke:css('--surface-1'), 'stroke-width':1.5});
    dot.style.cursor='pointer';
    dot.addEventListener('mousemove', e => showTip(e,
      r.Dimension.replace(/_/g,' '), [
        'Leader: ' + r.Leader,
        'Runner-up: ' + r.Runner_Up,
        'Margin: ' + money(r.Observed_Margin),
        '95% CI: ' + money(r.Margin_CI_Low) + ' to ' + money(r.Margin_CI_High),
        'Holds top in ' + pct(r.Leader_Retention_Rate) + ' of resamples',
        'Verdict: ' + r.Verdict,
      ]));
    dot.addEventListener('mouseleave', hideTip);
    svg.appendChild(dot);

    const lab = el('text', {x:L-12, y:yy+4, 'text-anchor':'end',
      fill:css('--text-primary'), 'font-size':12.5});
    lab.textContent = r.Dimension.replace(/_/g,' ');
    svg.appendChild(lab);

    // Halo the label: the zero rule runs behind this band and would
    // otherwise strike the text through.
    const note = el('text', {x:x(r.Margin_CI_Low), y:yy-14,
      fill:css('--text-secondary'), 'font-size':11,
      stroke:css('--surface-1'), 'stroke-width':3.5,
      'paint-order':'stroke fill', 'stroke-linejoin':'round'});
    note.textContent = r.Leader + ' holds top in ' +
      pct(r.Leader_Retention_Rate) + ' of resamples';
    svg.appendChild(note);
  });
  host.appendChild(svg);
}

/* ---------- card scaffolding ---------- */
function card(title, caption, full, render, tableCols, tableRows){
  const c = document.createElement('div');
  c.className = 'card' + (full ? ' full' : '');
  c.innerHTML = '<h2>'+title+'</h2><p class="cap">'+caption+'</p>';
  const chart = document.createElement('div');
  chart.className = 'chart';
  c.appendChild(chart);
  render(chart);

  if (tableCols){
    const btn = document.createElement('button');
    btn.className = 'toggle'; btn.type = 'button';
    btn.textContent = 'Show data table';
    const tbl = document.createElement('div');
    tbl.className = 'hidden';
    tbl.innerHTML = '<table><thead><tr>' +
      tableCols.map(h=>'<th>'+h[0]+'</th>').join('') + '</tr></thead><tbody>' +
      tableRows.map(r=>'<tr>' + tableCols.map(h=>'<td>'+h[1](r)+'</td>').join('') +
        '</tr>').join('') + '</tbody></table>';
    btn.onclick = () => {
      const open = !tbl.classList.contains('hidden');
      tbl.classList.toggle('hidden');
      btn.textContent = open ? 'Show data table' : 'Hide data table';
    };
    c.appendChild(btn); c.appendChild(tbl);
  }
  document.getElementById('grid').appendChild(c);
}

/* ---------- render ---------- */
function render(){
  document.getElementById('grid').innerHTML = '';
  const k = DATA.kpis, a = DATA.answers;

  document.getElementById('sub').textContent =
    num(k.total_orders) + ' orders  |  ' + k.date_from + ' to ' + k.date_to +
    '  |  ' + num(k.unique_customers) + ' customers';
  document.getElementById('bannerText').textContent =
    'All five headline rankings sit within random variation. Bootstrap testing ' +
    'puts the top state at only ' + pct(DATA.significance.find(s=>s.Dimension==='State').Leader_Retention_Rate) +
    ' likelihood of actually being first, and the 24-month trend fits a flat ' +
    'line (R2 = 0.008). The figures below are accurate; the rankings between ' +
    'them are not decision-grade.';

  const kpis = [
    ['Total Sales', money(k.total_sales), num(k.total_orders)+' orders'],
    ['Total Profit', money(k.total_profit), pct(k.overall_profit_margin)+' margin'],
    ['Total Orders', num(k.total_orders), num(k.unique_customers)+' customers'],
    ['Quantity Sold', num(k.total_quantity), (k.total_quantity/k.total_orders).toFixed(2)+' per order'],
    ['Avg Discount', pct(k.average_discount), 'range 0-30%'],
    ['Avg Order Value', money(k.average_order_value), 'per order'],
  ];
  document.getElementById('kpis').innerHTML = kpis.map(([l,v,n]) =>
    '<div class="kpi"><div class="label">'+l+'</div><div class="value">'+v+
    '</div><div class="note">'+n+'</div></div>').join('');

  const salesCols = [
    ['Name', r=>r.k], ['Sales', r=>money(r.Total_Sales)],
    ['Profit', r=>money(r.Total_Profit)], ['Orders', r=>num(r.Total_Orders)],
    ['Margin', r=>pct(r.Profit_Margin)], ['Share', r=>pct(r.Sales_Share)],
  ];
  const withKey = (rows, key) => rows.map(r => ({...r, k:r[key]}));

  const tipFor = r => ['Sales: '+money(r.Total_Sales),
    'Profit: '+money(r.Total_Profit), 'Orders: '+num(r.Total_Orders),
    'Margin: '+pct(r.Profit_Margin), 'Share: '+pct(r.Sales_Share)];

  card('Sales by State',
    'Rajasthan leads on paper. It holds that lead in only ' +
    pct(DATA.significance.find(s=>s.Dimension==='State').Leader_Retention_Rate) +
    ' of bootstrap resamples, so the order is effectively interchangeable.',
    false, host => barChart(host, DATA.state, r=>r.State, r=>r.Total_Sales, money, tipFor),
    salesCols, withKey(DATA.state, 'State'));

  card('Sales by Product Category',
    'All five categories fall within 5% of one another (permutation p = 0.58).',
    false, host => barChart(host, DATA.category, r=>r.Product_Category,
      r=>r.Total_Sales, money, tipFor),
    salesCols, withKey(DATA.category, 'Product_Category'));

  card('Top 10 Products by Sales',
    'Revenue spread across the top ten is under 12% - consistent with uniform ' +
    'random demand rather than genuine bestsellers.',
    false, host => barChartH(host, DATA.products, r=>r.Product_Name,
      r=>r.Total_Sales, money, tipFor),
    salesCols, withKey(DATA.products, 'Product_Name'));

  card('Orders by Payment Mode',
    'Five modes, each carrying about 20% of orders. An even split, not a preference.',
    false, host => barChart(host, DATA.payment, r=>r.Payment_Mode,
      r=>r.Total_Orders, num, tipFor),
    [['Mode', r=>r.k], ['Orders', r=>num(r.Total_Orders)],
     ['Sales', r=>money(r.Total_Sales)], ['Share', r=>pct(r.Sales_Share)]],
    withKey(DATA.payment, 'Payment_Mode'));

  card('Monthly Sales Trend',
    'Zero-baseline axis. Sales hold flat across 24 months; the wobble stays ' +
    'inside +/-5% of the mean and fits a flat line (R2 = 0.008).',
    true, host => lineChart(host, DATA.trend),
    [['Month', r=>r.Order_Month], ['Sales', r=>money(r.Total_Sales)],
     ['Profit', r=>money(r.Total_Profit)], ['Orders', r=>num(r.Total_Orders)],
     ['MoM', r=>(r.MoM_Growth===null||isNaN(r.MoM_Growth))?'n/a':pct(r.MoM_Growth)]],
    DATA.trend);

  card('Is any ranking real?',
    'Bootstrap 95% confidence interval on each leader\\'s margin over its ' +
    'nearest rival. Every interval crosses zero - no leader is statistically ' +
    'distinguishable from its runner-up.',
    true, host => sigChart(host, DATA.significance),
    [['Dimension', r=>r.Dimension.replace(/_/g,' ')], ['Leader', r=>r.Leader],
     ['Runner-up', r=>r.Runner_Up], ['Margin', r=>money(r.Observed_Margin)],
     ['CI low', r=>money(r.Margin_CI_Low)], ['CI high', r=>money(r.Margin_CI_High)],
     ['Holds top', r=>pct(r.Leader_Retention_Rate)],
     ['p', r=>r.Permutation_P_Value.toFixed(3)], ['Verdict', r=>r.Verdict]],
    DATA.significance);
}

/* ---------- theme ---------- */
const btn = document.getElementById('themeBtn');
btn.onclick = () => {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark'
    || (!document.documentElement.hasAttribute('data-theme')
        && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
  render();   // re-read the CSS variables for the new mode
};
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', render);
render();
</script>
</body>
</html>
"""


def main() -> None:
    ensure_dirs()
    print("=" * 70)
    print("STEP 4d - INTERACTIVE DASHBOARD")
    print("=" * 70 + "\n")

    data = collect()
    html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")

    kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(OUT.parent.parent)} ({kb:.0f} KB, self-contained)")
    print("Open it directly in a browser - no server or network access needed.")


if __name__ == "__main__":
    main()
