import json
import os

def main():
    # 定义两个VSCode版本的路径
    vscode_paths = {
        "1": r"D:\editor\Microsoft VS Code\resources\app\product.json",
        "2": r"D:\editor\Microsoft VS Code Insiders\resources\app\product.json"
    }
    
    # 提示用户选择
    print("请选择要修改的VSCode版本:")
    print("1. VSCode")
    print("2. VSCode Insiders")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    # 验证用户输入
    if choice not in vscode_paths:
        print("无效的选择，请输入 1 或 2")
        return
    
    file_path = vscode_paths[choice]
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 读取JSON文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 检查extensionEnabledApiProposals字段是否存在
    if "extensionEnabledApiProposals" not in data:
        print("找不到 extensionEnabledApiProposals 字段")
        return
    
    # 创建要插入的新元素
    new_entry_key = "Haleclipse.cometix-tab"
    new_entry_value = ["inlineCompletionsAdditions"]
    
    # 获取当前的extensionEnabledApiProposals
    current_proposals = data["extensionEnabledApiProposals"]
    
    # 检查是否已存在该key
    if new_entry_key in current_proposals:
        print(f"警告: {new_entry_key} 已存在于 extensionEnabledApiProposals 中")
        overwrite = input("是否覆盖? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("操作取消")
            return
    
    # 创建新的字典，将新元素放在第一位
    new_proposals = {new_entry_key: new_entry_value}
    # 将原有的其他元素添加进去（排除已存在的同名key）
    for key, value in current_proposals.items():
        if key != new_entry_key:
            new_proposals[key] = value
    
    # 更新数据
    data["extensionEnabledApiProposals"] = new_proposals
    
    # 写回文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent='\t', ensure_ascii=False)
        print(f"✓ 成功修改文件: {file_path}")
        print(f"✓ 已将 '{new_entry_key}' 插入到 extensionEnabledApiProposals 的第一位")
    except Exception as e:
        print(f"写入文件失败: {e}")
        return

if __name__ == "__main__":
    main()
