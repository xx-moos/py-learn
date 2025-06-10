#!/usr/bin/env python3
import yaml, base64
from urllib.parse import quote

# 1. 读取 Clash 配置
with open("hongxin.txt", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# 2. 提取节点列表
nodes = cfg.get("proxies", [])

# 3. 按需格式化（这里以常见的 trojan URI 为例，可根据 type 调整）
lines = []
for p in nodes:
    t = p.get("type")
    svr = p.get("server")
    name = p.get("name")
    port = p.get("port")
    pwd = p.get("password")
    sni = p.get("sni", "")
    # URL 参数部分：这里只示范 sni，如需更多可拼接 ?parameter=value&…
    params = f"?sni={quote(sni)}" if sni else ""
    uri = f"{t}://{quote(pwd)}@{svr}:{port}{params}#{quote(name)}"
    # 也可以输出 JSON、YAML 或其他自定义格式
    lines.append(uri)

# 4. 合并并 Base64 编码
plain_text = "\n".join(lines)
b64_text = base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")

# 5. 输出结果
print(b64_text)
