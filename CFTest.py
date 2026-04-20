import requests, re, os, ipaddress, random, uuid
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict

myID = uuid

# ✅ URL源与简称
sources = {
    'https://api.uouin.com/cloudflare.html': 'Uouin',
    'https://ip.164746.xyz': 'ZXW',
    'https://ipdb.api.030101.xyz/?type=bestcf': 'IPDB',
    'https://www.wetest.vip/page/cloudflare/address_v6.html': 'WeTestV6',
    'https://ipdb.api.030101.xyz/?type=bestcfv6': 'IPDBv6',
    'https://cf.090227.xyz/CloudFlareYes': 'CFYes',
    'https://ip.haogege.xyz': 'HaoGG',
    'https://vps789.com/openApi/cfIpApi': 'VPS',
    'https://www.wetest.vip/page/cloudflare/address_v4.html': 'WeTest',
    'https://addressesapi.090227.xyz/ct': 'CMLiuss',
    'https://addressesapi.090227.xyz/cmcc-ipv6': 'CMLiussv6',
    'https://raw.githubusercontent.com/xingpingcn/enhanced-FaaS-in-China/refs/heads/main/Cf.json': 'FaaS'
}

PORT = '443'  # 目标端口号

# 正则表达式
ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
ipv6_candidate_pattern = r'([a-fA-F0-9:]{2,39})'
base_url = "https://ipinfo.io"
path = "country"

headers = {
    'User-Agent': 'Mozilla/5.0'
}

# 删除旧文件
for file in ['output.txt']:
    if os.path.exists(file):
        os.remove(file)

# IP 分类存储池 (subnet -> set of ips)
ipv4_pool = defaultdict(set)
ipv6_dict = {}

# 当前时间
beijing_time = datetime.utcnow() + timedelta(hours=8)
timestamp = beijing_time.strftime('%Y%m%d_%H:%M')

print("开始抓取 IP 源...")

# 遍历来源获取原始 IP 数据
for url, shortname in sources.items():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text

        if url.endswith('.txt'):
            text = content
        else:
            soup = BeautifulSoup(content, 'html.parser')
            # 尝试提取文本
            elements = soup.find_all('tr') or soup.find_all('li') or [soup]
            text = '\n'.join(el.get_text() if hasattr(el, 'get_text') else str(el) for el in elements)

        # IPv4 提取与网段分组
        found_v4 = re.findall(ipv4_pattern, text)
        for ip in found_v4:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.version == 4:
                    # 计算 /24 网段
                    subnet = ".".join(ip.split(".")[:-1]) + ".0/24"
                    ipv4_pool[subnet].add(ip)
            except ValueError:
                continue

        # IPv6 提取 (保持原逻辑)
        found_v6 = re.findall(ipv6_candidate_pattern, text)
        for ip in found_v6:
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.version == 6:
                    ip_with_port = f"[{ip_obj.compressed}]:{PORT}"
                    if ip_with_port not in ipv6_dict:
                        comment = f"{shortname}-{myID.uuid4().hex[27:]}{str(random.randint(0,10))}"
                        ipv6_dict[ip_with_port] = comment
            except ValueError:
                continue

        print(f"  - 已处理: {shortname}")

    except Exception as e:
        print(f"  - [错误] {shortname}: {e}")

# 处理 IPv4：每个网段随机选 2 个并查询归属地
ipv4_dict = {}
print(f"正在处理网段去重 (共 {len(ipv4_pool)} 个网段)...")

for subnet, ips in ipv4_pool.items():
    # 每个网段随机选 2 个
    selected_ips = random.sample(list(ips), min(len(ips), 1))
    
    for ip in selected_ips:
        try:
            # 仅对选中的 IP 查询国家，节省 API 请求
            resp = requests.get(f"{base_url}/{ip}/{path}", timeout=5)
            location = resp.text.strip() or "Unknown"
            
            ip_with_port = f"{ip}:{PORT}"
            comment = f"{location}-{myID.uuid4().hex[27:]}{str(random.randint(0,10))}"
            ipv4_dict[ip_with_port] = comment
        except:
            # 查询失败则默认显示 US 或过滤掉
            ip_with_port = f"{ip}:{PORT}"
            ipv4_dict[ip_with_port] = f"Unknown-{myID.uuid4().hex[27:]}{str(random.randint(0,10))}"

# 写入 output.txt
with open('output.txt', 'w') as f4:
    f4.write(f"ipv4.list.updated.at#Upd{timestamp}\n")
    for ip_port in sorted(ipv4_dict):
        f4.write(f"{ip_port}#{ipv4_dict[ip_port]}\n")

# 写入 ipv6.txt
with open('ipv6.txt', 'w') as f6:
    f6.write(f"ipv6.list.updated.at#Upd{timestamp}\n")
    for ip_port in sorted(ipv6_dict):
        f6.write(f"{ip_port}#{ipv6_dict[ip_port]}\n")

print(f"\n✅ 处理完成！")
print(f"IPv4: 已写入 output.txt，共 {len(ipv4_dict)} 个 (每个 /24 网段最多 2 个)")
print(f"IPv6: 已写入 ipv6.txt，共 {len(ipv6_dict)} 个")
