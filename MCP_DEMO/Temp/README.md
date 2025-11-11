# 轻量 MCP（无需本地端口）说明（中文）

本目录提供一个不依赖本地 9999 端口的最小实现：一个纯本地目录扫描与报告生成工具。运行后会把结构化结果与 HTML 报告统一输出在 `Temp/` 下。

## 文件说明
- `dir_serch.py`：核心脚本，扫描指定目录并导出 `scan_results.json` 与 `scan_report.html`
- `scan_results.json`：扫描结果（结构化 JSON）
- `scan_report.html`：可读性良好的静态 HTML 报告

## 使用方法

```bash
# 在仓库根目录执行，扫描当前仓库
python3 Temp/dir_serch.py --root .

# 限制最大文件大小（单位：字节），例如 2MB：
python3 Temp/dir_serch.py --root . --max-size 2097152

# 需要跟随符号链接时：
python3 Temp/dir_serch.py --root . --follow-symlinks
```

执行完成后，输出文件（`scan_results.json` 与 `scan_report.html`）会位于当前目录下的 `Temp/` 中，无需启动任何本地服务或端口。

## 设计原则
- 轻量：单脚本完成扫描与报告，无额外服务
- 本地：不启动端口、无网络依赖
- 可读：JSON 方便自动处理，HTML 便于浏览


