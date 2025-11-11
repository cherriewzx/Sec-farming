#!/usr/bin/env python3
"""
测试 MCP 服务器的脚本
"""

import json
import subprocess
import sys
from pathlib import Path


def test_mcp_server():
    """测试 MCP 服务器的各个功能"""
    
    server_path = Path(__file__).parent / "mcp_server.py"
    
    print("=" * 60)
    print("测试 MCP Directory Scanner 服务器")
    print("=" * 60)
    
    # 测试 1: 初始化
    print("\n[测试 1] 初始化服务器...")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    result = send_request(server_path, request)
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 测试 2: 获取工具列表
    print("\n[测试 2] 获取工具列表...")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    result = send_request(server_path, request)
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 测试 3: 调用扫描工具（使用本地测试服务器）
    print("\n[测试 3] 调用扫描工具（扫描本地服务器 http://47.121.121.27:8000/）...")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "scan_directory",
            "arguments": {
                "target": "http://47.121.121.27:8000/",
                "timeout": 5,
                "follow_redirects": True,
                "save_all": False
            }
        }
    }
    result = send_request(server_path, request)
    
    if result.get("result"):
        content = result["result"].get("content", [])
        if content:
            result_data = json.loads(content[0].get("text", "{}"))
            print(f"扫描摘要:")
            print(f"  - 目标数量: {result_data.get('summary', {}).get('targets_scanned', 0)}")
            print(f"  - 发现数量: {result_data.get('summary', {}).get('total_findings', 0)}")
            print(f"\n详细结果（前3条）:")
            results = result_data.get("results", [])[:3]
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r.get('url')} - 状态码: {r.get('status')}, 关键词: {r.get('keyword_hits')}")
    else:
        print(f"错误: {result.get('error', {})}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def send_request(server_path: Path, request: dict) -> dict:
    """发送请求到 MCP 服务器并获取响应"""
    try:
        process = subprocess.Popen(
            ["python3", str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        request_json = json.dumps(request)
        stdout, stderr = process.communicate(input=request_json, timeout=10)
        
        if stderr:
            print(f"警告: {stderr}", file=sys.stderr)
        
        if stdout:
            try:
                return json.loads(stdout.strip())
            except json.JSONDecodeError:
                return {"error": {"message": f"无法解析响应: {stdout}"}}
        else:
            return {"error": {"message": "没有收到响应"}}
            
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": {"message": "请求超时"}}
    except Exception as e:
        return {"error": {"message": f"执行错误: {str(e)}"}}


if __name__ == "__main__":
    test_mcp_server()

