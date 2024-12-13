
# pip install smbprotocol
import smbclient

# 配置 SMB 共享信息
server = "192.168.31.134"  # 目标设备的 IP 地址
share = "SharedFiles"   # SMB 共享的文件夹
username = "Administrator"         # 登录的用户名
password = "123456"     # 登录的密码

# 待上传的文件和目标路径
local_file = "群控.py"
remote_path = f"\\\\{server}\\{share}\\定时调度.py"

# 开始上传
with smbclient.open_file(remote_path, mode='wb', username=username, password=password) as remote_file:
    with open(local_file, 'rb') as local_file_data:
        remote_file.write(local_file_data.read())

print(f"文件成功上传到 {remote_path}")
