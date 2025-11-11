#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
一个无需开启本地端口的轻量目录扫描与报告生成工具（MCP 变体）。
特性：
1. 纯本地运行：不启动 9999 等端口，无网络依赖
2. 结构化输出：扫描结果写入 Temp/scan_results.json
3. 可读报告：生成 Temp/scan_report.html
4. 轻量且不冗余：一个脚本完成扫描与报告

用法：
    python3 Temp/dir_serch.py --root <要扫描的目录> [--max-size 10485760] [--follow-symlinks]
示例：
    python3 Temp/dir_serch.py --root . --max-size 2097152
"""

import argparse
import dataclasses
import datetime
import html
import io
import json
import os
import stat
import sys
from typing import Dict, Iterator, List, Optional, Tuple

TEMP_DIR = os.path.dirname(os.path.abspath(__file__))
RESULT_JSON = os.path.join(TEMP_DIR, "scan_results.json")
RESULT_HTML = os.path.join(TEMP_DIR, "scan_report.html")


@dataclasses.dataclass
class FileEntry:
    path: str
    size: int
    mtime_iso: str
    mode: str
    is_symlink: bool
    extension: str


def human_readable_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024.0
    return f"{size:.2f}PB"


def format_mode(st_mode: int) -> str:
    # 近似 ls -l 权限字符串
    is_dir = "d" if stat.S_ISDIR(st_mode) else "-"
    perms = ""
    for who in (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH):
        perms += ("r" if who in (stat.S_IRUSR, stat.S_IRGRP, stat.S_IROTH) else
                  "w" if who in (stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH) else
                  "x" if who in (stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH) else "")
    # 上面简单拼接不区分位组，下面按位判断更准确
    r = "r" if (st_mode & stat.S_IRUSR) else "-"
    w = "w" if (st_mode & stat.S_IWUSR) else "-"
    x = "x" if (st_mode & stat.S_IXUSR) else "-"
    r2 = "r" if (st_mode & stat.S_IRGRP) else "-"
    w2 = "w" if (st_mode & stat.S_IWGRP) else "-"
    x2 = "x" if (st_mode & stat.S_IXGRP) else "-"
    r3 = "r" if (st_mode & stat.S_IROTH) else "-"
    w3 = "w" if (st_mode & stat.S_IWOTH) else "-"
    x3 = "x" if (st_mode & stat.S_IXOTH) else "-"
    return f"{is_dir}{r}{w}{x}{r2}{w2}{x2}{r3}{w3}{x3}"


def iter_files(root: str, follow_symlinks: bool) -> Iterator[Tuple[str, os.stat_result, bool]]:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            try:
                link = os.path.islink(full_path)
                st = os.stat(full_path, follow_symlinks=follow_symlinks)
            except (FileNotFoundError, PermissionError):
                continue
            yield full_path, st, link


def collect_entries(root: str, max_size: Optional[int], follow_symlinks: bool) -> List[FileEntry]:
    entries: List[FileEntry] = []
    for path, st, is_link in iter_files(root, follow_symlinks):
        if max_size is not None and st.st_size > max_size:
            continue
        mtime_iso = datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
        _, ext = os.path.splitext(path)
        entries.append(FileEntry(
            path=os.path.relpath(path, root),
            size=st.st_size,
            mtime_iso=mtime_iso,
            mode=format_mode(st.st_mode),
            is_symlink=is_link,
            extension=(ext.lower() or "")
        ))
    entries.sort(key=lambda e: (e.extension, e.path))
    return entries


def write_json(entries: List[FileEntry], json_path: str) -> None:
    data = [dataclasses.asdict(e) for e in entries]
    with io.open(json_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
                   "num_files": len(entries),
                   "results": data}, f, ensure_ascii=False, indent=2)


def render_html(entries: List[FileEntry]) -> str:
    # 极简 HTML，不依赖外部资源
    rows = []
    for e in entries:
        rows.append(
            "<tr>"
            f"<td>{html.escape(e.path)}</td>"
            f"<td>{html.escape(e.extension or '-')}</td>"
            f"<td style='text-align:right'>{e.size} ({html.escape(human_readable_size(e.size))})</td>"
            f"<td>{html.escape(e.mtime_iso)}</td>"
            f"<td>{html.escape(e.mode)}</td>"
            f"<td>{'✓' if e.is_symlink else ''}</td>"
            "</tr>"
        )
    table = "\n".join(rows)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>目录扫描报告</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; padding: 16px; }}
    .meta {{ color: #555; margin-bottom: 12px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px; font-size: 13px; }}
    th {{ background: #f9fafb; text-align: left; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    code {{ background: #f3f4f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h2>目录扫描报告</h2>
  <div class="meta">生成时间：{html.escape(datetime.datetime.now().isoformat(timespec="seconds"))} ・ 文件数：{len(entries)}</div>
  <table>
    <thead>
      <tr>
        <th>相对路径</th>
        <th>扩展名</th>
        <th>大小</th>
        <th>修改时间</th>
        <th>权限</th>
        <th>符号链接</th>
      </tr>
    </thead>
    <tbody>
      {table}
    </tbody>
  </table>
  <p class="meta">提示：本报告为纯静态页面，可直接打开 <code>Temp/scan_report.html</code> 查看。</p>
</body>
</html>"""


def write_html(entries: List[FileEntry], html_path: str) -> None:
    with io.open(html_path, "w", encoding="utf-8") as f:
        f.write(render_html(entries))


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轻量目录扫描与报告生成（无需端口）")
    parser.add_argument("--root", required=True, help="扫描起始目录")
    parser.add_argument("--max-size", type=int, default=None, help="仅包含不超过该字节数的文件")
    parser.add_argument("--follow-symlinks", action="store_true", help="是否跟随符号链接")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root = os.path.abspath(args.root)
    if not os.path.exists(root):
        print(f"[错误] 路径不存在：{root}", file=sys.stderr)
        return 2
    entries = collect_entries(root=root, max_size=args.max_size, follow_symlinks=args.follow_symlinks)
    # 输出到 Temp/
    os.makedirs(TEMP_DIR, exist_ok=True)
    write_json(entries, RESULT_JSON)
    write_html(entries, RESULT_HTML)
    print(f"[完成] JSON: {RESULT_JSON}")
    print(f"[完成] HTML: {RESULT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
轻量文件驱动 MCP（无本地端口）- 目录/路径探测器

说明：
- 不开启任何本地端口；通过文件输入/输出驱动
- 读取 Temp/targets.txt 与 Temp/wordlist.txt（若缺失则使用内置字典）
- 输出 Temp/scan_results.json 与可选 Temp/scan_results.csv
- 可与 Temp/generate_html_report.py 配合生成 HTML 报告
"""

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TARGETS_FILE = BASE_DIR / "targets.txt"
DEFAULT_WORDLIST_FILE = BASE_DIR / "wordlist.txt"
DEFAULT_JSON_OUT = BASE_DIR / "scan_results.json"

DEFAULT_WORDLIST = [
    "admin/", "login", "login/", "wp-admin/", "phpinfo.php",
    "config.php", ".env", "robots.txt", "sitemap.xml",
    "upload/", "uploads/", "dashboard/"
]

SENSITIVE_KEYWORDS = [
    "token", "password", "secret", "apikey", "api_key",
    "Index of", "Directory listing"
]


def normalize_target(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def load_lines_or_default(path: Path, fallback: List[str]) -> List[str]:
    if not path.exists():
        return fallback.copy()
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [l for l in lines if l]


def load_targets(path: Path) -> List[str]:
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [normalize_target(l) for l in lines if l]


def probe_url(full_url: str, timeout: int = 8, allow_redirects: bool = True, headers: Dict[str, str] = None) -> Dict[str, Any]:
    headers = headers or {"User-Agent": "DirScanLite/1.0"}
    try:
        resp = requests.get(full_url, timeout=timeout, allow_redirects=allow_redirects, headers=headers)
        text = resp.text or ""
        snippet = text[:1000]
        keyword_hits = [kw for kw in SENSITIVE_KEYWORDS if kw.lower() in snippet.lower()]
        return {
            "url": full_url,
            "status": resp.status_code,
            "length": len(text),
            "headers": {k: resp.headers.get(k) for k in ("Server", "Content-Type") if resp.headers.get(k)},
            "ok": resp.status_code < 400,
            "snippet": snippet,
            "keyword_hits": keyword_hits,
            "error": ""
        }
    except Exception as e:
        return {
            "url": full_url,
            "status": None,
            "length": 0,
            "headers": {},
            "ok": False,
            "snippet": "",
            "keyword_hits": [],
            "error": str(e)
        }


def scan_target(target: str, paths: List[str], timeout: int = 8, follow_redirects: bool = True, save_all: bool = False, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
    results = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        full = urljoin(target + "/", p)
        rec = probe_url(full, timeout=timeout, allow_redirects=follow_redirects, headers=headers)
        rec.update({"target": target, "path": p})
        if save_all or rec.get("ok") or rec.get("keyword_hits"):
            results.append(rec)
    return results


def save_json(path: Path, data: List[Dict[str, Any]]):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_csv(path: Path, data: List[Dict[str, Any]]):
    keys = ["target", "path", "url", "status", "length", "keyword_hits", "error"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in data:
            writer.writerow({k: r.get(k, "") for k in keys})


def parse_args():
    p = argparse.ArgumentParser(description="DirScanLite - 文件驱动的轻量扫描（无端口）")
    p.add_argument("-T", "--targets-file", default=str(DEFAULT_TARGETS_FILE), help="目标列表文件（默认 Temp/targets.txt）")
    p.add_argument("-w", "--wordlist", default=str(DEFAULT_WORDLIST_FILE), help="路径字典文件（默认 Temp/wordlist.txt）")
    p.add_argument("-o", "--out", default=str(DEFAULT_JSON_OUT), help="输出 JSON 文件（默认 Temp/scan_results.json）")
    p.add_argument("--csv", help="同时输出 CSV 文件（可选，位于 Temp 内）")
    p.add_argument("--timeout", type=int, default=8)
    p.add_argument("--no-redirect", action="store_true", help="不跟随重定向")
    p.add_argument("--save-all", action="store_true", help="保存所有请求（包括 404）")
    p.add_argument("--user-agent", default="DirScanLite/1.0")
    return p.parse_args()


def main():
    args = parse_args()

    targets = load_targets(Path(args.targets_file))
    if not targets:
        print("[!] 未提供有效 targets，检查 Temp/targets.txt")
        return
    paths = load_lines_or_default(Path(args.wordlist), DEFAULT_WORDLIST)
    headers = {"User-Agent": args.user_agent}

    all_results = []
    for t in targets:
        print(f"[+] Scanning: {t}")
        res = scan_target(
            t,
            paths,
            timeout=args.timeout,
            follow_redirects=not args.no_redirect,
            save_all=args.save_all,
            headers=headers,
        )
        print(f"    -> findings: {len(res)}")
        all_results.extend(res)

    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    save_json(outpath, all_results)
    if args.csv:
        save_csv(Path(args.csv), all_results)
    print(f"[+] Done. {len(all_results)} 记录已写入 {outpath}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
dir_scan_sync.py
最小可用的同步目录敏感路径扫描器（基于 requests 的同步实现）

主要功能：
- 支持单一目标（-t）或从文件批量导入目标（-T）
- 读取敏感路径字典（wordlist，每行一个 path）；未提供时使用内置默认列表
- 逐个请求目标 + 路径组合，记录：HTTP 状态码 / 响应长度 / 关键响应头 / 页首内容片段 / 关键词命中
- 支持选项：超时、是否跟随重定向、是否保存所有请求记录（包括 404）以及自定义 UA
- 扫描结果支持导出为 JSON（默认）与 CSV（可选）

使用范围提示：仅在拥有足够授权的前提下对目标进行测试。
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urljoin

import requests

# 内置默认字典。当未提供 --wordlist 时使用该列表。
# 注意：路径中既包含带斜杠结尾的目录形式，也包含文件形式（如 phpinfo.php）。
DEFAULT_WORDLIST = [
    "admin/", "login", "login/", "wp-admin/", "phpinfo.php", "config.php",
    ".env", "robots.txt", "sitemap.xml", "upload/", "uploads/", "dashboard/"
]

# 在响应片段中检索的敏感关键词集合（大小写不敏感对比）
SENSITIVE_KEYWORDS = ["token", "password", "secret", "apikey", "api_key", "Index of", "Directory listing"]


def normalize_target(url: str) -> str:
    """规范化目标地址：
    - 去除首尾空白
    - 若缺少协议，默认补全为 https://
    - 去除末尾斜杠，方便后续拼接
    """
    url = url.strip()
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def load_wordlist(path: Path) -> List[str]:
    """加载敏感路径字典。
    - 若路径不存在，回退到 DEFAULT_WORDLIST 的拷贝
    - 逐行读取并去除空白，剔除空行
    """
    if not path or not path.exists():
        return DEFAULT_WORDLIST.copy()
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [l for l in lines if l]


def load_targets(path: Path) -> List[str]:
    """加载批量目标文件。
    - 每行一个目标，支持裸域名或完整 URL
    - 对每个条目做 normalize_target 规范化
    """
    if not path or not path.exists():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [normalize_target(l) for l in lines if l]


def probe_url(full_url: str, timeout: int = 8, allow_redirects: bool = True, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """对单个 URL 发起 HTTP GET 探测并提取关键信息。

    返回字典包含字段：
    - url: 完整请求 URL
    - status: HTTP 状态码（异常时为 None）
    - length: 响应正文长度（字符数）
    - headers: 选取的响应头片段（仅挑选 Server / Content-Type）
    - ok: 状态码 < 400 视为成功
    - snippet: 响应正文前 1000 个字符（避免输出过大）
    - keyword_hits: 在 snippet 中命中的敏感关键词列表
    - error: 异常信息（仅在请求异常时填充）
    """
    headers = headers or {"User-Agent": "DirScanSync/1.0 (+https://example.com)"}
    try:
        resp = requests.get(full_url, timeout=timeout, allow_redirects=allow_redirects, headers=headers)
        text = resp.text or ""
        # snippet length limited to avoid huge outputs
        snippet = text[:1000]
        keyword_hits = [kw for kw in SENSITIVE_KEYWORDS if kw.lower() in snippet.lower()]
        return {
            "url": full_url,
            "status": resp.status_code,
            "length": len(text),
            "headers": {k: resp.headers.get(k) for k in ("Server", "Content-Type") if resp.headers.get(k)},
            "ok": resp.status_code < 400,
            "snippet": snippet,
            "keyword_hits": keyword_hits,
            "error": ""
        }
    except Exception as e:
        # 网络错误、SSL 错误、超时等异常路径在此兜底
        return {
            "url": full_url,
            "status": None,
            "length": 0,
            "headers": {},
            "ok": False,
            "snippet": "",
            "keyword_hits": [],
            "error": str(e)
        }


def scan_target(target: str, paths: List[str], timeout: int = 8, follow_redirects: bool = True, save_all: bool = False, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """针对单个目标枚举字典中的路径并逐条探测。

    - target: 规范化后的基础 URL（不含末尾斜杠）
    - paths: 字符串路径列表，可为"目录/"或"文件"形式
    - save_all: False 时仅保留成功（<400）或命中关键词的记录；True 时全部保留
    返回：每条路径对应的探测结果列表
    """
    results = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        # ensure proper join (avoid double slashes)
        full = urljoin(target + "/", p)
        rec = probe_url(full, timeout=timeout, allow_redirects=follow_redirects, headers=headers)
        rec.update({"target": target, "path": p})
        # if save_all is False, only save findings with status < 400 or keyword hits
        if save_all or rec.get("ok") or rec.get("keyword_hits"):
            results.append(rec)
    return results


def save_json(path: Path, data: List[Dict[str, Any]]):
    """将结果写入 JSON 文件，使用 UTF-8 编码并保留中文。"""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_csv(path: Path, data: List[Dict[str, Any]]):
    """将结果写入 CSV 文件，只挑选关键字段，便于快速筛选与统计。"""
    keys = ["target", "path", "url", "status", "length", "keyword_hits", "error"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in data:
            writer.writerow({k: r.get(k, "") for k in keys})


def parse_args():
    """命令行参数解析：
    -t/--target: 单个目标（域名或完整 URL）
    -T/--targets-file: 目标列表文件（每行一个目标）
    -w/--wordlist: 路径字典文件
    -o/--out: JSON 输出文件路径（默认 results.json）
    --csv: 额外输出 CSV 文件路径（可选）
    --timeout: 请求超时时间（秒，默认 8）
    --no-redirect: 不跟随重定向（默认跟随）
    --save-all: 保存所有请求结果（包括 404）
    --user-agent: 自定义 User-Agent
    """
    p = argparse.ArgumentParser(description="Dir Scan Sync - scan target for sensitive paths/files")
    p.add_argument("-t", "--target", help="single target (e.g. example.com or https://example.com)")
    p.add_argument("-T", "--targets-file", help="file with one target per line")
    p.add_argument("-w", "--wordlist", help="wordlist file, one path per line")
    p.add_argument("-o", "--out", default="results.json", help="output json file")
    p.add_argument("--csv", help="also save csv file (path)")
    p.add_argument("--timeout", type=int, default=8)
    p.add_argument("--no-redirect", action="store_true", help="do not follow redirects")
    p.add_argument("--save-all", action="store_true", help="save all requests (including 404)")
    p.add_argument("--user-agent", default="DirScanSync/1.0")
    return p.parse_args()


def main():
    """主流程：
    1) 解析参数，收集目标集合（单个或文件批量）
    2) 准备路径字典（文件或默认）与请求头（UA）
    3) 逐目标执行扫描，按需过滤结果
    4) 输出 JSON，若提供 --csv 则同时输出 CSV
    """
    args = parse_args()

    targets = []
    if args.target:
        targets.append(normalize_target(args.target))
    if args.targets_file:
        targets.extend(load_targets(Path(args.targets_file)))
    if not targets:
        print("No targets provided. Use -t or -T.")
        sys.exit(1)
    paths = load_wordlist(Path(args.wordlist)) if args.wordlist else DEFAULT_WORDLIST.copy()


    headers = {"User-Agent": args.user_agent}
    all_results = []
    for t in targets:
        print(f"[+] Scanning target: {t} ...")
        res = scan_target(t, paths, timeout=args.timeout, follow_redirects=not args.no_redirect, save_all=args.save_all, headers=headers)
        print(f"    -> findings: {len(res)}")
        all_results.extend(res)

    outpath = Path(args.out)
    save_json(outpath, all_results)
    if args.csv:
        save_csv(Path(args.csv), all_results)
    print(f"[+] Scan finished. {len(all_results)} records saved to {outpath}")


if __name__ == "__main__":
    main()
