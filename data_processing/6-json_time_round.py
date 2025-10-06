import json
import os


input_folder = r'' 
output_folder = r''  

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def modify_numbers(sequence):
    modified_sequence = []
    for num in sequence:
        try:
            num_float = float(num)  
            if '.' in num: 
                if num_float > 1:
                    modified_sequence.append(1)
            else:
                modified_sequence.append(num)  
        except ValueError:
            modified_sequence.append(num)  
    return modified_sequence


for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, filename)  
        

        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        

        for entry in data:
            if "completion" in entry:
                sequence = entry["completion"].split(", ")
                modified_sequence = modify_numbers(sequence)
                entry["completion"] = ", ".join(map(str, modified_sequence))

       
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)


