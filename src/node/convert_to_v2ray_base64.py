import yaml
import base64
import re

# 读取节点文件
def load_nodes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('proxies', [])

# SS 节点 URI 生成
def ss_uri(node):
    userinfo = f"{node['cipher']}:{node['password']}"
    userinfo_b64 = base64.urlsafe_b64encode(userinfo.encode()).decode().rstrip('=')
    server = node['server']
    port = node['port']
    plugin = ''
    if 'plugin' in node and node['plugin']:
        plugin_opts = node.get('plugin-opts', {})
        opts = []
        for k, v in plugin_opts.items():
            opts.append(f"{k}={v}")
        plugin = f"/?plugin={node['plugin']}%3B{'%3B'.join(opts)}"
    name = node.get('name', '')
    uri = f"ss://{userinfo_b64}@{server}:{port}{plugin}#{name}"
    return uri

# Trojan 节点 URI 生成
def trojan_uri(node):
    password = node['password']
    server = node['server']
    port = node['port']
    params = []
    if node.get('sni'):
        params.append(f"sni={node['sni']}")
    if node.get('skip-cert-verify'):
        params.append(f"allowInsecure={str(node['skip-cert-verify']).lower()}")
    param_str = '?' + '&'.join(params) if params else ''
    name = node.get('name', '')
    uri = f"trojan://{password}@{server}:{port}{param_str}#{name}"
    return uri

# VLESS 节点 URI 生成
def vless_uri(node):
    uuid = node['uuid']
    server = node['server']
    port = node['port']
    params = []
    if node.get('tls'):
        params.append('security=tls')
    if node.get('flow'):
        params.append(f"flow={node['flow']}")
    if node.get('servername'):
        params.append(f"sni={node['servername']}")
    if node.get('reality-opts'):
        reality = node['reality-opts']
        if reality.get('public-key'):
            params.append(f"public-key={reality['public-key']}")
        if reality.get('short-id'):
            params.append(f"short-id={reality['short-id']}")
    if node.get('client-fingerprint'):
        params.append(f"fp={node['client-fingerprint']}")
    if node.get('network'):
        params.append(f"type={node['network']}")
    param_str = '?' + '&'.join(params) if params else ''
    name = node.get('name', '')
    uri = f"vless://{uuid}@{server}:{port}{param_str}#{name}"
    return uri

# Hysteria2 节点 URI 生成（v2rayN 5.38+ 支持）
def hysteria2_uri(node):
    password = node['password']
    server = node['server']
    port = node['port']
    params = []
    if node.get('auth'):
        params.append(f"auth={node['auth']}")
    if node.get('sni'):
        params.append(f"sni={node['sni']}")
    if node.get('skip-cert-verify') is not None:
        params.append(f"insecure={str(node['skip-cert-verify']).lower()}")
    if node.get('up'):
        params.append(f"upmbps={node['up']}")
    if node.get('down'):
        params.append(f"downmbps={node['down']}")
    param_str = '?' + '&'.join(params) if params else ''
    name = node.get('name', '')
    uri = f"hysteria2://{password}@{server}:{port}{param_str}#{name}"
    return uri

# 主流程
def main():
    nodes = load_nodes('hongxin.txt')
    uri_list = []
    for node in nodes:
        t = node.get('type')
        try:
            if t == 'ss':
                uri = ss_uri(node)
            elif t == 'trojan':
                uri = trojan_uri(node)
            elif t == 'vless':
                uri = vless_uri(node)
            elif t == 'hysteria2':
                uri = hysteria2_uri(node)
            else:
                continue
            uri_list.append(uri)
        except Exception as e:
            print(f"节点解析失败: {node.get('name', '')}，原因: {e}")
    all_uri = '\n'.join(uri_list)
    b64 = base64.b64encode(all_uri.encode('utf-8')).decode('utf-8')
    print(b64)

if __name__ == '__main__':
    main() 