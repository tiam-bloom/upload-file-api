
# python3.8 pip install pywinrm 
import winrm
# 创建远程会话
remote_computer = "http://192.168.110.170:5985/wsman"  # 目标设备的 WinRM 地址
username = "admin"
password = "123456"

# winrs -r:192.168.110.170:5985 -u:admin -p:123456 ipconfig

session = winrm.Session(remote_computer, auth=(username, password),  transport="ntlm")
# from requests_kerberos import HTTPKerberosAuth
# session = winrm.Session(remote_computer, auth= HTTPKerberosAuth())

# 执行命令
command = "ipconfig /all"
response = session.run_cmd(command)

print(response.status_code)
# 打印结果
print("STDOUT:", response.std_out.decode("ISO-8859-1"))
# print("STDERR:", response.std_err.decode())
