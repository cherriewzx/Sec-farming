#!/usr/bin/env python3
"""
MCP Server for Directory Scanner
将 dir_serch.py 封装为 MCP (Model Context Protocol) 工具
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 导入 dir_serch 的核心功能
from dir_serch import (
    DEFAULT_WORDLIST,
    normalize_target,
    load_wordlist,
    load_targets,
    scan_target,
    save_json,
    save_csv,
)


class MCPServer:
    """MCP 服务器实现，通过 stdio 进行 JSON-RPC 通信"""
    
    def __init__(self):
        self.request_id = None
    
    def send_response(self, result: Any = None, error: Optional[Dict] = None):
        """发送 JSON-RPC 响应"""
        response = {
            "jsonrpc": "2.0",
            "id": self.request_id,
        }
        if error:
            response["error"] = error
        else:
            response["result"] = result
        
        print(json.dumps(response), flush=True)
    
    def handle_request(self, request: Dict):
        """处理 JSON-RPC 请求"""
        self.request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        # 如果是通知（没有 id），不发送响应
        is_notification = "id" not in request
        
        try:
            if method == "initialize":
                self.handle_initialize(params)
            elif method == "tools/list":
                if not is_notification:
                    self.handle_tools_list()
            elif method == "tools/call":
                if not is_notification:
                    self.handle_tools_call(params)
            elif method == "notifications/initialized":
                # 初始化通知，不需要响应
                pass
            else:
                if not is_notification:
                    self.send_response(error={
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    })
        except Exception as e:
            if not is_notification:
                self.send_response(error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                })
    
    def handle_initialize(self, params: Dict):
        """处理初始化请求"""
        self.send_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "directory-scanner",
                "version": "1.0.0"
            }
        })
    
    def handle_tools_list(self):
        """返回可用工具列表"""
        self.send_response({
            "tools": [
                {
                    "name": "scan_directory",
                    "description": "扫描目标网站的敏感路径和文件，检测目录遍历、敏感文件泄露等安全问题",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "目标 URL 或域名（例如：example.com 或 https://example.com）"
                            },
                            "targets_file": {
                                "type": "string",
                                "description": "目标列表文件路径（每行一个目标，可选）"
                            },
                            "wordlist": {
                                "type": "string",
                                "description": "路径字典文件路径（每行一个路径，可选，不提供则使用默认字典）"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "请求超时时间（秒，默认 8）",
                                "default": 8
                            },
                            "follow_redirects": {
                                "type": "boolean",
                                "description": "是否跟随 HTTP 重定向（默认 true）",
                                "default": True
                            },
                            "save_all": {
                                "type": "boolean",
                                "description": "是否保存所有请求结果（包括 404，默认 false）",
                                "default": False
                            },
                            "user_agent": {
                                "type": "string",
                                "description": "自定义 User-Agent（可选）",
                                "default": "DirScanSync/1.0"
                            },
                            "output_json": {
                                "type": "string",
                                "description": "JSON 输出文件路径（可选，不提供则不保存文件）"
                            },
                            "output_csv": {
                                "type": "string",
                                "description": "CSV 输出文件路径（可选）"
                            }
                        },
                        "required": ["target"]
                    }
                }
            ]
        })
    
    def handle_tools_call(self, params: Dict):
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "scan_directory":
            result = self.scan_directory(arguments)
            self.send_response({
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            })
        else:
            self.send_response(error={
                "code": -32602,
                "message": f"Unknown tool: {tool_name}"
            })
    
    def scan_directory(self, args: Dict) -> Dict[str, Any]:
        """执行目录扫描"""
        # 收集目标
        targets = []
        
        if args.get("target"):
            targets.append(normalize_target(args["target"]))
        
        if args.get("targets_file"):
            targets_file = Path(args["targets_file"])
            if targets_file.exists():
                targets.extend(load_targets(targets_file))
        
        if not targets:
            return {
                "error": "No targets provided. Please provide 'target' or 'targets_file'.",
                "results": []
            }
        
        # 加载路径字典
        if args.get("wordlist"):
            wordlist_path = Path(args["wordlist"])
            paths = load_wordlist(wordlist_path)
        else:
            paths = DEFAULT_WORDLIST.copy()
        
        # 准备请求头
        headers = {"User-Agent": args.get("user_agent", "DirScanSync/1.0")}
        
        # 扫描参数
        timeout = args.get("timeout", 8)
        follow_redirects = args.get("follow_redirects", True)
        save_all = args.get("save_all", False)
        
        # 执行扫描
        all_results = []
        scan_summary = []
        
        for target in targets:
            results = scan_target(
                target=target,
                paths=paths,
                timeout=timeout,
                follow_redirects=follow_redirects,
                save_all=save_all,
                headers=headers
            )
            all_results.extend(results)
            scan_summary.append({
                "target": target,
                "findings_count": len(results)
            })
        
        # 保存文件（如果指定）
        output_info = {}
        if args.get("output_json"):
            json_path = Path(args["output_json"])
            save_json(json_path, all_results)
            output_info["json_file"] = str(json_path)
        
        if args.get("output_csv"):
            csv_path = Path(args["output_csv"])
            save_csv(csv_path, all_results)
            output_info["csv_file"] = str(csv_path)
        
        # 返回结果
        return {
            "success": True,
            "summary": {
                "targets_scanned": len(targets),
                "total_findings": len(all_results),
                "targets": scan_summary
            },
            "results": all_results,
            "output_files": output_info
        }


def main():
    """主函数：从 stdio 读取 JSON-RPC 请求并处理"""
    server = MCPServer()
    
    # 从标准输入读取 JSON-RPC 请求
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            server.handle_request(request)
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()

