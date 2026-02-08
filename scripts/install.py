#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书MCP插件安装脚本
自动配置 OpenClaw 扩展
"""

import os
import sys
import json
import shutil
import subprocess
import platform

def get_openclaw_extensions_dir():
    """获取 OpenClaw 扩展目录"""
    if platform.system() == "Windows":
        # 尝试常见路径
        candidates = [
            os.path.expanduser("~\\.openclaw\\extensions"),
            os.path.expandvars("%APPDATA%\\openclaw\\extensions"),
        ]
    else:
        candidates = [
            os.path.expanduser("~/.openclaw/extensions"),
            os.path.expanduser("~/.config/openclaw/extensions"),
        ]
    
    for path in candidates:
        parent = os.path.dirname(path)
        if os.path.exists(parent):
            os.makedirs(path, exist_ok=True)
            return path
    
    # 默认
    default = os.path.expanduser("~/.openclaw/extensions")
    os.makedirs(default, exist_ok=True)
    return default


def install():
    print("=" * 50)
    print("  小红书MCP插件安装程序")
    print("=" * 50)
    
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = get_openclaw_extensions_dir()
    target = os.path.join(ext_dir, "xiaohongshu-mcp")
    
    print(f"\n插件目录: {plugin_dir}")
    print(f"安装目标: {target}")
    
    # 检查Python依赖
    print("\n[1/4] 检查Python依赖...")
    try:
        import requests
        print("  ✅ requests 已安装")
    except ImportError:
        print("  📦 安装 requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
        print("  ✅ requests 安装完成")
    
    # 创建符号链接或复制
    print("\n[2/4] 安装插件...")
    if os.path.exists(target):
        if os.path.islink(target):
            os.remove(target)
        else:
            shutil.rmtree(target)
    
    try:
        os.symlink(plugin_dir, target)
        print(f"  ✅ 符号链接创建: {target} → {plugin_dir}")
    except (OSError, NotImplementedError):
        shutil.copytree(plugin_dir, target)
        print(f"  ✅ 文件复制到: {target}")
    
    # 检查MCP服务
    print("\n[3/4] 检查MCP服务...")
    try:
        import requests as req
        r = req.post("http://localhost:18060/mcp", json={
            "jsonrpc": "2.0", "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "installer", "version": "1.0"}},
            "id": "1"
        }, headers={"Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"},
        timeout=10)
        if r.status_code == 200:
            print("  ✅ MCP服务运行正常")
        else:
            print(f"  ⚠️  MCP服务返回 {r.status_code}，请确保服务已启动")
    except Exception:
        print("  ⚠️  MCP服务未运行，请先启动：")
        if platform.system() == "Windows":
            print("     xiaohongshu-mcp-windows-amd64.exe -port :18060")
        else:
            print("     ./xiaohongshu-mcp-darwin-arm64 -port :18060")
    
    # 完成
    print("\n[4/4] 安装完成！")
    print("\n" + "=" * 50)
    print("  后续步骤：")
    print("  1. 确保 MCP 服务已启动")
    print("  2. 重启 OpenClaw：openclaw gateway restart")
    print("  3. 使用 '检查小红书登录状态' 测试")
    print("=" * 50)


def uninstall():
    ext_dir = get_openclaw_extensions_dir()
    target = os.path.join(ext_dir, "xiaohongshu-mcp")
    
    if os.path.exists(target):
        if os.path.islink(target):
            os.remove(target)
        else:
            shutil.rmtree(target)
        print(f"✅ 已卸载: {target}")
    else:
        print("插件未安装")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
