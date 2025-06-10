import base64


# 写一个吧字符串转化base64字符的函数
def base64_encode(string):
    b64_text = base64.b64encode(string.encode("utf-8")).decode("utf-8")
    print(b64_text)
    return b64_text


if __name__ == "__main__":
    base64_encode("""vmess://78d27d94-6e52-4364-b4d5-6ccb04d6e69b@1749382941.tencentapp.cn:2053?encryption=auto&host=1749383511.speed.nlb.cccp.freefly.pp.ua&path=%2F&security=tls&sni=1749383511.speed.nlb.cccp.freefly.pp.ua&type=ws#%E5%BE%B7%E5%9B%BD%E7%BA%BD%E4%BC%A6%E5%A0%A11%20%7C%200x
    vmess://78d27d94-6e52-4364-b4d5-6ccb04d6e69b@1749382941.tencentapp.cn:8443?encryption=auto&host=1749383511.speed.adl.cccp.freefly.pp.ua&path=%2F&security=tls&sni=1749383511.speed.adl.cccp.freefly.pp.ua&type=ws#%E7%BE%8E%E5%9B%BD%E5%8D%97%E9%83%A8%E8%BE%BE%E6%8B%89%E6%96%AF
    vless://7f8b71f3-119d-4909-9649-3890176b6bf1@visa.com:8880?ed=2560&eh=Sec-WebSocket-Protocol&encryption=none&host=crypto-nebula-590.liuchuang2024.workers.dev&path=%2F&type=ws#worker%E8%8A%82%E7%82%B9
    vmess://78d27d94-6e52-4364-b4d5-6ccb04d6e69b@1749382941.tencentapp.cn:2096?encryption=auto&host=1749383511.speed.trabblsacxa.cccp.freefly.pp.ua&path=%2F&security=tls&sni=1749383511.speed.trabblsacxa.cccp.freefly.pp.ua&type=ws#%E5%9C%9F%E8%80%B3%E5%85%B6
    vmess://78d27d94-6e52-4364-b4d5-6ccb04d6e69b@1749382941.tencentapp.cn:2053?encryption=auto&host=1749383511.speed.laxha.cccp.freefly.pp.ua&path=%2F&security=tls&sni=1749383511.speed.laxha.cccp.freefly.pp.ua&type=ws#%E7%BE%8E%E5%9B%BD%E8%A5%BF%E9%83%A8%E6%B4%9B%E6%9D%89%E7%9F%B6
    trojan://85f133142f04dbf6547da33895cfabb3@113.99.140.184:39001/?type=tcp&security=tls&sni=www.yrtok.com&allowInsecure=1#%E9%A6%99%E6%B8%AF%20
    trojan://85f133142f04dbf6547da33895cfabb3@113.99.140.184:39001/?type=tcp&security=tls&sni=www.yrtok.com&allowInsecure=1#%E9%A6%99%E6%B8%AF
    vless://1a13b791-c067-48c0-8e23-e55fbe57d428@47.243.247.159:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=7cdd6be326b8db05.iryanc.com&fp=chrome&pbk=XYv1ZOcugsZ2PworI7Ya3tgFxNpqdGdNaIkwAS0BvXo&sid=1fe8907ce3368240&type=tcp&headerType=none#%E9%A6%99%E6%B8%AF-direct""")
