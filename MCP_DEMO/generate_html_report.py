#!/usr/bin/env python3
"""
generate_html_report.py

Utility helper to render the JSON output produced by `dir_serch.py`
into a simple HTML report with summarised findings.
"""

import json
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from typing import List, Dict, Any


def load_results(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Results JSON must be a list")
    return data


def build_html(results: List[Dict[str, Any]], source_path: Path) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(results)
    successes = sum(1 for r in results if r.get("ok"))
    with_keywords = sum(1 for r in results if r.get("keyword_hits"))

    def fmt_keywords(rec: Dict[str, Any]) -> str:
        hits = rec.get("keyword_hits") or []
        if not hits:
            return "&mdash;"
        return "".join(f"<span class='chip chip-keyword'>{escape(str(kw))}</span>" for kw in hits)

    def status_badge(status: Any) -> str:
        if status is None:
            return "<span class='badge badge-na'>N/A</span>"
        try:
            s = int(status)
        except Exception:
            return f"<span class='badge badge-na'>{escape(str(status))}</span>"
        if 200 <= s < 300:
            cls = "badge-2xx"
        elif 300 <= s < 400:
            cls = "badge-3xx"
        elif 400 <= s < 500:
            cls = "badge-4xx"
        else:
            cls = "badge-5xx"
        return f"<span class='badge {cls}'>{s}</span>"

    rows = []
    for rec in results:
        row_class = "hit-row" if (rec.get('keyword_hits') or []) else ""
        rows.append(
            f"<tr class='{row_class}'>"
            f"<td>{escape(rec.get('target', ''))}</td>"
            f"<td>{escape(rec.get('path', ''))}</td>"
            f"<td>{escape(rec.get('url', ''))}</td>"
            f"<td>{status_badge(rec.get('status'))}</td>"
            f"<td class='num'>{rec.get('length', '')}</td>"
            f"<td>{fmt_keywords(rec)}</td>"
            f"<td>{escape(rec.get('error', '') or '')}</td>"
            f"<td><pre>{escape((rec.get('snippet') or '').strip())}</pre></td>"
            "</tr>"
        )

    table_rows = "\n".join(rows) if rows else (
        "<tr><td colspan='8' style='text-align:center;'>No results</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Dir Search Report</title>
  <style>
    :root {{
      --bg: #0b0c0f;
      --panel: #12151b;
      --panel-2: #171a21;
      --border: #202531;
      --text: #e6e8ee;
      --muted: #9aa3b2;
      --chip-bg: #1c2330;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 24px;
    }}
    h1 {{
      margin-top: 0;
      letter-spacing: 0.3px;
    }}
    .summary {{
      margin-bottom: 20px;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }}
    .summary div {{
      background: var(--panel);
      border-radius: 8px;
      padding: 12px 18px;
      border: 1px solid var(--border);
    }}
    .toolbar {{
      background: linear-gradient(180deg, var(--panel-2), var(--panel));
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
      margin: 14px 0 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .toolbar .meta {{ color: var(--muted); font-size: 14px; }}
    .toolbar .title {{ font-weight: 600; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{
      background: var(--panel-2);
      text-align: left;
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    tr.hit-row td {{
      background: linear-gradient(180deg, rgba(27, 46, 30, 0.35), rgba(21, 32, 24, 0.35));
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      border: 1px solid var(--border);
      background: var(--chip-bg);
      color: var(--text);
    }}
    .badge-2xx {{ background: rgba(24, 178, 107, 0.15); border-color: rgba(24, 178, 107, 0.35); color: #5cf2b3; }}
    .badge-3xx {{ background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.35); color: #93c5fd; }}
    .badge-4xx {{ background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.35); color: #fbbf24; }}
    .badge-5xx {{ background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.35); color: #fca5a5; }}
    .badge-na  {{ background: rgba(107, 114, 128, 0.15); border-color: rgba(107, 114, 128, 0.35); color: #cbd5e1; }}
    .chip {{
      display: inline-block;
      padding: 2px 8px;
      margin: 2px 4px 2px 0;
      font-size: 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--chip-bg);
      color: var(--text);
    }}
    .chip-keyword {{
      border-color: rgba(91, 156, 255, 0.35);
      background: rgba(91, 156, 255, 0.12);
      color: #b5d2ff;
    }}
    td.num {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: #cbd5e1; }}
  </style>
</head>
<body>
  <h1>Dir Search Report</h1>
  <div class="toolbar">
    <div class="title">可视化扫描结果</div>
    <div class="meta">
      源数据: <span class="muted">{escape(str(source_path))}</span> ・ 生成时间: <span class="muted">{escape(generated_at)}</span>
    </div>
  </div>
  <div class="summary">
    <div><strong>Total records:</strong> {total}</div>
    <div><strong>Successful responses (&lt;400):</strong> {successes}</div>
    <div><strong>Keyword hits:</strong> {with_keywords}</div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Target</th>
        <th>Path</th>
        <th>URL</th>
        <th>Status</th>
        <th>Length</th>
        <th>Keyword hits</th>
        <th>Error</th>
        <th>Snippet</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</body>
</html>
"""


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: generate_html_report.py <results.json> [output.html]")
        sys.exit(1)
    src = Path(args[0]).expanduser()
    dst = Path(args[1]).expanduser() if len(args) > 1 else src.with_suffix(".html")

    results = load_results(src)
    html = build_html(results, src)
    dst.write_text(html, encoding="utf-8")
    print(f"[+] HTML report written to: {dst}")


if __name__ == "__main__":
    main()

