import requests
from ipaddress import IPv4Network
import csv
import time
import concurrent.futures
import random

# 定义多个基础网段
base_networks = [
    IPv4Network('173.245.48.0/20'),
    IPv4Network('103.21.244.0/22'),
    IPv4Network('103.22.200.0/22'),
    IPv4Network('103.31.4.0/22'),
    IPv4Network('141.101.64.0/18'),
    IPv4Network('108.162.192.0/18'),
    IPv4Network('190.93.240.0/20'),
    IPv4Network('188.114.96.0/20'),
    IPv4Network('197.234.240.0/22'),
    IPv4Network('198.41.128.0/17'),
    IPv4Network('162.158.0.0/16'),
    IPv4Network('162.15.0.0/16'),
    IPv4Network('104.16.0.0/16'),
    IPv4Network('104.17.0.0/16'),
    IPv4Network('104.18.0.0/16'),
    IPv4Network('104.19.0.0/16'),
    IPv4Network('104.24.0.0/16'),
    IPv4Network('104.25.0.0/16'),
    IPv4Network('104.26.0.0/16'),
    IPv4Network('172.64.0.0/16'),
    IPv4Network('172.65.0.0/16'),
    IPv4Network('172.66.0.0/16'),
    IPv4Network('172.67.0.0/16'),
    IPv4Network('131.0.72.0/22')
]

def process_ip(ip, writer):
    url = f"http://{ip}/cdn-cgi/trace"
    try:
        # 记录请求开始时间
        start_time = time.time()
        # 发送请求
        response = requests.get(url, timeout=1)
        # 记录请求结束时间并计算耗时
        end_time = time.time()
        request_time = end_time - start_time

        if response.status_code == 200:
            # 解析响应内容获取 colo 信息
            lines = response.text.splitlines()
            colo_line = next((line for line in lines if line.startswith('colo=')), None)
            if colo_line:
                colo = colo_line.split('=')[1]
                # 将结果写入 CSV 文件
                writer.writerow({'ip': ip, 'colo': colo, 'request_time': request_time})
                # 在控制台输出结果，包含请求耗时
                print(f"{ip}   {colo}   耗时: {request_time:.2f} 秒")
    except requests.RequestException:
        pass

# 打开 CSV 文件以写入结果
with open('results.csv', mode='w', newline='') as csv_file:
    fieldnames = ['ip', 'colo', 'request_time']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    # 写入 CSV 文件的表头
    writer.writeheader()

    ips = []
    # 遍历每个网段
    for base_network in base_networks:
        # 遍历每个 /24 子网
        for subnet in base_network.subnets(new_prefix=24):
            # 生成 9 到 251 之间的随机值 x
            x = random.randint(9, 251)
            # 选取子网中的第 x 个可用 IP 地址
            try:
                #ip = str(list(subnet.hosts())[x - 1])
                ip = str(list(subnet.hosts())[99])
                ips.append(ip)
            except IndexError:
                # 处理子网可用 IP 数量不足的情况
                continue

    # 使用线程池处理 IP
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 这里使用 lambda 函数来传递 writer 参数
        futures = [executor.submit(process_ip, ip, writer) for ip in ips]
        concurrent.futures.wait(futures)
