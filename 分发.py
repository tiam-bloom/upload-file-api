# pip install smbprotocol -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
from pathlib import Path
import smbclient

"""
只支持局域网内
"""


class SmbSender:
    def __init__(self, server) -> None:
        # 配置 SMB 共享信息
        self.server = server  # 目标设备的 IP 地址
        self.share = "DDrive"  # SMB 共享的文件夹 D盘
        self.username = "admin"  # 登录的用户名
        self.password = "123456"  # 登录的密码

    def upload_file(self, local_file, remote_file):
        # 目前只支持向已存在的目录下上传
        # remote_path = f"\\\\{self.server}\\{self.share}\\群控.py"
        remote_path = Path(f"\\\\{self.server}\\{self.share}", remote_file)
        # 开始上传
        with smbclient.open_file(
            remote_path, mode="wb", username=self.username, password=self.password
        ) as remote_file:
            with open(local_file, "rb") as local_file_data:
                remote_file.write(local_file_data.read())

        print(f"文件成功上传到 {remote_path}")


if __name__ == "__main__":
    sender = SmbSender("192.168.110.170")
    # 待上传的文件和目标路径
    local_file = Path("群控.py")
    # 确保目标目录存在
    remote_file = Path("文件", "群控.py")
    sender.upload_file(local_file, remote_file)
