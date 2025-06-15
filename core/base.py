"""
Abstract base classes for quantum chemistry automation
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class BaseCoordinateGenerator(ABC):
    """Abstract base class for coordinate generation from SMILES"""
    
    @abstractmethod
    def generate_coordinates(self, smiles: str, molecule_name: str, 
                           optimize: bool = True) -> str:
        """
        Generate 3D coordinates from SMILES string
        
        Args:
            smiles: SMILES representation of molecule
            molecule_name: Name for the molecule
            optimize: Whether to perform force field optimization
            
        Returns:
            XYZ coordinates as string
        """
        pass
    
    @abstractmethod
    def save_xyz_file(self, xyz_content: str, output_path: Path) -> None:
        """Save XYZ content to file"""
        pass


class BaseCalculator(ABC):
    """Abstract base class for quantum chemistry calculations"""
    
    @abstractmethod
    def calculate_batch(self, xyz_files: List[Path], output_dir: Path) -> Dict[str, Any]:
        """
        Perform calculations on batch of XYZ files
        
        Args:
            xyz_files: List of XYZ file paths
            output_dir: Output directory for results
            
        Returns:
            Dictionary with calculation results
        """
        pass
    
    @abstractmethod
    def calculate_single(self, xyz_file: Path, output_dir: Path) -> str:
        """
        Perform calculation on single XYZ file
        
        Args:
            xyz_file: XYZ file path
            output_dir: Output directory for results
            
        Returns:
            Result message
        """
        pass


class BaseInputGenerator(ABC):
    """Abstract base class for quantum chemistry input file generation"""
    
    @abstractmethod
    def generate_input(self, xyz_file: Path, config: Dict[str, Any]) -> str:
        """
        Generate input file content from XYZ coordinates
        
        Args:
            xyz_file: Path to XYZ coordinate file
            config: Configuration parameters
            
        Returns:
            Input file content as string
        """
        pass
    
    @abstractmethod
    def save_input_file(self, content: str, output_path: Path) -> None:
        """Save input file content to disk"""
        pass
    