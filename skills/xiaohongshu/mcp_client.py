#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书 MCP 标准客户端 v2.0
对接 xpzouying/xiaohongshu-mcp 的 Streamable HTTP 协议
支持全部 13 个原生工具

用法:
    python mcp_client.py status                    # 检查登录
    python mcp_client.py login                     # 获取二维码
    python mcp_client.py search <keyword>          # 搜索
    python mcp_client.py feeds                     # 推荐列表
    python mcp_client.py publish <json>            # 发布图文
    python mcp_client.py publish_video <json>      # 发布视频
    python mcp_client.py detail <json>             # 帖子详情
    python mcp_client.py comment <json>            # 评论
    python mcp_client.py like <json>               # 点赞
    python mcp_client.py favorite <json>           # 收藏
    python mcp_client.py user_profile <json>       # 用户主页
"""

import json
import base64
import os
import sys
import requests

# 默认配置
DEFAULT_MCP_URL = "http://localhost:18060/mcp"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")


class MCPClient:
    """MCP Streamable HTTP 客户端"""

    def __init__(self, url=None):
        self.url = url or os.environ.get("XIAOHONGSHU_MCP_URL", DEFAULT_MCP_URL)
        self.session_id = None
        self._id = 0
        self._ready = False

    def _next_id(self):
        self._id += 1
        return str(self._id)

    def _post(self, method, params=None, notification=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params:
            body["params"] = params
        if not notification:
            body["id"] = self._next_id()

        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        r = requests.post(self.url, json=body, headers=headers, timeout=180)

        if "Mcp-Session-Id" in r.headers:
            self.session_id = r.headers["Mcp-Session-Id"]

        if r.status_code == 202:
            return {}

        ct = r.headers.get("Content-Type", "")
        if "text/event-stream" in ct:
            for line in reversed(r.text.split("\n")):
                if line.startswith("data:"):
                    try:
                        return json.loads(line[5:].strip())
                    except Exception:
                        pass
            return {"raw": r.text[:500]}

        try:
            return r.json()
        except Exception:
            return {"error": f"HTTP {r.status_code}", "body": r.text[:300]}

    def _init(self):
        if self._ready:
            return
        self._post("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "xiaohongshu-mcp-plugin", "version": "2.0"}
        })
        self._post("notifications/initialized", notification=True)
        self._ready = True

    def call(self, tool, arguments=None):
        """调用MCP工具，返回文本结果列表"""
        self._init()
        params = {"name": tool}
        if arguments:
            params["arguments"] = arguments
        resp = self._post("tools/call", params)

        # 提取内容
        content = resp.get("result", resp).get("content", []) if isinstance(resp, dict) else []
        texts = []
        images = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    texts.append(item["text"])
                elif item.get("type") == "image":
                    images.append(item)

        if resp.get("error"):
            texts.append(f"错误: {json.dumps(resp['error'], ensure_ascii=False)}")

        return texts, images


# ── 便捷函数 ──────────────────────────────────────────────

def check_login(client):
    texts, _ = client.call("check_login_status")
    return "\n".join(texts) if texts else "无响应"


def get_qrcode(client):
    texts, images = client.call("get_login_qrcode")
    result = []
    for t in texts:
        result.append(t)
    for img in images:
        try:
            data = base64.b64decode(img["data"])
            os.makedirs(DATA_DIR, exist_ok=True)
            qr_path = os.path.join(DATA_DIR, "login_qrcode.png")
            with open(qr_path, "wb") as f:
                f.write(data)
            result.append(f"二维码已保存: {qr_path}")
        except Exception as e:
            result.append(f"保存二维码失败: {e}")
    return "\n".join(result) if result else "无响应"


def search(client, keyword, filters=None):
    args = {"keyword": keyword}
    if filters:
        args["filters"] = filters
    texts, _ = client.call("search_feeds", args)
    return "\n".join(texts) if texts else "无结果"


def list_feeds(client):
    texts, _ = client.call("list_feeds")
    return "\n".join(texts) if texts else "无结果"


def publish(client, title, content, images, tags=None, schedule_at=None):
    args = {"title": title, "content": content, "images": images}
    if tags:
        args["tags"] = tags
    if schedule_at:
        args["schedule_at"] = schedule_at
    texts, _ = client.call("publish_content", args)
    return "\n".join(texts) if texts else "无响应"


def publish_video(client, title, content, video, tags=None):
    args = {"title": title, "content": content, "video": video}
    if tags:
        args["tags"] = tags
    texts, _ = client.call("publish_with_video", args)
    return "\n".join(texts) if texts else "无响应"


def get_detail(client, feed_id, xsec_token, load_all=False):
    args = {"feed_id": feed_id, "xsec_token": xsec_token}
    if load_all:
        args["load_all_comments"] = True
    texts, _ = client.call("get_feed_detail", args)
    return "\n".join(texts) if texts else "无响应"


def post_comment(client, feed_id, xsec_token, content):
    texts, _ = client.call("post_comment_to_feed", {
        "feed_id": feed_id, "xsec_token": xsec_token, "content": content
    })
    return "\n".join(texts) if texts else "无响应"


def like_feed(client, feed_id, xsec_token, unlike=False):
    args = {"feed_id": feed_id, "xsec_token": xsec_token}
    if unlike:
        args["unlike"] = True
    texts, _ = client.call("like_feed", args)
    return "\n".join(texts) if texts else "无响应"


def favorite_feed(client, feed_id, xsec_token, unfavorite=False):
    args = {"feed_id": feed_id, "xsec_token": xsec_token}
    if unfavorite:
        args["unfavorite"] = True
    texts, _ = client.call("favorite_feed", args)
    return "\n".join(texts) if texts else "无响应"


def user_profile(client, user_id, xsec_token):
    texts, _ = client.call("user_profile", {
        "user_id": user_id, "xsec_token": xsec_token
    })
    return "\n".join(texts) if texts else "无响应"


# ── CLI ──────────────────────────────────────────────────

def main():
    client = MCPClient()
    args = sys.argv[1:]

    if not args:
        print("用法: python mcp_client.py <command> [args]")
        print("命令: status | login | search <kw> | feeds | publish <json> | detail <json> | comment <json> | like <json> | favorite <json> | user_profile <json>")
        return

    cmd = args[0]

    if cmd == "status":
        print(check_login(client))

    elif cmd == "login":
        print(get_qrcode(client))

    elif cmd == "search":
        kw = args[1] if len(args) > 1 else "AI"
        filters = None
        # 解析可选的排序和类型参数
        i = 2
        while i < len(args):
            if args[i] == "--sort" and i + 1 < len(args):
                filters = filters or {}
                filters["sort_by"] = args[i + 1]
                i += 2
            elif args[i] == "--type" and i + 1 < len(args):
                filters = filters or {}
                filters["note_type"] = args[i + 1]
                i += 2
            else:
                i += 1
        print(search(client, kw, filters))

    elif cmd == "feeds":
        print(list_feeds(client))

    elif cmd == "publish":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(publish(client, p["title"], p["content"], p["images"], p.get("tags"), p.get("schedule_at")))

    elif cmd == "publish_video":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(publish_video(client, p["title"], p["content"], p["video"], p.get("tags")))

    elif cmd == "detail":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(get_detail(client, p["feed_id"], p["xsec_token"], p.get("load_all_comments", False)))

    elif cmd == "comment":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(post_comment(client, p["feed_id"], p["xsec_token"], p["comment"]))

    elif cmd == "like":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(like_feed(client, p["feed_id"], p["xsec_token"], p.get("unlike", False)))

    elif cmd == "favorite":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(favorite_feed(client, p["feed_id"], p["xsec_token"], p.get("unfavorite", False)))

    elif cmd == "user_profile":
        p = json.loads(args[1]) if len(args) > 1 else {}
        print(user_profile(client, p["user_id"], p["xsec_token"]))

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
