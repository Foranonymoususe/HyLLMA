# 把已经生成好的json文件中，0直接删掉， 大于1的改为1
import json
import os

# 定义文件夹路径
input_folder = r'/Users/hetianyi/Desktop/flightsim/flightsim_json'  # 原始文件夹路径
output_folder = r'/Users/hetianyi/Desktop/flightsim/flightsim_json_1'  # 保存修改后的文件夹路径

# 检查输出文件夹是否存在，不存在则创建
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 定义处理小数的函数，正整数和负整数保持不变，只保留修改为1的小数，删除修改为0的小数
def modify_numbers(sequence):
    modified_sequence = []
    for num in sequence:
        try:
            num_float = float(num)  # 尝试将数字转换为浮点数
            if '.' in num:  # 仅对小数进行处理
                if num_float > 1:
                    modified_sequence.append(1)  # 保留修改为1的数
                # 忽略小于1的数，相当于删除
            else:
                modified_sequence.append(num)  # 保留整数部分
        except ValueError:
            modified_sequence.append(num)  # 保留非数值的部分
    return modified_sequence

# 遍历输入文件夹中的所有JSON文件
for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, filename)  # 输出文件名与原文件名相同
        
        # 读取JSON文件
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 处理数据
        for entry in data:
            if "completion" in entry:
                sequence = entry["completion"].split(", ")
                modified_sequence = modify_numbers(sequence)
                entry["completion"] = ", ".join(map(str, modified_sequence))

        # 保存修改后的数据到新的文件夹
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"修改后的文件已保存为 {output_file_path}")

print("所有文件已处理完毕。")
