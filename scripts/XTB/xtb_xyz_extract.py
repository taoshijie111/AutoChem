import os
import numpy as np
import pandas as pd

def read_xyz(file_path):
    atoms = []
    coordinates = []
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        
        for i, line in enumerate(lines):
            if i > 1:  
                atom_info = line.split()
                if len(atom_info) == 4: 
                    atoms.append(atom_info[0])  
                    try:
                        coord = list(map(float, atom_info[1:]))
                        coordinates.append(coord)
                    except ValueError:
                        print(f"Error reading coordinates at line {i+1} in the file.")
                        return None, None
    return atoms, np.array(coordinates)


def find_and_extract_xyz_data(root_directory, file_name='xtbopt.xyz'):
    found_files = 0
    successful_extractions = 0
    data_list = []
    for root, dirs, files in os.walk(root_directory):
        if file_name in files:
            found_files += 1
            xyz_path = os.path.join(root, file_name)
            
            parent_dir_name = os.path.basename(root)
            print(f"处理文件: {xyz_path}")
            atoms, coordinates = read_xyz(xyz_path)
            
            if atoms is not None and coordinates is not None:
                data_list.append({
                    'name': parent_dir_name,
                    'atoms': atoms,
                    'coordinates': coordinates
                })
                successful_extractions += 1
                
    print(f"找到 {file_name} 文件: {found_files} 个")
    print(f"成功提取完整数据: {successful_extractions} 个")
    print(f"总数据条目: {len(data_list)} 个")
    
    if not data_list:
        return pd.DataFrame(columns=['name', 'atoms', 'coordinates'])
    
    df = pd.DataFrame(data_list)
    df = df.sort_values('name').reset_index(drop=True)
    
    return df
    
    
if __name__ == '__main__':
    xyz_data = find_and_extract_xyz_data('/home/user/data/AutoChem/output_files/xtb_OSC_20250627_093955', file_name='xtbopt.xyz')
    xyz_data.to_csv('./xyz_data.csv')