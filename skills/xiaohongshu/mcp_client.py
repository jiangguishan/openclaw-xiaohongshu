
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书 MCP 标准客户端 v3.0（优化版）
对接 xpzouying/xiaohongshu-mcp 的 Streamable HTTP 协议
支持全部 13 个原生工具 + 3 个智能工具

优化目标：
- 更稳定 - 完善的错误处理和重试机制
- 更通用 - 任何OpenClaw模型都能方便调用
- 更智能 - 自动处理图片、标签、字数限制

用法:
    python mcp_client.py status                    # 检查登录
    python mcp_client.py login                     # 获取二维码
    python mcp_client.py search &lt;keyword&gt;          # 搜索
    python mcp_client.py feeds                     # 推荐列表
    python mcp_client.py publish &lt;json&gt;            # 发布图文
    python mcp_client.py smart_publish &lt;json&gt;      # 智能发布（新增）
    python mcp_client.py publish_video &lt;json&gt;      # 发布视频
    python mcp_client.py detail &lt;json&gt;             # 帖子详情
    python mcp_client.py comment &lt;json&gt;            # 评论
    python mcp_client.py like &lt;json&gt;               # 点赞
    python mcp_client.py favorite &lt;json&gt;           # 收藏
    python mcp_client.py user_profile &lt;json&gt;       # 用户主页
"""

import json
import base64
import os
import sys
import time
import requests
from typing import List, Dict, Any, Optional, Tuple

# 默认配置
DEFAULT_MCP_URL = "http://localhost:18060/mcp"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
COOKIES_PATH = os.path.join("D:\\openclawWk\\xiaohongshu-mcp", "cookies.json")

# 智能配置
MAX_TITLE_LENGTH = 20
MAX_CONTENT_LENGTH = 1000
DEFAULT_TAGS = ["AI", "科技", "创业"]
MAX_RETRIES = 3
RETRY_DELAY = 2


class MCPClient:
    """MCP Streamable HTTP 客户端（优化版）"""

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
            "clientInfo": {"name": "xiaohongshu-mcp-plugin", "version": "3.0"}
        })
        self._post("notifications/initialized", notification=True)
        self._ready = True

    def call(self, tool, arguments=None, max_retries=MAX_RETRIES):
        """调用MCP工具，带重试机制"""
        self._init()
        params = {"name": tool}
        if arguments:
            params["arguments"] = arguments

        last_error = None
        for attempt in range(max_retries):
            try:
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
                    error_msg = json.dumps(resp['error'], ensure_ascii=False)
                    texts.append(f"错误: {error_msg}")
                    last_error = error_msg

                    # 如果是最后一次尝试，返回错误
                    if attempt == max_retries - 1:
                        return texts, images

                    # 否则等待重试
                    print(f"   ⚠️  尝试 {attempt + 1}/{max_retries} 失败，等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    continue

                return texts, images

            except Exception as e:
                last_error = str(e)
                if attempt == max_retries - 1:
                    return [f"错误: {last_error}"], []
                print(f"   ⚠️  尝试 {attempt + 1}/{max_retries} 异常: {last_error}，等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)

        return [f"错误: 重试 {max_retries} 次后仍然失败: {last_error}"], []


# ── 智能优化函数 ──────────────────────────────────────────────

def optimize_title(title, max_length=MAX_TITLE_LENGTH):
    """
    智能优化标题到指定长度
    
    返回：(优化后的标题, 是否被缩短)
    """
    if len(title) <= max_length:
        return title, False

    # 策略1：去掉标点符号
    optimized = title.replace("！", "").replace("？", "").replace("，", "").replace("。", "")
    if len(optimized) &lt;= max_length:
        return optimized, True

    # 策略2：截短并加上省略号
    optimized = title[:max_length-1] + "…"
    return optimized, True


def optimize_content(content, max_length=MAX_CONTENT_LENGTH):
    """
    智能优化内容到指定长度
    
    返回：(优化后的内容, 是否被截断)
    """
    if len(content) &lt;= max_length:
        return content, False

    # 截短并加上省略号
    optimized = content[:max_length-1] + "…"
    return optimized, True


def check_images(images):
    """
    检查图片是否存在
    
    返回：(有效图片列表, 无效图片列表)
    """
    valid = []
    invalid = []

    for img in images:
        if os.path.exists(img):
            valid.append(img)
        else:
            # 尝试在常见位置查找
            common_dirs = [
                os.path.dirname(os.path.abspath(__file__)),
                DATA_DIR,
                os.getcwd(),
            ]
            found = False
            for dir_path in common_dirs:
                test_path = os.path.join(dir_path, os.path.basename(img))
                if os.path.exists(test_path):
                    valid.append(test_path)
                    found = True
                    break
            if not found:
                invalid.append(img)

    return valid, invalid


def generate_tags(title, content="", existing_tags=None):
    """
    智能生成标签
    """
    if existing_tags and len(existing_tags) &gt; 0:
        return existing_tags

    tags = []
    title_lower = title.lower()

    # 关键词匹配
    tag_keywords = {
        "AI": ["ai", "chatgpt", "claude", "openai", "anthropic", "人工智能"],
        "科技": ["tech", "科技", "技术", "创新"],
        "创业": ["startup", "创业", "创始人", "公司"],
        "投资": ["invest", "投资", "融资", "资本"],
        "编程": ["code", "编程", "代码", "程序"],
    }

    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword in title_lower or keyword in content:
                if tag not in tags:
                    tags.append(tag)
                break

    # 如果没有标签，使用默认标签
    if len(tags) == 0:
        tags = DEFAULT_TAGS.copy()

    return tags


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


def smart_publish(client, title, content, images, tags=None, auto_optimize=True):
    """
    智能发布（新增）
    
    特点：
    - 自动优化标题到20字以内
    - 自动优化内容到1000字以内
    - 自动检查图片
    - 自动生成标签
    - 详细的优化报告
    """
    result = {
        "success": False,
        "message": "",
        "optimizations": {},
        "error": None
    }

    try:
        # 1. 优化标题
        if auto_optimize:
            optimized_title, title_shortened = optimize_title(title)
            result["optimizations"]["title"] = {
                "original": title,
                "optimized": optimized_title,
                "shortened": title_shortened
            }
            title = optimized_title

        # 2. 优化内容
        if auto_optimize:
            optimized_content, content_truncated = optimize_content(content)
            result["optimizations"]["content"] = {
                "original_length": len(content),
                "optimized_length": len(optimized_content),
                "truncated": content_truncated
            }
            content = optimized_content

        # 3. 检查图片
        valid_images, invalid_images = check_images(images)
        result["optimizations"]["images"] = {
            "valid": valid_images,
            "invalid": invalid_images,
            "count": len(valid_images)
        }

        if len(valid_images) == 0:
            result["error"] = "没有找到有效的图片文件"
            result["message"] = "发布失败：没有找到有效的图片文件"
            return json.dumps(result, ensure_ascii=False)

        # 4. 生成标签
        final_tags = generate_tags(title, content, tags)
        result["optimizations"]["tags"] = {
            "provided": tags,
            "generated": final_tags
        }

        # 5. 发布
        publish_result = publish(client, title, content, valid_images, final_tags)

        result["success"] = True
        result["message"] = "发布成功"
        result["publish_result"] = publish_result

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"发布失败：{str(e)}"
        return json.dumps(result, ensure_ascii=False)


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
        print("=" * 70)
        print("小红书 MCP 客户端 v3.0（优化版）")
        print("=" * 70)
        print("\n基础命令:")
        print("  status                    # 检查登录状态")
        print("  login                     # 获取登录二维码")
        print("  search &lt;keyword&gt;          # 搜索内容")
        print("  feeds                     # 获取推荐列表")
        print("  publish &lt;json&gt;            # 发布图文")
        print("  publish_video &lt;json&gt;      # 发布视频")
        print("  detail &lt;json&gt;             # 帖子详情")
        print("  comment &lt;json&gt;            # 发表评论")
        print("  like &lt;json&gt;               # 点赞/取消点赞")
        print("  favorite &lt;json&gt;           # 收藏/取消收藏")
        print("  user_profile &lt;json&gt;       # 用户主页")
        print("\n智能命令（新增）:")
        print("  smart_publish &lt;json&gt;      # 智能发布（自动优化）")
        print("\n智能发布示例:")
        print('  {')
        print('    "title": "用战争赌博？这事不对劲",')
        print('    "content": "这两天看到一件事...",')
        print('    "images": ["path/to/img1.png", "path/to/img2.png"],')
        print('    "tags": ["AI", "科技"],')
        print('    "auto_optimize": true')
        print('  }')
        print("\n" + "=" * 70)
        return

    cmd = args[0]

    if cmd == "status":
        print(check_login(client))

    elif cmd == "login":
        print(get_qrcode(client))

    elif cmd == "search":
        kw = args[1] if len(args) &gt; 1 else "AI"
        filters = None
        i = 2
        while i &lt; len(args):
            if args[i] == "--sort" and i + 1 &lt; len(args):
                filters = filters or {}
                filters["sort_by"] = args[i + 1]
                i += 2
            elif args[i] == "--type" and i + 1 &lt; len(args):
                filters = filters or {}
                filters["note_type"] = args[i + 1]
                i += 2
            else:
                i += 1
        print(search(client, kw, filters))

    elif cmd == "feeds":
        print(list_feeds(client))

    elif cmd == "publish":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(publish(client, p["title"], p["content"], p["images"], p.get("tags"), p.get("schedule_at")))

    elif cmd == "smart_publish":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(smart_publish(
            client,
            p["title"],
            p["content"],
            p["images"],
            p.get("tags"),
            p.get("auto_optimize", True)
        ))

    elif cmd == "publish_video":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(publish_video(client, p["title"], p["content"], p["video"], p.get("tags")))

    elif cmd == "detail":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(get_detail(client, p["feed_id"], p["xsec_token"], p.get("load_all_comments", False)))

    elif cmd == "comment":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(post_comment(client, p["feed_id"], p["xsec_token"], p["comment"]))

    elif cmd == "like":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(like_feed(client, p["feed_id"], p["xsec_token"], p.get("unlike", False)))

    elif cmd == "favorite":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(favorite_feed(client, p["feed_id"], p["xsec_token"], p.get("unfavorite", False)))

    elif cmd == "user_profile":
        p = json.loads(args[1]) if len(args) &gt; 1 else {}
        print(user_profile(client, p["user_id"], p["xsec_token"]))

    else:
        print(f"未知命令: {cmd}")
        print("\n使用 'python mcp_client.py' 查看帮助")


if __name__ == "__main__":
    main()

