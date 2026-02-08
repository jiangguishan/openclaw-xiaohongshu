# 小红书MCP插件 for OpenClaw

通过标准 MCP 协议对接 [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)，为 OpenClaw 提供完整的小红书自动化能力。

## ✨ 功能

- 🔐 **扫码登录** - 通过二维码登录小红书
- 📝 **发布内容** - 图文/视频发布，支持标签和定时发布
- 🔍 **搜索内容** - 关键词搜索，支持排序和筛选
- 📋 **推荐列表** - 获取首页推荐内容
- 💬 **评论互动** - 发表评论、回复评论
- ❤️ **点赞收藏** - 点赞/取消点赞、收藏/取消收藏
- 👤 **用户主页** - 获取用户资料和笔记列表
- 📊 **帖子详情** - 获取完整内容、互动数据和评论

## 📦 安装

### 前置要求

1. **OpenClaw** 已安装并运行
2. **Python 3.8+** 已安装
3. **小红书MCP服务** - 从 [Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载

### 快速安装

```bash
# 1. 克隆或下载本插件
git clone <本仓库地址> xiaohongshu-mcp-plugin
cd xiaohongshu-mcp-plugin

# 2. 运行安装脚本
python scripts/install.py

# 3. 重启 OpenClaw
openclaw gateway restart
```

### 手动安装

```bash
# 创建符号链接到 OpenClaw 扩展目录
# Windows
mklink /D "%USERPROFILE%\.openclaw\extensions\xiaohongshu-mcp" "插件完整路径"

# macOS/Linux
ln -s "插件完整路径" ~/.openclaw/extensions/xiaohongshu-mcp

# 安装Python依赖
pip install requests

# 重启 OpenClaw
openclaw gateway restart
```

## 🚀 使用

### 1. 启动MCP服务

```bash
# Windows
xiaohongshu-mcp-windows-amd64.exe -port :18060

# macOS
./xiaohongshu-mcp-darwin-arm64 -port :18060
```

### 2. 登录

对 OpenClaw 说：
> "帮我登录小红书"

它会返回一个二维码，用小红书App扫码即可。

### 3. 开始使用

自然语言即可操作：
- "搜索小红书上关于AI的内容"
- "发一条小红书帖子：标题是'今日分享'，内容是..."
- "帮我看看这个帖子的评论"
- "给这条笔记点个赞"

## 📁 插件结构

```
xiaohongshu-mcp-plugin/
├── openclaw.plugin.json          # 插件清单
├── package.json                  # npm包信息
├── index.js                      # OpenClaw工具注册（11个Agent Tools）
├── README.md                     # 本文件
├── skills/
│   └── xiaohongshu/
│       ├── SKILL.md              # 技能说明
│       └── mcp_client.py         # MCP标准客户端（核心）
└── scripts/
    └── install.py                # 安装脚本
```

## 🔧 配置

在 OpenClaw 配置中可调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `mcpUrl` | `http://localhost:18060/mcp` | MCP服务地址 |
| `chromeBin` | 自动检测 | Chrome浏览器路径 |
| `headless` | `true` | 无头模式 |
| `port` | `18060` | MCP服务端口 |

## ⚠️ 注意事项

1. **同一账号不能多端网页登录** - MCP登录后不要在其他网页端登录
2. **发布频率** - 建议每天不超过50篇
3. **内容规范** - 遵守小红书社区规则
4. **Cookies** - 过期后重新扫码即可，不会封号

## 🏗️ 架构

```
OpenClaw Agent
    ↓ (Agent Tools)
index.js → 11个注册工具
    ↓ (subprocess)
mcp_client.py → MCP Streamable HTTP 协议
    ↓ (HTTP POST)
xiaohongshu-mcp 服务 (Go + rod浏览器自动化)
    ↓ (Chrome)
小红书网页
```

## 📄 许可证

MIT License

## 🙏 致谢

- [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) - MCP服务核心
- [OpenClaw](https://github.com/openclaw/openclaw) - AI助手平台
