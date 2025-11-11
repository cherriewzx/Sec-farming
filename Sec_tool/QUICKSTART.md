# MCP Directory Scanner 快速开始

## 快速安装

```bash
# 1. 安装依赖
cd Sec_tool
pip install -r requirements.txt

# 2. 测试服务器（可选）
python3 test_mcp.py
```

## 在 Cursor 中配置

1. 打开 Cursor 设置
2. 找到 MCP 配置（通常在 `~/.cursor/mcp.json` 或设置界面）
3. 添加以下配置：

```json
{
  "mcpServers": {
    "directory-scanner": {
      "command": "python3",
      "args": [
        "/Users/a58/Desktop/Script_tools/Sec-farming/Sec_tool/mcp_server.py"
      ]
    }
  }
}
```

**注意**：请将路径替换为你的实际路径。

4. 重启 Cursor

## 使用方式

配置完成后，你可以在 Cursor 中直接使用 AI 助手调用目录扫描功能：

```
请扫描 example.com 的敏感路径
```

或者更详细的请求：

```
扫描 https://example.com，使用自定义字典文件 /path/to/wordlist.txt，
超时时间设为 10 秒，并将结果保存到 /path/to/results.json
```

## 文件说明

- `mcp_server.py` - MCP 服务器主文件
- `mcp_config.json` - MCP 配置示例
- `test_mcp.py` - 测试脚本
- `MCP_README.md` - 详细文档
- `QUICKSTART.md` - 本文件（快速开始指南）

## 常见问题

### Q: 如何知道 MCP 服务器是否正常工作？
A: 运行 `python3 test_mcp.py` 进行测试

### Q: 如何修改配置路径？
A: 编辑 `mcp_config.json` 或 Cursor 的 MCP 配置文件，确保路径是绝对路径

### Q: 扫描结果保存在哪里？
A: 如果指定了 `output_json` 或 `output_csv` 参数，结果会保存到指定路径；否则只返回在响应中

