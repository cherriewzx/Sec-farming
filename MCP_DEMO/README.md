## MCP_DEMO - 目录敏感路径扫描与可视化报告

一个最小可用的 Web 目录/敏感路径扫描工具集，支持：
- 使用 `dir_serch.py` 同步扫描目标路径
- 导出结构化 JSON / CSV 结果
- 通过 `generate_html_report.py` 生成美观的可视化 HTML 报告
- 提供基于 FastAPI 的 MCP 服务封装（`mcp_dirscan.py` + `mcp.json`）

### 目录结构
- `dir_serch.py`：扫描逻辑（请求、过滤、导出）
- `generate_html_report.py`：将 JSON 结果渲染为 HTML 报告
- `mcp_dirscan.py`：将扫描能力封装成 MCP HTTP 服务（FastAPI）
- `mcp.json`：MCP 服务描述（入口、参数 schema）
- `scan_results.json`：样例扫描结果
- `scan_report.html`：样例可视化报告

### 1) 命令行扫描
运行扫描并导出 JSON：
```bash
python3 dir_serch.py -t http://127.0.0.1:8888 -o scan_results.json
```
可选参数（摘录）：
- `-w/--wordlist` 字典路径
- `--csv` 额外导出 CSV 文件
- `--timeout` 请求超时（秒）
- `--no-redirect` 不跟随重定向
- `--save-all` 保存所有请求记录（包括 404）
- `--user-agent` 自定义 UA

### 2) 生成可视化报告
```bash
python3 generate_html_report.py scan_results.json scan_report.html
```
打开 `scan_report.html` 查看：包含状态码彩色徽章、关键词“芯片”标识、命中行高亮、粘性表头等。

### 3) 以 MCP 服务方式使用
启动服务（仅本机访问）：
```bash
python3 mcp_dirscan.py
```
默认监听：`127.0.0.1:9999`

服务接口：
- `POST /tool/dir_scan`
  - body 示例：
    ```json
    {
      "target": "http://127.0.0.1:8888",
      "timeout": 8,
      "follow_redirects": true,
      "save_all": false,
      "user_agent": "DirScanMCP/1.0"
    }
    ```
- `GET /health` 健康检查

`mcp.json` 用于 MCP 宿主/客户端识别服务入口与参数；已配置为 `http://localhost:9999/tool/dir_scan`。

### 安全与授权
- 仅在授权范围内使用扫描工具；避免对未授权目标发起请求。
- MCP 服务默认仅绑定 `127.0.0.1`，更安全；如需局域网访问，可改为 `0.0.0.0` 并结合防火墙/反代/IP 白名单。

### 环境要求
- Python 3.9+
- 依赖：`requests`、`fastapi`、`uvicorn`（仅服务模式）

### 许可证
本示例仅供学习与演示。请在合规前提下使用。 

