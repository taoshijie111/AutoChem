import re
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path    
from tqdm import tqdm


def gaussian_broadening(frequencies, intensities, width, output_range):
    """
    Apply Gaussian broadening to spectral data.
    
    Parameters:
    -----------
    frequencies : array-like
        Peak frequencies in eV
    intensities : array-like  
        Peak intensities (oscillator strengths)
    width : float
        Gaussian width (FWHM) in eV
    output_range : array-like
        Energy range for output spectrum in eV
        
    Returns:
    --------
    broadened_spectrum : numpy.ndarray
        Broadened spectrum values at output_range energies
        
    Notes:
    ------
    The function is normalized such that a unit oscillator strength produces
    a broadened curve with an area of 28700 when eV is used as the x-axis unit.
    This follows the standard convention in electronic spectroscopy.
    """
    
    # Convert arrays to numpy arrays for consistency
    frequencies = np.asarray(frequencies)
    intensities = np.asarray(intensities)
    output_range = np.asarray(output_range)
    
    # Validate input dimensions
    if len(frequencies) != len(intensities):
        raise ValueError("frequencies and intensities must have the same length")
    
    # Convert FWHM to standard deviation
    # FWHM = 2 * sqrt(2 * ln(2)) * σ ≈ 2.355 * σ
    sigma = width / (2 * np.sqrt(2 * np.log(2)))
    
    # Initialize output spectrum
    broadened_spectrum = np.zeros_like(output_range, dtype=float)
    
    # Calculate normalization factor
    # For unit oscillator strength, area should be 28700
    # Area of Gaussian = A * σ * sqrt(2π), so A = 28700 / (σ * sqrt(2π))
    # normalization = 28700 / (sigma * np.sqrt(2 * np.pi))
    
    # For each peak, add its Gaussian contribution
    for freq, intensity in zip(frequencies, intensities):
        # Calculate Gaussian for this peak
        gaussian = np.exp(-0.5 * ((output_range - freq) / sigma)**2)
        
        # Add this peak's contribution to the spectrum
        broadened_spectrum += intensity * gaussian #  * normalization
    
    return broadened_spectrum


def extract_data_from_std2(file_path):
    """
    Extracts data from a .std2 file and returns it as a list of dictionaries.
    
    Args:
        file_path (str): The path to the .std2 file.
        
    Returns:
        list: A list of dictionaries containing the extracted data.
    """
    energy, intensity = [], []
    extract = False
    with open(file_path, 'r') as file:
        for line in file:
            if 'DATXY' in line:
                extract = True
                continue
            if extract:
                if line.strip():  # Skip empty lines
                    parts = line.split()
                    energy.append(float(parts[1]))
                    intensity.append(float(parts[2]))
    return {'energy': energy, 'intensity': intensity}



def read_smiles(file_path):
    with open(file_path, 'r') as file:
        smiles_list = [line.strip() for line in file if line.strip()]
    print(f'Read {len(smiles_list)} SMILES from {file_path}')
    return smiles_list


def get_sorted_numeric_dirs(root_path):
    dir_list = [item for item in root_path.iterdir() if item.is_dir()]
    
    numeric_dirs = []
    for dir_path in dir_list:
        try:
            num = int(dir_path.name) 
            numeric_dirs.append((num, dir_path))
        except ValueError:
            continue  
    
    numeric_dirs.sort(key=lambda x: x[0])
    
    sorted_dirs = [item[1] for item in numeric_dirs]
    
    return sorted_dirs


def process_spectral_data(root, smiles_list, save_path=None):
    root = Path(root)
    
    # 获取所有job目录
    job_dirs = []
    for item in root.iterdir():
        if item.is_dir():
            match = re.fullmatch(r"job(\d+)", item.name)
            if match:
                num = int(match.group(1))  # 提取数字并转为整数用于排序
                job_dirs.append((num, item))
                
    job_dirs.sort(key=lambda x: x[0])
    job_dirs = [item[1] for item in job_dirs]
    
    global_idx = 0
    success_count = 0
    all_broadening_data = {}
    all_raw_data = {}
    for folder in job_dirs:
        # 处理每个Job目录
        file_path_list = get_sorted_numeric_dirs(folder)
        for file_path in tqdm(file_path_list, desc=f'Processing {folder.name}', leave=False):
            file_path = file_path /  'tda.dat'
            smi = smiles_list[global_idx]
            global_idx += 1
            
            if file_path.exists():
                data = extract_data_from_std2(file_path)
                if data['energy'] and data['intensity']:
                    # 进行高斯展宽处理
                    result = gaussian_broadening(data['energy'], data['intensity'], 0.003, np.linspace(0, 13.5, 4000))
                    # 整理数据
                    all_raw_data[smi] = result
                    all_broadening_data[smi] = result
                    success_count += 1
    
    print(f'Processed {success_count} spectra out of {global_idx} total SMILES.')        
    if save_path:
        save_path = Path(save_path)
        with open(save_path / 'uv_broadening_data.pkl', 'wb') as f:
            pickle.dump(all_broadening_data, f)
        with open(save_path / 'uv_raw_data.pkl', 'wb') as f:
            pickle.dump(all_raw_data, f)
            
if __name__ == '__main__':
    smiles_list = read_smiles('rxndb_small.smi')
    process_spectral_data('/home/user/data/uspto_xtb/uv/small', smiles_list, save_path='.')
    
