@echo off
chcp 65001 >nul
echo 正在启动小红书MCP服务器...
echo 使用ChromeDriver: D:\openclawWk\chromedriver

set CHROMEDRIVER_PATH=D:\openclawWk\chromedriver
set PATH=%CHROMEDRIVER_PATH%;%PATH%

set XIAOHONGSHU_COOKIES_PATH=D:\openclawWk\xiaohongshu-mcp-plugin\data\xiaohongshu_cookies.json

cd /d "D:\openclawWk\xiaohongshu-mcp-plugin"

xiaohongshu-mcp-windows-amd64.exe -port :18060 -log-level debug

echo.
echo 服务器已停止
pause
