from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

from constructionist_math import Graph, demo


@dataclass
class AttractorRow:
    n: int
    v: int
    inflow_resolve: int
    mass: int
    order2_mass: int
    order3_mass: int
    pull_ratio: float
    rank_inflow: int
    rank_pull: int


def _class_mass(graph: Graph, v: int) -> Tuple[int, int, int]:
    key = (int(v), 1)
    node_uids = graph.value_classes.get(key, set())
    if not node_uids:
        return 0, 0, 0
    node_uid = next(iter(node_uids))
    node = graph.nodes_by_uid.get(node_uid)
    if node is None:
        return 0, 0, 0

    # Value-centric semantics: one node per value, many derivation edges per value.
    sigs: set[tuple[str, tuple[int, ...]]] = set()
    grounded_in = 0
    speculative_in = 0
    for edge in graph.edges:
        if edge.output is not node:
            continue
        sig = (str(edge.op), tuple(int(inp.node_uid) for inp in edge.inputs))
        if sig in sigs:
            continue
        sigs.add(sig)
        if all(inp.status == "G" for inp in edge.inputs):
            grounded_in += 1
        else:
            speculative_in += 1
    return len(sigs), grounded_in, speculative_in


def _inflow_counts(graph: Graph) -> Dict[int, int]:
    """
    "Inflow" proxy under value-centric semantics.

    Historically this view used speculative→grounded resolution fan-in.
    With one-node-per-value identity, treat inflow as distinct derivations into v
    whose inputs include at least one speculative node.
    """
    inflow: Dict[int, int] = {}
    sigs_by_v: Dict[int, set[tuple[str, tuple[int, ...]]]] = {}
    for edge in graph.edges:
        out = edge.output
        if out.value is None or int(out.value[1]) != 1:
            continue
        v = int(out.value[0])
        if not any(inp.status == "S" for inp in edge.inputs):
            continue
        sig = (str(edge.op), tuple(int(inp.node_uid) for inp in edge.inputs))
        seen = sigs_by_v.setdefault(v, set())
        if sig in seen:
            continue
        seen.add(sig)
        inflow[v] = inflow.get(v, 0) + 1
    return inflow


def _rank_map(metric_map: Dict[int, float]) -> Dict[int, int]:
    values = sorted(metric_map.keys(), key=lambda v: (-metric_map[v], abs(v), v))
    return {v: idx + 1 for idx, v in enumerate(values)}


def collect_rows(n_min: int, n_max: int) -> List[AttractorRow]:
    rows: List[AttractorRow] = []
    for n in range(n_min, n_max + 1):
        graph = demo(limit=n)
        inflow = _inflow_counts(graph)

        per_v: Dict[int, Dict[str, float]] = {}
        for v in range(-n, n + 1):
            mass, order2, order3 = _class_mass(graph, v)
            in_v = inflow.get(v, 0)
            pull = (in_v / mass) if mass > 0 else 0.0
            per_v[v] = {
                "inflow": float(in_v),
                "mass": float(mass),
                "order2_mass": float(order2),
                "order3_mass": float(order3),
                "pull": float(pull),
            }

        rank_inflow = _rank_map({v: per_v[v]["inflow"] for v in per_v})
        rank_pull = _rank_map({v: per_v[v]["pull"] for v in per_v})

        for v in range(-n, n + 1):
            rows.append(
                AttractorRow(
                    n=n,
                    v=v,
                    inflow_resolve=int(per_v[v]["inflow"]),
                    mass=int(per_v[v]["mass"]),
                    order2_mass=int(per_v[v]["order2_mass"]),
                    order3_mass=int(per_v[v]["order3_mass"]),
                    pull_ratio=float(per_v[v]["pull"]),
                    rank_inflow=int(rank_inflow[v]),
                    rank_pull=int(rank_pull[v]),
                )
            )
    return rows


def _spearman_from_rank_maps(a: Dict[int, int], b: Dict[int, int], keys: List[int]) -> float:
    m = len(keys)
    if m <= 1:
        return 1.0
    sum_d2 = 0.0
    for key in keys:
        d = float(a[key] - b[key])
        sum_d2 += d * d
    denom = m * (m * m - 1)
    if denom <= 0:
        return 1.0
    return 1.0 - (6.0 * sum_d2 / denom)


def build_summary(rows: List[AttractorRow], n_min: int, n_max: int) -> Dict[str, object]:
    by_n: Dict[int, List[AttractorRow]] = {}
    for row in rows:
        by_n.setdefault(row.n, []).append(row)

    top_last: List[Dict[str, object]] = []
    for row in sorted(by_n.get(n_max, []), key=lambda r: (r.rank_inflow, abs(r.v), r.v))[:15]:
        top_last.append(
            {
                "v": row.v,
                "rank_inflow": row.rank_inflow,
                "inflow_resolve": row.inflow_resolve,
                "mass": row.mass,
                "pull_ratio": row.pull_ratio,
            }
        )

    by_v: Dict[int, List[AttractorRow]] = {}
    for row in rows:
        by_v.setdefault(row.v, []).append(row)

    persistence: List[Dict[str, object]] = []
    for v, vals in sorted(by_v.items()):
        vals.sort(key=lambda r: r.n)
        ranks = [r.rank_inflow for r in vals]
        pulls = [r.pull_ratio for r in vals]
        inflows = [r.inflow_resolve for r in vals]
        if not ranks:
            continue
        avg_rank = mean(ranks)
        var_rank = mean([(r - avg_rank) ** 2 for r in ranks])
        std_rank = math.sqrt(var_rank)
        persistence.append(
            {
                "v": v,
                "count": len(vals),
                "n_first": vals[0].n,
                "n_last": vals[-1].n,
                "rank_mean": avg_rank,
                "rank_stddev": std_rank,
                "rank_stability": 1.0 / (1.0 + std_rank),
                "pull_ratio_mean": mean(pulls),
                "inflow_mean": mean(inflows),
            }
        )

    persistence.sort(
        key=lambda row: (
            -int(row["count"] >= 5),
            -row["rank_stability"],
            -row["count"],
            abs(int(row["v"])),
            int(row["v"]),
        )
    )

    spearman_rows: List[Dict[str, object]] = []
    for n in range(n_min + 1, n_max + 1):
        prev_rows = by_n.get(n - 1, [])
        cur_rows = by_n.get(n, [])
        prev_rank = {r.v: r.rank_inflow for r in prev_rows}
        cur_rank = {r.v: r.rank_inflow for r in cur_rows}
        common = sorted(set(prev_rank.keys()).intersection(cur_rank.keys()))
        if not common:
            continue
        rho = _spearman_from_rank_maps(prev_rank, cur_rank, common)
        spearman_rows.append({"n_prev": n - 1, "n_cur": n, "spearman_rank_inflow": rho, "common_values": len(common)})

    return {
        "schema_version": 1,
        "n_min": n_min,
        "n_max": n_max,
        "persistence_min_count_for_priority": 5,
        "row_count": len(rows),
        "top_attractors_at_n_max": top_last,
        "persistence": persistence[:50],
        "consecutive_rank_spearman": spearman_rows,
    }


def write_csv(rows: List[AttractorRow], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "n",
                "v",
                "inflow_resolve",
                "mass",
                "order2_mass",
                "order3_mass",
                "pull_ratio",
                "rank_inflow",
                "rank_pull",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.n,
                    row.v,
                    row.inflow_resolve,
                    row.mass,
                    row.order2_mass,
                    row.order3_mass,
                    f"{row.pull_ratio:.8f}",
                    row.rank_inflow,
                    row.rank_pull,
                ]
            )


def write_json(rows: List[AttractorRow], summary: Dict[str, object], out_json: Path) -> None:
    payload = {
        "summary": summary,
        "rows": [
            {
                "n": r.n,
                "v": r.v,
                "inflow_resolve": r.inflow_resolve,
                "mass": r.mass,
                "order2_mass": r.order2_mass,
                "order3_mass": r.order3_mass,
                "pull_ratio": r.pull_ratio,
                "rank_inflow": r.rank_inflow,
                "rank_pull": r.rank_pull,
            }
            for r in rows
        ],
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _metric_value(row: AttractorRow, metric: str) -> float:
    if metric == "inflow":
        return float(row.inflow_resolve)
    if metric == "mass":
        return float(row.mass)
    if metric == "pull":
        return float(row.pull_ratio)
    if metric == "rank":
        return float(row.rank_inflow)
    return float(row.inflow_resolve)


def _hsl_color_for_t(t: float) -> str:
    clamped = max(0.0, min(1.0, t))
    h = 232.0 - 218.0 * clamped
    s = 90.0
    l = 10.0 + 62.0 * clamped
    return f"hsl({h:.2f}, {s:.2f}%, {l:.2f}%)"


def write_svg(
    rows: List[AttractorRow],
    out_svg: Path,
    *,
    n_min: int,
    n_max: int,
    metric: str = "inflow",
    scale_mode: str = "log",
    v_abs: int = 80,
) -> None:
    v_abs = max(1, int(v_abs))
    row_map: Dict[Tuple[int, int], AttractorRow] = {(row.n, row.v): row for row in rows}
    visible: List[AttractorRow] = []
    for n in range(n_min, n_max + 1):
        for v in range(-v_abs, v_abs + 1):
            row = row_map.get((n, v))
            if row is not None:
                visible.append(row)

    width = 1800
    height = 980
    pad = 56
    grid_w = width - (2 * pad)
    grid_h = height - (2 * pad)
    n_count = max(1, n_max - n_min + 1)
    v_count = max(1, (2 * v_abs) + 1)
    cell_w = grid_w / n_count
    cell_h = grid_h / v_count

    if visible:
        values = [_metric_value(row, metric) for row in visible]
        min_val = min(values)
        max_val = max(values)
    else:
        min_val = 0.0
        max_val = 1.0
    span = max(1e-9, max_val - min_val)
    log_span = max(1e-9, math.log1p(max_val) - math.log1p(min_val))

    lines: List[str] = []
    lines.append(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}'>")
    lines.append("<rect width='100%' height='100%' fill='#0b1220'/>")
    lines.append(
        "<text x='26' y='34' fill='#d7e3ff' font-family='monospace' font-size='20'>"
        "MoO Attractor Map (fallback SVG)"
        "</text>"
    )
    lines.append(
        f"<text x='26' y='58' fill='#8ca1d6' font-family='monospace' font-size='13'>"
        f"N={n_min}..{n_max} | |v|<={v_abs} | metric={metric} | scale={scale_mode}"
        "</text>"
    )

    for n in range(n_min, n_max + 1):
        for v in range(-v_abs, v_abs + 1):
            row = row_map.get((n, v))
            if row is None:
                continue
            raw = _metric_value(row, metric)
            t = (raw - min_val) / span
            if scale_mode == "log" and metric not in {"pull", "rank"}:
                t = (math.log1p(raw) - math.log1p(min_val)) / log_span
            if metric == "rank":
                t = 1.0 - t
            color = _hsl_color_for_t(t)
            x_idx = n - n_min
            y_idx = v_abs - v
            x = pad + (x_idx * cell_w)
            y = pad + (y_idx * cell_h)
            lines.append(
                f"<rect x='{x:.3f}' y='{y:.3f}' width='{cell_w + 0.25:.3f}' height='{cell_h + 0.25:.3f}' "
                f"fill='{color}'/>"
            )

    y_center = pad + (v_abs * cell_h)
    lines.append(
        f"<line x1='{pad}' y1='{y_center:.3f}' x2='{pad + grid_w}' y2='{y_center:.3f}' "
        "stroke='rgba(220,240,255,0.75)' stroke-width='1.25'/>"
    )
    lines.append(
        f"<rect x='{pad}' y='{pad}' width='{grid_w}' height='{grid_h}' fill='none' "
        "stroke='rgba(130,160,220,0.35)' stroke-width='1'/>"
    )
    lines.append("</svg>")

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(
    rows: List[AttractorRow],
    out_html: Path,
    *,
    n_min: int,
    n_max: int,
    fallback_svg_src: str = "",
) -> None:
    payload = json.dumps(
        [
            {
                "n": r.n,
                "v": r.v,
                "inflow": r.inflow_resolve,
                "mass": r.mass,
                "pull": r.pull_ratio,
                "rank": r.rank_inflow,
                "o2": r.order2_mass,
                "o3": r.order3_mass,
            }
            for r in rows
        ],
        separators=(",", ":"),
    )

    default_v_max = min(n_max, 80)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MoO Attractor Map</title>
  <style>
    :root {{
      --bg: #0b1220;
      --fg: #d7e3ff;
      --muted: #8ca1d6;
      --panel: #121b2d;
      --line: #293a61;
    }}
    body {{
      margin: 0;
      background: radial-gradient(circle at 18% 20%, #15233f, var(--bg) 60%);
      color: var(--fg);
      font-family: "IBM Plex Sans", "Fira Sans", sans-serif;
    }}
    .wrap {{
      display: grid;
      grid-template-columns: 360px 1fr;
      min-height: 100vh;
    }}
    .panel {{
      background: color-mix(in oklab, var(--panel) 92%, black);
      border-right: 1px solid var(--line);
      padding: 20px;
      box-sizing: border-box;
    }}
    h1 {{
      margin: 0 0 10px;
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 20px;
    }}
    p {{
      margin: 6px 0 10px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }}
    .row {{ margin: 10px 0; }}
    label {{
      display: block;
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 12px;
      margin-bottom: 5px;
    }}
    input[type=range], select {{
      width: 100%;
      box-sizing: border-box;
    }}
    .mono {{
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.35;
      white-space: pre-wrap;
    }}
    .viewer {{
      position: relative;
      width: 100%;
      min-height: 100vh;
    }}
    canvas, .fallback {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100vh;
      display: block;
    }}
    .fallback {{
      object-fit: contain;
      background: transparent;
      z-index: 0;
    }}
    canvas {{
      z-index: 1;
      opacity: 0;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <h1>MoO Attractor Map</h1>
      <p>N={n_min}..{n_max}. Heatmap over integer anchors v. Color = selected metric.</p>
      <div class="row">
        <label>Metric</label>
        <select id="metric">
          <option value="inflow">inflow_resolve</option>
          <option value="mass">mass</option>
          <option value="pull">pull_ratio</option>
          <option value="rank">rank_inflow (inverted color)</option>
        </select>
      </div>
      <div class="row">
        <label>Color Scale</label>
        <select id="scale">
          <option value="log">log (recommended)</option>
          <option value="linear">linear</option>
        </select>
      </div>
      <div class="row">
        <label>N Min <span id="nMinLabel"></span></label>
        <input id="nMin" type="range" min="{n_min}" max="{n_max}" step="1" value="{n_min}" />
      </div>
      <div class="row">
        <label>N Max <span id="nMaxLabel"></span></label>
        <input id="nMax" type="range" min="{n_min}" max="{n_max}" step="1" value="{n_max}" />
      </div>
      <div class="row">
        <label>|v| Max <span id="vMaxLabel"></span></label>
        <input id="vMax" type="range" min="1" max="{n_max}" step="1" value="{default_v_max}" />
      </div>
      <div class="mono" id="meta"></div>
      <div class="mono" id="hover"></div>
      <div class="mono" id="top"></div>
    </section>
    <section class="viewer">
      <img id="fallback" class="fallback" src="{fallback_svg_src}" alt="Attractor fallback" />
      <canvas id="view"></canvas>
    </section>
  </div>
  <script>
    const rows = {payload};
    const canvas = document.getElementById("view");
    const fallbackEl = document.getElementById("fallback");
    const ctx = canvas ? canvas.getContext("2d") : null;
    const metricEl = document.getElementById("metric");
    const scaleEl = document.getElementById("scale");
    const nMinEl = document.getElementById("nMin");
    const nMaxEl = document.getElementById("nMax");
    const vMaxEl = document.getElementById("vMax");
    const nMinLabel = document.getElementById("nMinLabel");
    const nMaxLabel = document.getElementById("nMaxLabel");
    const vMaxLabel = document.getElementById("vMaxLabel");
    const meta = document.getElementById("meta");
    const hover = document.getElementById("hover");
    const top = document.getElementById("top");

    const allN = [...new Set(rows.map(r => r.n))].sort((a,b)=>a-b);
    const nSourceMin = allN[0];
    const nSourceMax = allN[allN.length - 1];

    const map = new Map();
    for (const r of rows) {{
      map.set(`${{r.n}}|${{r.v}}`, r);
    }}

    let hoverX = -1;
    let hoverY = -1;

    function metricValue(r, metric) {{
      if (metric === "inflow") return r.inflow;
      if (metric === "mass") return r.mass;
      if (metric === "pull") return r.pull;
      if (metric === "rank") return r.rank;
      return r.inflow;
    }}

    function colorFromT(t) {{
      const clamped = Math.max(0, Math.min(1, t));
      const h = 232 - 218 * clamped;
      const s = 90;
      const l = 10 + 62 * clamped;
      return `hsl(${{h}}, ${{s}}%, ${{l}}%)`;
    }}

    function resize() {{
      const dpr = window.devicePixelRatio || 1;
      const cw = Math.max(1, Math.floor(canvas.clientWidth));
      const ch = Math.max(1, Math.floor(canvas.clientHeight));
      const pw = Math.max(1, Math.floor(cw * dpr));
      const ph = Math.max(1, Math.floor(ch * dpr));
      if (canvas.width !== pw || canvas.height !== ph) {{
        canvas.width = pw;
        canvas.height = ph;
      }}
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return {{ w: cw, h: ch }};
    }}

    function draw() {{
      if (!canvas || !ctx) {{
        meta.textContent = "Canvas unavailable; showing SVG fallback.";
        if (fallbackEl) {{
          fallbackEl.style.display = "block";
        }}
        return;
      }}
      try {{
        let nLo = Number(nMinEl.value);
        let nHi = Number(nMaxEl.value);
        if (nLo > nHi) {{
          if (document.activeElement === nMinEl) {{
            nHi = nLo;
            nMaxEl.value = String(nHi);
          }} else {{
            nLo = nHi;
            nMinEl.value = String(nLo);
          }}
        }}
        const vAbs = Number(vMaxEl.value);
        const metric = metricEl.value;
        const scaleMode = scaleEl.value;

        nMinLabel.textContent = `${{nLo}}`;
        nMaxLabel.textContent = `${{nHi}}`;
        vMaxLabel.textContent = `${{vAbs}}`;

        const nCount = nHi - nLo + 1;
        const vCount = vAbs * 2 + 1;

        const dims = resize();
        const w = dims.w;
        const h = dims.h;
        const pad = 30;
        const gridW = Math.max(1, w - pad * 2);
        const gridH = Math.max(1, h - pad * 2);
        const cellW = gridW / Math.max(1, nCount);
        const cellH = gridH / Math.max(1, vCount);

        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = "#0b1220";
        ctx.fillRect(0, 0, w, h);

        const visible = [];
        for (let n = nLo; n <= nHi; n += 1) {{
          for (let v = -vAbs; v <= vAbs; v += 1) {{
            const row = map.get(`${{n}}|${{v}}`);
            if (!row) continue;
            visible.push(row);
          }}
        }}
        if (visible.length === 0) {{
          meta.textContent = "No visible cells; showing SVG fallback.";
          if (fallbackEl) {{
            fallbackEl.style.display = "block";
          }}
          canvas.style.opacity = "0";
          return;
        }}

        let minVal = Number.POSITIVE_INFINITY;
        let maxVal = Number.NEGATIVE_INFINITY;
        for (const r of visible) {{
          const v = metricValue(r, metric);
          if (v < minVal) minVal = v;
          if (v > maxVal) maxVal = v;
        }}
        if (!isFinite(minVal) || !isFinite(maxVal)) {{
          minVal = 0;
          maxVal = 1;
        }}
        const span = Math.max(1e-9, maxVal - minVal);
        const logSpan = Math.max(1e-9, Math.log1p(maxVal) - Math.log1p(minVal));

        for (const r of visible) {{
          const xIdx = r.n - nLo;
          const yIdx = vAbs - r.v;
          const x = pad + xIdx * cellW;
          const y = pad + yIdx * cellH;
          const raw = metricValue(r, metric);
          let t = (raw - minVal) / span;
          if (scaleMode === "log" && metric !== "pull" && metric !== "rank") {{
            t = (Math.log1p(raw) - Math.log1p(minVal)) / logSpan;
          }}
          if (metric === "rank") t = 1.0 - t;
          ctx.fillStyle = colorFromT(t);
          ctx.fillRect(x, y, Math.ceil(cellW), Math.ceil(cellH));
        }}

        ctx.strokeStyle = "rgba(130,160,220,0.35)";
        ctx.lineWidth = 1;
        ctx.strokeRect(pad, pad, gridW, gridH);

        // Reference axis for v=0 to make center attractor visible.
        if (vAbs > 0) {{
          const yCenterIdx = vAbs - 0;
          const yCenter = pad + yCenterIdx * cellH;
          ctx.strokeStyle = "rgba(220,240,255,0.55)";
          ctx.beginPath();
          ctx.moveTo(pad, yCenter);
          ctx.lineTo(pad + gridW, yCenter);
          ctx.stroke();
        }}

        meta.textContent = `Cells: ${{visible.length}} | N=[${{nLo}}, ${{nHi}}] | |v|<=${{vAbs}} | metric=${{metric}} | scale=${{scaleMode}} | min=${{minVal.toFixed(4)}} max=${{maxVal.toFixed(4)}}`;

        const atN = [];
        for (let v = -vAbs; v <= vAbs; v += 1) {{
          const r = map.get(`${{nHi}}|${{v}}`);
          if (r) atN.push(r);
        }}
        atN.sort((a,b) => a.rank - b.rank || Math.abs(a.v) - Math.abs(b.v) || a.v - b.v);
        const lines = ["Top attractors @ N max:"];
        for (const r of atN.slice(0, 8)) {{
          lines.push(`v=${{r.v}} rank=${{r.rank}} inflow=${{r.inflow}} mass=${{r.mass}} pull=${{r.pull.toFixed(4)}}`);
        }}
        top.textContent = lines.join("\\n");

        if (hoverX >= pad && hoverX <= pad + gridW && hoverY >= pad && hoverY <= pad + gridH) {{
          const xIdx = Math.floor((hoverX - pad) / cellW);
          const yIdx = Math.floor((hoverY - pad) / cellH);
          const n = nLo + xIdx;
          const v = vAbs - yIdx;
          const r = map.get(`${{n}}|${{v}}`);
          if (r) {{
            hover.textContent = `hover n=${{n}} v=${{v}} inflow=${{r.inflow}} mass=${{r.mass}} pull=${{r.pull.toFixed(6)}} rank=${{r.rank}} o2=${{r.o2}} o3=${{r.o3}}`;
          }} else {{
            hover.textContent = `hover n=${{n}} v=${{v}} (no data)`;
          }}
        }} else {{
          hover.textContent = "";
        }}
        if (fallbackEl) {{
          fallbackEl.style.display = "none";
        }}
        canvas.style.opacity = "1";
      }} catch (err) {{
        const msg = (err && err.message) ? err.message : String(err);
        meta.textContent = `Canvas draw failed; showing SVG fallback. ${{msg}}`;
        if (fallbackEl) {{
          fallbackEl.style.display = "block";
        }}
        canvas.style.opacity = "0";
      }}
    }}

    canvas.addEventListener("mousemove", (ev) => {{
      const rect = canvas.getBoundingClientRect();
      hoverX = ev.clientX - rect.left;
      hoverY = ev.clientY - rect.top;
      draw();
    }});

    for (const el of [metricEl, scaleEl, nMinEl, nMaxEl, vMaxEl]) {{
      el.addEventListener("input", draw);
      el.addEventListener("change", draw);
    }}

    window.addEventListener("resize", () => {{
      draw();
    }});

    draw();
  </script>
</body>
</html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MoO attractor maps over N.")
    parser.add_argument("--n-min", type=int, default=1)
    parser.add_argument("--n-max", type=int, default=20)
    parser.add_argument("--csv", type=Path, default=Path("out/attractor_n1_20.csv"))
    parser.add_argument("--json", type=Path, default=Path("out/attractor_n1_20.json"))
    parser.add_argument("--svg", type=Path, default=Path("out/attractor_n1_20.svg"))
    parser.add_argument("--html", type=Path, default=Path("out/attractor_n1_20.html"))
    args = parser.parse_args()
    if args.n_min < 1:
        parser.error("--n-min must be >= 1")
    if args.n_max < args.n_min:
        parser.error("--n-max must be >= --n-min")
    return args


def main() -> None:
    args = parse_args()
    rows = collect_rows(args.n_min, args.n_max)
    summary = build_summary(rows, args.n_min, args.n_max)
    default_v_abs = min(args.n_max, 80)
    write_csv(rows, args.csv)
    write_json(rows, summary, args.json)
    write_svg(
        rows,
        args.svg,
        n_min=args.n_min,
        n_max=args.n_max,
        metric="inflow",
        scale_mode="log",
        v_abs=default_v_abs,
    )
    if args.svg.parent.resolve() == args.html.parent.resolve():
        fallback_svg_src = args.svg.name
    else:
        fallback_svg_src = args.svg.as_posix()
    write_html(
        rows,
        args.html,
        n_min=args.n_min,
        n_max=args.n_max,
        fallback_svg_src=fallback_svg_src,
    )
    print(f"Wrote CSV : {args.csv}")
    print(f"Wrote JSON: {args.json}")
    print(f"Wrote SVG : {args.svg}")
    print(f"Wrote HTML: {args.html}")


if __name__ == "__main__":
    main()
