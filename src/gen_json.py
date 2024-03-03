import json

def generate_config(num_nodes, start_port=50000):
    addresses = []
    for i in range(num_nodes):
        port = start_port + i * 2  # 为了避免端口冲突，每个节点分配两个端口
        internal_port = port + 1
        addresses.append({
            "ip": "127.0.0.1",
            "port": port,
            "internal_port": internal_port
        })
    config = {"addresses": addresses}
    with open('../config.json', 'w') as f:
        json.dump(config, f, indent=4)

# 调用函数生成配置文件，例如生成20个节点的配置
generate_config(99)