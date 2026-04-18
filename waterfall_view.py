from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from constructionist_math import Graph, Node, demo


@dataclass
class WaterfallPoint:
    n: int
    k: int
    x: float
    y: float
    z: float
    mass: int
    center_mass: int
    order2_mass: int
    order3_mass: int


def _normalized_y(n: int, n_min: int, n_max: int) -> float:
    if n_max <= n_min:
        return 0.0
    return (n - n_min) / (n_max - n_min)


def _class_mass(graph: Graph, k: int) -> Tuple[int, int, int]:
    key = (int(k), 1)
    node_uids = graph.value_classes.get(key, set())
    if not node_uids:
        return 0, 0, 0
    node_uid = next(iter(node_uids))
    node = graph.nodes_by_uid.get(node_uid)
    if node is None:
        return 0, 0, 0

    # Value-centric semantics: one node per value, many edges per value.
    # Treat "mass" as the number of distinct derivation signatures flowing into the value.
    sigs: set[tuple[str, tuple[int, ...]]] = set()
    order2 = 0
    order3 = 0
    for edge in graph.edges:
        if edge.output is not node:
            continue
        sig = (str(edge.op), tuple(int(inp.node_uid) for inp in edge.inputs))
        if sig in sigs:
            continue
        sigs.add(sig)
        if all(inp.status == "G" for inp in edge.inputs):
            order2 += 1
        else:
            order3 += 1
    return len(sigs), order2, order3


def collect_points(n_min: int, n_max: int) -> List[WaterfallPoint]:
    points: List[WaterfallPoint] = []
    for n in range(n_min, n_max + 1):
        graph = demo(limit=n)
        center_mass, _, _ = _class_mass(graph, 0)
        if center_mass <= 0:
            center_mass = 1
        y = _normalized_y(n, n_min, n_max)
        for k in range(-n, n + 1):
            mass, order2, order3 = _class_mass(graph, k)
            z = mass / center_mass
            points.append(
                WaterfallPoint(
                    n=n,
                    k=k,
                    x=(k / n) if n > 0 else 0.0,
                    y=y,
                    z=z,
                    mass=mass,
                    center_mass=center_mass,
                    order2_mass=order2,
                    order3_mass=order3,
                )
            )
    return points


def write_csv(points: List[WaterfallPoint], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "n",
                "k",
                "x_k_over_n",
                "y_n_normalized",
                "z_mass_over_center",
                "mass",
                "center_mass",
                "order2_mass",
                "order3_mass",
            ]
        )
        for p in points:
            writer.writerow(
                [
                    p.n,
                    p.k,
                    f"{p.x:.8f}",
                    f"{p.y:.8f}",
                    f"{p.z:.8f}",
                    p.mass,
                    p.center_mass,
                    p.order2_mass,
                    p.order3_mass,
                ]
            )


def _rotate_xyz(x: float, y: float, z: float, yaw: float, pitch: float, roll: float) -> Tuple[float, float, float]:
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cr = math.cos(roll)
    sr = math.sin(roll)

    # Yaw around Z
    x1 = cy * x - sy * y
    y1 = sy * x + cy * y
    z1 = z

    # Pitch around X
    x2 = x1
    y2 = cp * y1 - sp * z1
    z2 = sp * y1 + cp * z1

    # Roll around Y
    x3 = cr * x2 + sr * z2
    y3 = y2
    z3 = -sr * x2 + cr * z2
    return x3, y3, z3


def _project_points(
    points: List[WaterfallPoint],
    *,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
) -> List[Dict[str, float]]:
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)
    projected: List[Dict[str, float]] = []
    for p in points:
        x = p.x
        y = (p.y * 2.0) - 1.0
        z = p.z
        rx, ry, rz = _rotate_xyz(x, y, z, yaw, pitch, roll)
        depth = 2.6 + ry
        if depth < 0.4:
            depth = 0.4
        u = rx / depth
        v = rz / depth
        projected.append(
            {
                "n": float(p.n),
                "k": float(p.k),
                "u": u,
                "v": v,
                "mass": float(p.mass),
                "order2_mass": float(p.order2_mass),
                "order3_mass": float(p.order3_mass),
            }
        )
    return projected


def write_svg(
    points: List[WaterfallPoint],
    out_svg: Path,
    *,
    n_min: int,
    n_max: int,
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
) -> None:
    projected = _project_points(points, yaw_deg=yaw_deg, pitch_deg=pitch_deg, roll_deg=roll_deg)
    if not projected:
        out_svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>\n", encoding="utf-8")
        return

    min_u = min(p["u"] for p in projected)
    max_u = max(p["u"] for p in projected)
    min_v = min(p["v"] for p in projected)
    max_v = max(p["v"] for p in projected)

    width = 1400
    height = 900
    pad_x = 80
    pad_y = 70
    span_u = (max_u - min_u) or 1.0
    span_v = (max_v - min_v) or 1.0
    sx = (width - 2 * pad_x) / span_u
    sy = (height - 2 * pad_y) / span_v
    scale = min(sx, sy)

    def map_xy(u: float, v: float) -> Tuple[float, float]:
        px = pad_x + (u - min_u) * scale
        py = height - (pad_y + (v - min_v) * scale)
        return px, py

    by_n: Dict[int, List[Dict[str, float]]] = {}
    for row in projected:
        n = int(row["n"])
        by_n.setdefault(n, []).append(row)
    for n in by_n:
        by_n[n].sort(key=lambda row: row["k"])

    lines: List[str] = []
    lines.append(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}'>")
    lines.append("<rect width='100%' height='100%' fill='#0b1220'/>")
    lines.append(
        "<text x='32' y='42' fill='#d7e3ff' font-family='monospace' font-size='24'>"
        "MoO Normalized Waterfall (x=k/N, y=N, z=mass/m(0))"
        "</text>"
    )
    lines.append(
        f"<text x='32' y='72' fill='#8ca1d6' font-family='monospace' font-size='16'>"
        f"N={n_min}..{n_max} | yaw={yaw_deg:.1f} pitch={pitch_deg:.1f} roll={roll_deg:.1f}"
        "</text>"
    )

    rng = max(1, n_max - n_min)
    for n in sorted(by_n.keys()):
        t = (n - n_min) / rng
        r = int(80 + 140 * t)
        g = int(120 + 90 * (1.0 - t))
        b = int(220 - 120 * t)
        color = f"rgb({r},{g},{b})"
        pts = [map_xy(row["u"], row["v"]) for row in by_n[n]]
        poly = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        lines.append(
            f"<polyline points='{poly}' fill='none' stroke='{color}' stroke-width='1.8' opacity='0.72'/>"
        )
        for row in by_n[n]:
            x, y = map_xy(row["u"], row["v"])
            radius = 1.8 + min(2.0, row["mass"] / 50.0)
            lines.append(
                f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{radius:.2f}' fill='{color}' opacity='0.78'/>"
            )

    lines.append(
        "<text x='32' y='840' fill='#8ca1d6' font-family='monospace' font-size='14'>"
        "Each colored polyline is one N-slice; all slices are in one normalized frame and rotated together."
        "</text>"
    )
    lines.append("</svg>")

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(points: List[WaterfallPoint], out_html: Path, *, n_min: int, n_max: int) -> None:
    rows = [
        {
            "n": p.n,
            "k": p.k,
            "x": p.x,
            "y": (p.y * 2.0) - 1.0,
            "z": p.z,
            "mass": p.mass,
            "order2_mass": p.order2_mass,
            "order3_mass": p.order3_mass,
        }
        for p in points
    ]
    payload = json.dumps(rows, separators=(",", ":"))

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MoO Waterfall View</title>
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
      background: radial-gradient(circle at 20% 20%, #15233f, var(--bg) 55%);
      color: var(--fg);
      font-family: "IBM Plex Sans", "Fira Sans", sans-serif;
    }}
    .wrap {{
      display: grid;
      grid-template-columns: 340px 1fr;
      min-height: 100vh;
    }}
    .panel {{
      background: color-mix(in oklab, var(--panel) 92%, black);
      border-right: 1px solid var(--line);
      padding: 22px;
      box-sizing: border-box;
    }}
    h1 {{
      margin: 0 0 12px;
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 20px;
    }}
    p {{
      margin: 8px 0 14px;
      line-height: 1.35;
      color: var(--muted);
      font-size: 13px;
    }}
    .row {{
      margin: 12px 0;
    }}
    label {{
      display: block;
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 12px;
      margin-bottom: 6px;
    }}
    input[type=range] {{
      width: 100%;
    }}
    .mono {{
      font-family: "IBM Plex Mono", "Fira Mono", monospace;
      font-size: 12px;
      color: var(--muted);
    }}
    canvas {{
      width: 100%;
      height: 100vh;
      display: block;
      background: transparent;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <h1>MoO Normalized Waterfall</h1>
      <p>N={n_min}..{n_max}. Coordinates: x = k/N, y = normalized N, z = class_mass / mass(0).</p>
      <div class="row">
        <label>N Min <span id="nMinLabel"></span></label>
        <input id="nMin" type="range" min="{n_min}" max="{n_max}" step="1" value="{n_min}" />
      </div>
      <div class="row">
        <label>N Max <span id="nMaxLabel"></span></label>
        <input id="nMax" type="range" min="{n_min}" max="{n_max}" step="1" value="{n_max}" />
      </div>
      <div class="row">
        <label>Yaw <span id="yawLabel"></span></label>
        <input id="yaw" type="range" min="-180" max="180" step="1" value="32" />
      </div>
      <div class="row">
        <label>Pitch <span id="pitchLabel"></span></label>
        <input id="pitch" type="range" min="-89" max="89" step="1" value="28" />
      </div>
      <div class="row">
        <label>Roll <span id="rollLabel"></span></label>
        <input id="roll" type="range" min="-180" max="180" step="1" value="-8" />
      </div>
      <div class="row">
        <label><input id="spin" type="checkbox" checked /> Auto-rotate (unison)</label>
      </div>
      <div class="mono" id="meta"></div>
    </section>
    <canvas id="view"></canvas>
  </div>
  <script>
    const points = {payload};
    const canvas = document.getElementById("view");
    const ctx = canvas.getContext("2d");
    const nMinEl = document.getElementById("nMin");
    const nMaxEl = document.getElementById("nMax");
    const nMinLabel = document.getElementById("nMinLabel");
    const nMaxLabel = document.getElementById("nMaxLabel");
    const yawEl = document.getElementById("yaw");
    const pitchEl = document.getElementById("pitch");
    const rollEl = document.getElementById("roll");
    const spinEl = document.getElementById("spin");
    const yawLabel = document.getElementById("yawLabel");
    const pitchLabel = document.getElementById("pitchLabel");
    const rollLabel = document.getElementById("rollLabel");
    const meta = document.getElementById("meta");

    const sourceNMin = Math.min(...points.map(p => p.n));
    const sourceNMax = Math.max(...points.map(p => p.n));
    const byN = new Map();
    for (const p of points) {{
      if (!byN.has(p.n)) byN.set(p.n, []);
      byN.get(p.n).push(p);
    }}
    for (const arr of byN.values()) {{
      arr.sort((a,b) => a.k - b.k);
    }}
    const sortedNs = [...byN.keys()].sort((a,b) => a - b);

    function colorForN(n) {{
      const t = (n - sourceNMin) / Math.max(1, (sourceNMax - sourceNMin));
      const r = Math.floor(80 + 140 * t);
      const g = Math.floor(120 + 90 * (1 - t));
      const b = Math.floor(220 - 120 * t);
      return `rgb(${{r}},${{g}},${{b}})`;
    }}

    function rotate(x, y, z, yaw, pitch, roll) {{
      const cy = Math.cos(yaw), sy = Math.sin(yaw);
      const cp = Math.cos(pitch), sp = Math.sin(pitch);
      const cr = Math.cos(roll), sr = Math.sin(roll);
      const x1 = cy * x - sy * y;
      const y1 = sy * x + cy * y;
      const z1 = z;
      const x2 = x1;
      const y2 = cp * y1 - sp * z1;
      const z2 = sp * y1 + cp * z1;
      const x3 = cr * x2 + sr * z2;
      const y3 = y2;
      const z3 = -sr * x2 + cr * z2;
      return [x3, y3, z3];
    }}

    function project(x, y, z, yaw, pitch, roll) {{
      const [rx, ry, rz] = rotate(x, y, z, yaw, pitch, roll);
      let depth = 2.6 + ry;
      if (depth < 0.4) depth = 0.4;
      return [rx / depth, rz / depth, ry];
    }}

    function resize() {{
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(canvas.clientWidth * dpr);
      canvas.height = Math.floor(canvas.clientHeight * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }}

    function draw(ts) {{
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

      if (spinEl.checked) {{
        const current = Number(yawEl.value);
        yawEl.value = String(current + 0.06);
      }}
      const yaw = Number(yawEl.value) * Math.PI / 180;
      const pitch = Number(pitchEl.value) * Math.PI / 180;
      const roll = Number(rollEl.value) * Math.PI / 180;
      nMinLabel.textContent = `${{nLo}}`;
      nMaxLabel.textContent = `${{nHi}}`;
      yawLabel.textContent = `${{Number(yawEl.value).toFixed(1)}}°`;
      pitchLabel.textContent = `${{Number(pitchEl.value).toFixed(1)}}°`;
      rollLabel.textContent = `${{Number(rollEl.value).toFixed(1)}}°`;

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "#0b1220";
      ctx.fillRect(0, 0, w, h);

      const visibleNs = sortedNs.filter(n => n >= nLo && n <= nHi);
      const projected = [];
      const projectedByN = new Map();
      let activePointCount = 0;

      for (const n of visibleNs) {{
        const slice = byN.get(n) || [];
        const out = [];
        for (const p of slice) {{
          const [u, v, depth] = project(p.x, p.y, p.z, yaw, pitch, roll);
          const row = {{...p, u, v, depth}};
          projected.push(row);
          out.push(row);
        }}
        projectedByN.set(n, out);
        activePointCount += slice.length;
      }}

      if (projected.length === 0) {{
        meta.textContent = `Points: 0 / ${{points.length}} | Slices: 0 / ${{sortedNs.length}} | Visible N: [${{nLo}}, ${{nHi}}]`;
        requestAnimationFrame(draw);
        return;
      }}

      const minU = Math.min(...projected.map(p => p.u));
      const maxU = Math.max(...projected.map(p => p.u));
      const minV = Math.min(...projected.map(p => p.v));
      const maxV = Math.max(...projected.map(p => p.v));
      const spanU = (maxU - minU) || 1;
      const spanV = (maxV - minV) || 1;
      const padX = 60, padY = 60;
      const sx = (w - padX * 2) / spanU;
      const sy = (h - padY * 2) / spanV;
      const scale = Math.min(sx, sy);
      const toPx = (u, v) => [padX + (u - minU) * scale, h - (padY + (v - minV) * scale)];

      // Draw per-slice polylines.
      for (const n of visibleNs) {{
        const arr = projectedByN.get(n) || [];
        const color = colorForN(n);
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.72;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        arr.forEach((p, idx) => {{
          if (!p) return;
          const [x, y] = toPx(p.u, p.v);
          if (idx === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }});
        ctx.stroke();
      }}

      const sorted = projected.slice().sort((a,b) => a.depth - b.depth);
      for (const p of sorted) {{
        const color = colorForN(p.n);
        const [x, y] = toPx(p.u, p.v);
        const r = 1.6 + Math.min(2.2, p.mass / 55);
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.82;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      }}
      ctx.globalAlpha = 1.0;

      meta.textContent = `Points: ${{activePointCount}} / ${{points.length}} | Slices: ${{visibleNs.length}} / ${{sortedNs.length}} | Visible N: [${{nLo}}, ${{nHi}}]`;
      requestAnimationFrame(draw);
    }}

    window.addEventListener("resize", resize);
    resize();
    requestAnimationFrame(draw);
  </script>
</body>
</html>
"""

    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render normalized MoO waterfall views.")
    parser.add_argument("--n-min", type=int, default=1)
    parser.add_argument("--n-max", type=int, default=20)
    parser.add_argument("--yaw", type=float, default=32.0)
    parser.add_argument("--pitch", type=float, default=28.0)
    parser.add_argument("--roll", type=float, default=-8.0)
    parser.add_argument("--csv", type=Path, default=Path("out/waterfall_n1_20.csv"))
    parser.add_argument("--svg", type=Path, default=Path("out/waterfall_n1_20.svg"))
    parser.add_argument("--html", type=Path, default=Path("out/waterfall_n1_20.html"))
    args = parser.parse_args()
    if args.n_min < 1:
        parser.error("--n-min must be >= 1")
    if args.n_max < args.n_min:
        parser.error("--n-max must be >= --n-min")
    return args


def main() -> None:
    args = parse_args()
    points = collect_points(args.n_min, args.n_max)
    write_csv(points, args.csv)
    write_svg(
        points,
        args.svg,
        n_min=args.n_min,
        n_max=args.n_max,
        yaw_deg=args.yaw,
        pitch_deg=args.pitch,
        roll_deg=args.roll,
    )
    write_html(points, args.html, n_min=args.n_min, n_max=args.n_max)
    print(f"Wrote CSV : {args.csv}")
    print(f"Wrote SVG : {args.svg}")
    print(f"Wrote HTML: {args.html}")


if __name__ == "__main__":
    main()
