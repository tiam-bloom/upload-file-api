@echo off
chcp 65001
REM --- 启用文件和打印机共享 ---
echo 正在启用文件和打印机共享...
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes

REM --- 启用 SMB 服务 (确保 SMB 1.0/2.0/3.0 已启用) ---
echo 正在启用 SMB 协议服务...
sc config lanmanserver start= auto
net start lanmanserver

REM --- 设置 D 盘为共享并配置访问权限 ---
echo 正在共享 D 盘...
net share DDrive=D:\ /GRANT:admin,FULL

REM --- 创建 admin 用户并设置密码 ---
echo 正在创建用户 admin 并设置密码...
net user admin 123456 /add
net localgroup administrators admin /add

REM --- 设置 D 盘权限 (完全控制权限) ---
echo 正在设置 D 盘的文件夹权限...
icacls "D:\" /grant admin:(OI)(CI)F

REM --- 提示完成 ---
echo SMB 文件共享已配置完成！现在可以通过 SMB 协议访问 D 盘。
pause
