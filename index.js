
/**
 * 小红书MCP插件 - OpenClaw Agent Tools（优化版v3.0）
 * 通过标准MCP Streamable HTTP协议对接 xpzouying/xiaohongshu-mcp 服务
 * 
 * 优化目标：
 * - 更稳定 - 完善的错误处理和重试机制
 * - 更通用 - 任何OpenClaw模型都能方便调用
 * - 更智能 - 自动处理图片、标签、字数限制
 */

const { execSync, spawn } = require("child_process");
const path = require("path");

module.exports = function (api) {
  const skillDir = path.join(__dirname, "skills", "xiaohongshu");

  // ── 工具1：检查登录状态 ──
  api.registerTool({
    name: "xiaohongshu_check_login",
    description: "检查小红书登录状态",
    parameters: { type: "object", properties: {}, additionalProperties: false },
    async execute() {
      return runPython(skillDir, "mcp_client.py", ["status"]);
    },
  });

  // ── 工具2：获取登录二维码 ──
  api.registerTool({
    name: "xiaohongshu_login",
    description: "获取小红书登录二维码，返回二维码图片路径，用户需用小红书App扫码（二维码有效期约2分钟）",
    parameters: { type: "object", properties: {}, additionalProperties: false },
    async execute() {
      return runPython(skillDir, "mcp_client.py", ["login"]);
    },
  });

  // ── 工具3：搜索内容 ──
  api.registerTool({
    name: "xiaohongshu_search",
    description: "搜索小红书内容，返回帖子列表（包含标题、作者、互动数据、xsec_token等）",
    parameters: {
      type: "object",
      properties: {
        keyword: { type: "string", description: "搜索关键词" },
        sort_by: { type: "string", description: "排序：综合|最新|最多点赞|最多评论|最多收藏", default: "综合" },
        note_type: { type: "string", description: "类型：不限|视频|图文", default: "不限" },
      },
      required: ["keyword"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      const args = ["search", params.keyword];
      if (params.sort_by) args.push("--sort", params.sort_by);
      if (params.note_type) args.push("--type", params.note_type);
      return runPython(skillDir, "mcp_client.py", args);
    },
  });

  // ── 工具4：获取推荐列表 ──
  api.registerTool({
    name: "xiaohongshu_feeds",
    description: "获取小红书首页推荐内容列表",
    parameters: { type: "object", properties: {}, additionalProperties: false },
    async execute() {
      return runPython(skillDir, "mcp_client.py", ["feeds"]);
    },
  });

  // ── 工具5：发布图文（基础版） ──
  api.registerTool({
    name: "xiaohongshu_publish",
    description: "发布图文内容到小红书（标题最多20字，正文最多1000字）",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "帖子标题（最多20个中文字符）" },
        content: { type: "string", description: "帖子正文（最多1000字）" },
        images: { type: "array", items: { type: "string" }, description: "图片路径或URL列表（至少1张）" },
        tags: { type: "array", items: { type: "string" }, description: "话题标签列表，如 ['AI', '科技']" },
      },
      required: ["title", "content", "images"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "publish",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具6：智能发布（新增v3.0） ──
  api.registerTool({
    name: "xiaohongshu_smart_publish",
    description: "智能发布图文到小红书（自动优化标题、内容、图片、标签，带重试机制）",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "帖子标题（自动优化到20字以内）" },
        content: { type: "string", description: "帖子正文（自动优化到1000字以内）" },
        images: { type: "array", items: { type: "string" }, description: "图片路径列表（自动检查有效性）" },
        tags: { type: "array", items: { type: "string" }, description: "话题标签列表（不填自动生成）" },
        auto_optimize: { type: "boolean", description: "是否自动优化（默认true）", default: true },
      },
      required: ["title", "content", "images"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "smart_publish",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具7：发布视频 ──
  api.registerTool({
    name: "xiaohongshu_publish_video",
    description: "发布视频内容到小红书（仅支持本地视频文件）",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "视频标题（最多20字）" },
        content: { type: "string", description: "视频描述" },
        video: { type: "string", description: "本地视频文件绝对路径" },
        tags: { type: "array", items: { type: "string" }, description: "话题标签" },
      },
      required: ["title", "content", "video"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "publish_video",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具8：帖子详情 ──
  api.registerTool({
    name: "xiaohongshu_detail",
    description: "获取小红书帖子详情（内容、评论、互动数据）。需要feed_id和xsec_token，可从搜索或推荐结果中获取",
    parameters: {
      type: "object",
      properties: {
        feed_id: { type: "string", description: "帖子ID" },
        xsec_token: { type: "string", description: "访问令牌" },
        load_all_comments: { type: "boolean", description: "是否加载全部评论", default: false },
      },
      required: ["feed_id", "xsec_token"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "detail",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具9：发表评论 ──
  api.registerTool({
    name: "xiaohongshu_comment",
    description: "在小红书帖子下发表评论",
    parameters: {
      type: "object",
      properties: {
        feed_id: { type: "string", description: "帖子ID" },
        xsec_token: { type: "string", description: "访问令牌" },
        comment: { type: "string", description: "评论内容" },
      },
      required: ["feed_id", "xsec_token", "comment"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "comment",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具10：点赞 ──
  api.registerTool({
    name: "xiaohongshu_like",
    description: "为小红书帖子点赞或取消点赞",
    parameters: {
      type: "object",
      properties: {
        feed_id: { type: "string", description: "帖子ID" },
        xsec_token: { type: "string", description: "访问令牌" },
        unlike: { type: "boolean", description: "true=取消点赞", default: false },
      },
      required: ["feed_id", "xsec_token"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "like",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具11：收藏 ──
  api.registerTool({
    name: "xiaohongshu_favorite",
    description: "收藏或取消收藏小红书帖子",
    parameters: {
      type: "object",
      properties: {
        feed_id: { type: "string", description: "帖子ID" },
        xsec_token: { type: "string", description: "访问令牌" },
        unfavorite: { type: "boolean", description: "true=取消收藏", default: false },
      },
      required: ["feed_id", "xsec_token"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "favorite",
        JSON.stringify(params),
      ]);
    },
  });

  // ── 工具12：用户主页 ──
  api.registerTool({
    name: "xiaohongshu_user_profile",
    description: "获取小红书用户主页信息（昵称、粉丝数、笔记列表等）",
    parameters: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "用户ID" },
        xsec_token: { type: "string", description: "访问令牌" },
      },
      required: ["user_id", "xsec_token"],
      additionalProperties: false,
    },
    async execute(_id, params) {
      return runPython(skillDir, "mcp_client.py", [
        "user_profile",
        JSON.stringify(params),
      ]);
    },
  });
};

// ── Helper（优化版） ──

function runPython(cwd, script, args) {
  return new Promise((resolve) =&gt; {
    try {
      const cmd = `python "${path.join(cwd, script)}" ${args
        .map((a) =&gt; `"${a.replace(/"/g, '\\"')}"`)
        .join(" ")}`;
      const output = execSync(cmd, {
        cwd,
        timeout: 300_000, // 增加到5分钟
        encoding: "utf8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      });
      resolve({ content: [{ type: "text", text: output.trim() }] });
    } catch (e) {
      resolve({
        content: [{ type: "text", text: `❌ 执行失败: ${e.message}\n\n建议：\n1. 检查MCP服务是否运行在端口18060\n2. 检查是否已登录小红书\n3. 检查图片路径是否正确\n4. 检查标题是否在20字以内` }],
      });
    }
  });
}

