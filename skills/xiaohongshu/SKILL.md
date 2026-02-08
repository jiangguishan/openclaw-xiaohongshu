# 小红书MCP技能

## 概述
通过标准 MCP Streamable HTTP 协议对接 [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 服务，提供完整的小红书自动化能力。

## 前置条件

### 1. 下载 MCP 服务
从 [GitHub Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载：
- `xiaohongshu-mcp-windows-amd64.exe`（MCP服务）
- `xiaohongshu-login-windows-amd64.exe`（登录工具，备用）

### 2. 启动 MCP 服务
```bash
# Windows
xiaohongshu-mcp-windows-amd64.exe -port :18060

# 指定Chrome路径（可选）
xiaohongshu-mcp-windows-amd64.exe -bin "C:\path\to\chrome.exe" -port :18060

# macOS
./xiaohongshu-mcp-darwin-arm64 -port :18060
```

### 3. Python 依赖
```bash
pip install requests
```

## 可用工具（13个）

### 账号管理
| 工具 | 说明 |
|------|------|
| `xiaohongshu_check_login` | 检查登录状态 |
| `xiaohongshu_login` | 获取登录二维码（用小红书App扫码，有效期约2分钟） |

### 内容发布
| 工具 | 说明 |
|------|------|
| `xiaohongshu_publish` | 发布图文（标题≤20字，正文≤1000字，至少1张图） |
| `xiaohongshu_publish_video` | 发布视频（仅支持本地文件） |

### 内容获取
| 工具 | 说明 |
|------|------|
| `xiaohongshu_search` | 搜索内容（支持排序、筛选） |
| `xiaohongshu_feeds` | 获取首页推荐列表 |
| `xiaohongshu_detail` | 获取帖子详情+评论 |
| `xiaohongshu_user_profile` | 获取用户主页信息 |

### 互动功能
| 工具 | 说明 |
|------|------|
| `xiaohongshu_comment` | 发表评论 |
| `xiaohongshu_like` | 点赞/取消点赞 |
| `xiaohongshu_favorite` | 收藏/取消收藏 |

## 使用流程

### 首次使用
1. 启动MCP服务
2. 调用 `xiaohongshu_login` 获取二维码
3. 用小红书App扫码登录
4. 调用 `xiaohongshu_check_login` 验证

### 日常使用
```
# 自然语言即可
"搜索小红书上关于AI的内容"
"发一条小红书帖子，标题是..."
"帮我看看这个帖子的评论"
"给这条笔记点个赞"
```

## 重要提示

1. **同一账号不能多端网页登录** - 登录MCP后不要在其他网页端登录，否则会被踢出
2. **Cookies过期** - 如遇"未登录"，重新扫码即可
3. **发布频率** - 建议每天不超过50篇
4. **内容规范** - 遵守小红书社区规则

## 架构
```
OpenClaw Agent → index.js(工具注册) → mcp_client.py → MCP协议 → xiaohongshu-mcp服务 → Chrome → 小红书
```
