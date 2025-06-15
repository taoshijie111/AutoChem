from pathlib import Path
from datetime import datetime
from typing import List, Union
import shutil
import logging

logger = logging.getLogger('File Manager')


class FileManager:
    """Handles file operations and directory management"""
    
    def __init__(self, base_input_dir: str = ".", 
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
    
    def create_xtb_output_directory(self, source_identifier: str) -> Path:
        """
        Create XTB-specific output directory with naming convention:
        xtb_source_identifier_date
        
        Args:
            source_identifier: Either SMI filename or directory basename
            
        Returns:
            Path to XTB output directory
        """
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_identifier).stem
        dir_name = f"xtb_{source_name}_{date_str}"
        
        output_dir = self.base_output_dir / dir_name
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Created XTB output directory: {output_dir}")
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
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        xyz_files = list(directory.glob("*.xyz"))
        logger.info(f"Found {len(xyz_files)} XYZ files in {directory}")
        return xyz_files
    
    def find_xyz_files_recursive(self, directory: Path) -> List[Path]:
        """
        Recursively find all XYZ files in directory and subdirectories
        
        Args:
            directory: Root directory to search
            
        Returns:
            List of XYZ file paths
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        xyz_files = list(directory.rglob("*.xyz"))
        logger.info(f"Found {len(xyz_files)} XYZ files recursively in {directory}")
        return xyz_files
    
    def validate_xyz_directory(self, directory_path: Union[str, Path]) -> Path:
        """
        Validate that the provided path is a directory containing XYZ files
        
        Args:
            directory_path: Path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If directory contains no XYZ files
        """
        path = Path(directory_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        xyz_files = self.list_xyz_files(path)
        if not xyz_files:
            raise ValueError(f"No XYZ files found in directory: {path}")
        
        return path
    
    def copy_xyz_files_to_output(self, xyz_files: List[Path], output_dir: Path) -> List[Path]:
        """
        Copy XYZ files to output directory
        
        Args:
            xyz_files: List of source XYZ files
            output_dir: Destination directory
            
        Returns:
            List of copied file paths
        """
        copied_files = []
        
        for xyz_file in xyz_files:
            dest_file = output_dir / xyz_file.name
            shutil.copy2(xyz_file, dest_file)
            copied_files.append(dest_file)
        
        logger.info(f"Copied {len(copied_files)} XYZ files to {output_dir}")
        return copied_files
    