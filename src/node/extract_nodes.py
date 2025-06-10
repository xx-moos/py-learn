#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml, json, base64
from pathlib import Path

# 读取配置
fn = Path('configyaml.txt')
cfg = yaml.safe_load(fn.read_text(encoding='utf-8'))

nodes = []

# 1) 本地落地节点
for p in cfg.get('proxies', []):
    node = {
        'name': p.get('name'),
        'type': p.get('type'),
        'server': p.get('server'),
        'port': p.get('port'),
    }
    # 常见凭证字段
    for key in ('username','password','uuid','alterId','cipher','sni'):
        if p.get(key) is not None:
            node[key] = p[key]
    # dialer-proxy 等额外备注
    if p.get('dialer-proxy'):
        node['dialer-proxy'] = p['dialer-proxy']
    nodes.append(node)

# 2) 订阅源（proxy-providers） —— 只保留 key 与 url
for k, prov in cfg.get('proxy-providers', {}).items():
    nodes.append({
        'name': f"PROVIDER｜{k}",
        'type': prov.get('type'),
        'url': prov.get('url'),
        'interval': prov.get('interval'),
        # 如有 override 也可一起输出
        'override': prov.get('override', {})
    })

# 输出为 JSON（可根据需要改 CSV、URI 列表等）
json_text = json.dumps(nodes, ensure_ascii=False, indent=2)

# Base64 编码输出
b64 = base64.b64encode(json_text.encode('utf-8')).decode('utf-8')
print(b64)

# 如果需要直接写文件：
# Path('nodes_encoded.txt').write_text(b64)
