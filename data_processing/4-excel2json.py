import pandas as pd
import json
import os

excel_folder = r''
json_file_path = r''



all_files_data = []

for file_index, file_name in enumerate(os.listdir(excel_folder)):
    if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
        file_path = os.path.join(excel_folder, file_name)
        df = pd.read_excel(file_path)
        
        
        all_columns_data = []
        
        
        for col in df.columns[2:]:
            
            for row_index in [0, 1]:
                value = df.at[row_index, col]
                if pd.notna(value):
                    all_columns_data.append(str(int(value)))  

            
            value = df.at[2, col]
            if pd.notna(value):
                    rounded_value = round(float(value), 3)  
                    all_columns_data.append(str(rounded_value))


        text = ", ".join(all_columns_data)
        
        all_files_data.append({
            "input": f"<<SYS>>\nNetwork traffic metadata of www.youtube.com\n<</SYS>>",
            "completion": text
        })


json_data = json.dumps(all_files_data, indent=4, ensure_ascii=False)


with open(json_file_path, 'w', encoding='utf-8') as f:
    f.write(json_data)



