#!/usr/bin/env python3
"""
MCP wrapper for dir_serch.py

功能：
- 将 dir_serch 的扫描功能封装为可供 MCP 调用的 HTTP 接口
- 输入参数：target、wordlist、timeout、save_all 等
- 输出结构化 JSON 结果
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import uvicorn

# 导入你已有的扫描逻辑
from dir_serch import (
    normalize_target,
    load_wordlist,
    scan_target,
    DEFAULT_WORDLIST
)

app = FastAPI(title="DirScan MCP Service", version="1.0.0")


class ScanRequest(BaseModel):
    target: str
    wordlist_path: Optional[str] = None
    timeout: int = 8
    follow_redirects: bool = True
    save_all: bool = False
    user_agent: str = "DirScanMCP/1.0"


@app.post("/tool/dir_scan")
def dir_scan(req: ScanRequest):
    """
    扫描接口：
    POST /tool/dir_scan
    body:
    {
      "target": "example.com",
      "timeout": 8
    }
    """
    target = normalize_target(req.target)
    if not target:
        raise HTTPException(status_code=400, detail="Invalid target")

    paths = load_wordlist(Path(req.wordlist_path)) if req.wordlist_path else DEFAULT_WORDLIST.copy()

    results = scan_target(
        target,
        paths,
        timeout=req.timeout,
        follow_redirects=req.follow_redirects,
        save_all=req.save_all,
        headers={"User-Agent": req.user_agent},
    )

    return {"target": target, "result_count": len(results), "results": results}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9999)
