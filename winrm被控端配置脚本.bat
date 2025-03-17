@echo off
chcp 65001
REM --- 启用 WinRM 服务 ---
echo 正在启用 WinRM 服务...
winrm quickconfig -q

REM --- 配置 WinRM 信任所有 IP 来源 ---
echo 正在配置 WinRM 允许所有 IP 来源...
winrm set winrm/config/client '@{TrustedHosts="*"}'

REM --- 配置 WinRM 允许使用基本身份验证（例如 admin/123456）---
echo 正在配置 WinRM 允许基本身份验证...
winrm set winrm/config/service/Auth '@{Basic="true"}'

REM --- 配置 WinRM 允许通过 HTTP 进行通信 ---
echo 正在配置 WinRM 允许通过 HTTP 进行通信...
winrm set winrm/config/service '@{AllowUnencrypted="true"}'

REM --- 配置管理员账户 admin ---
echo 正在配置管理员账户 admin...
net user admin 123456 /add
net localgroup administrators admin /add

REM --- 启动 WinRM 服务 ---
echo 启动 WinRM 服务...
net start winrm

echo 被控端 WinRM 配置完成！
pause
