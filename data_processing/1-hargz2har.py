import os
import gzip
import shutil

def convert_and_delete_gz(directory):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return
 
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.har.gz'):
                gz_path = os.path.join(dirpath, filename)
                har_path = os.path.join(dirpath, filename[:-3])  

                with gzip.open(gz_path, 'rb') as f_in, open(har_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                

                os.remove(gz_path)

                print(f"Converted {gz_path} to {har_path} and deleted {gz_path}")


convert_and_delete_gz(r'')

