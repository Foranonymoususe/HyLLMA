#excel数据转化为json文件，加上sys
import pandas as pd
import json
import os

# 文件夹路径
excel_folder = r'/Users/hetianyi/Desktop/flightsim/flightsim_excel/scan'
json_file_path = r'/Users/hetianyi/Desktop//flightsim//flightsim_json/flightsim_scan_test.json'



# 初始化一个列表来存储所有文件的数据
all_files_data = []

# 遍历Excel文件夹中的所有文件
for file_index, file_name in enumerate(os.listdir(excel_folder)):
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        file_path = os.path.join(excel_folder, file_name)
        df = pd.read_excel(file_path)
        
        # 初始化一个空列表来存储单个文件的数据
        all_columns_data = []
        
        # 按列遍历数据，忽略第一列和第二列
        for col in df.columns[2:]:
            # 处理Positive_Size_Direction和Negative_Size_Direction行
            for row_index in [0, 1]:
                value = df.at[row_index, col]
                if pd.notna(value):
                    all_columns_data.append(str(int(value)))  # 转换为整数形式

            # 处理Interval行
            # value = df.at[2, col]
            # if pd.notna(value):
            #     all_columns_data.append(str(value))  # 保留小数形式
            # 处理Interval行
            value = df.at[2, col]
            if pd.notna(value):
                    rounded_value = round(float(value), 3)  # 四舍五入保留三位小数
                    all_columns_data.append(str(rounded_value))


        # 将所有列的数据合并为一个字符串，并用逗号分隔
        text = ", ".join(all_columns_data)
        
        # 添加到格式化数据列表中
        all_files_data.append({
            "input": f"<<SYS>>\nNetwork traffic metadata of www.youtube.com\n<</SYS>>",
            "completion": text
        })

# 将字典列表转换为JSON字符串
json_data = json.dumps(all_files_data, indent=4, ensure_ascii=False)

# 将JSON字符串保存到文件中
with open(json_file_path, 'w', encoding='utf-8') as f:
    f.write(json_data)

print(f"JSON数据已保存到: {json_file_path}")





# import pandas as pd
# import json
# import os

# # 文件夹路径
# excel_base_folder = '/Users/hetianyi/Desktop/malware_excel/mal_lastline_crypt/train'
# json_output_base_folder = '/Users/hetianyi/Desktop/malware_raw_json'

# # 创建保存 JSON 文件的文件夹
# os.makedirs(json_output_base_folder, exist_ok=True)

# # 遍历Excel文件夹中的每个子文件夹
# for folder_index, folder_name in enumerate(os.listdir(excel_base_folder)):
#     folder_path = os.path.join(excel_base_folder, folder_name)
#     if os.path.isdir(folder_path):
#         # 初始化一个列表来存储该文件夹中所有文件的数据
#         all_files_data = []
        
#         # 遍历子文件夹中的所有Excel文件
#         for file_index, file_name in enumerate(os.listdir(folder_path)):
#             if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
#                 file_path = os.path.join(folder_path, file_name)
#                 df = pd.read_excel(file_path)
                
#                 # 初始化一个空列表来存储单个文件的数据
#                 all_columns_data = []
                
#                 # 按列遍历数据，忽略第一列和第二列
#                 for col in df.columns[2:]:
#                     # 处理Positive_Size_Direction和Negative_Size_Direction行
#                     for row_index in [0, 1]:
#                         value = df.at[row_index, col]
#                         if pd.notna(value):
#                             all_columns_data.append(str(int(value)))  # 转换为整数形式

#                     # 处理Interval行
#                     value = df.at[2, col]
#                     if pd.notna(value):
#                         all_columns_data.append(str(value))  # 保留小数形式

#                 # 将所有列的数据合并为一个字符串，并用逗号分隔
#                 text = ", ".join(all_columns_data)
                
#                 # 添加到格式化数据列表中
#                 all_files_data.append({
#                     "input": f"<<SYS>>\nNetwork traffic metadata of {folder_name}\n<</SYS>>",
#                     "completion": text
#                 })

#         # 创建 JSON 文件路径
#         json_file_path = os.path.join(json_output_base_folder, f'{folder_name}.json')
        
#         # 将字典列表转换为JSON字符串
#         json_data = json.dumps(all_files_data, indent=4, ensure_ascii=False)
        
#         # 将JSON字符串保存到文件中
#         with open(json_file_path, 'w', encoding='utf-8') as f:
#             f.write(json_data)

#         print(f"JSON数据已保存到: {json_file_path}")