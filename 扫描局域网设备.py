# pip install python-nmap
# https://nmap.org/download#windows
import nmap


def nmap_scan_network(target_ip):
    """
    使用 nmap 扫描目标 IP 地址，获取开放端口和服务信息。

    参数:
        target_ip (str): 要扫描的 IP 地址或网段，例如 "192.168.1.0/24" 或 "192.168.1.1"

    返回:
        dict: 扫描结果，包含开放端口和服务信息
    """
    # 指定 nmap.exe 路径
    nmap_path = [r"F:\Program\Nmap\nmap.exe"]
    nm = nmap.PortScanner(nmap_search_path=nmap_path)

    # 执行扫描，-p 1-1024 : 扫描目标 IP 地址的 1-1024 端口
    nm.scan(hosts=target_ip, arguments="-O -T4 -p 5985")

    # 解析结果
    scan_results = {}

    for host in nm.all_hosts():
        osmatch = nm[host].get("osmatch", [])
        if osmatch:
            system = osmatch[0].get("name", "")
        else:
            system = "未知系统"

        scan_results[host] = {
            "hostnames": nm[host].hostname(),
            "state": nm[host].state(),
            "system": system,
            "open_ports": [],
        }

        # 遍历所有开放端口
        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            for port in lport:
                service = nm[host][proto][port]["name"]
                scan_results[host]["open_ports"].append((port, service))

    return scan_results


if __name__ == "__main__":
    # 指定要扫描的网段，例如 "192.168.1.0/24"
    network = "192.168.31.0/24"
    print(f"正在扫描网段: {network} ...")

    results = nmap_scan_network(network)
    
    # 输出扫描结果
    for index, (host, data) in enumerate(results.items()):
        print(
            f"{index} 扫描到设备: {host} (主机名: {data['hostnames']}, 状态: {data['state']}), 操作系统: {data['system']}"
        )
        for port, service in data["open_ports"]:
            print(f"  开放端口: {port}, 服务: {service}")
