from pathlib import Path
from datetime import datetime
from typing import List
import shutil


class FileManager:
    """Handles file operations and directory management"""
    
    def __init__(self, base_input_dir: str = "input_files", 
                 base_output_dir: str = "output_files"):
        self.base_input_dir = Path(base_input_dir)
        self.base_output_dir = Path(base_output_dir)
        self.ensure_directories()
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.base_input_dir.mkdir(exist_ok=True)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def create_output_directory(self, smi_filename: str, tag: str) -> Path:
        """
        Create output directory with naming convention:
        smi_filename + execution_date + tag
        """
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        smi_name = Path(smi_filename).stem
        dir_name = f"{smi_name}_{date_str}_{tag}"
        
        output_dir = self.base_output_dir / dir_name
        output_dir.mkdir(exist_ok=True)
        return output_dir
    
    def read_smi_file(self, smi_filename: str) -> List[str]:
        """Read SMILES from .smi file"""
        smi_path = self.base_input_dir / smi_filename
        
        if not smi_path.exists():
            raise FileNotFoundError(f"SMI file not found: {smi_path}")
        
        with open(smi_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def list_xyz_files(self, directory: Path) -> List[Path]:
        """List all XYZ files in a directory"""
        return list(directory.glob("*.xyz"))