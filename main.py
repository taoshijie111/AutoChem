from pathlib import Path
from typing import Optional, Dict, Any
import argparse
import logging
from tqdm import tqdm

from core.file_manager import FileManager
from coordinate_generation.openbabel_generator import OpenBabelGenerator

from utils.logging_config import setup_logging
from utils.exceptions import QuantumChemAutomationError

logger = logging.getLogger(__name__)

class QuantumChemWorkflow:
    """Main workflow coordinator"""
    
    def __init__(self, args):
        self.file_manager = FileManager()
        self.coord_generator = OpenBabelGenerator(force_field=args.force_field, optimization_steps=args.optimization_steps)
        
    def run_coordinate_generation(self, smi_filename: str, tag: str, 
                                optimize: bool = True) -> Path:
        """
        Run coordinate generation workflow
        
        Args:
            smi_filename: Name of the .smi file in input_files
            tag: Tag for output directory naming
            optimize: Whether to perform force field optimization
            
        Returns:
            Path to output directory containing XYZ files
        """
        logger.info(f"Starting coordinate generation for {smi_filename}")
        
        try:
            # Read SMILES from file
            smiles_list = self.file_manager.read_smi_file(smi_filename)
            
            # Create output directory
            output_dir = self.file_manager.create_output_directory(smi_filename, tag)
            
            # Generate coordinates for each SMILES
            for i, smiles in enumerate(tqdm(smiles_list)):
                molecule_name = f"molecule_{i+1}"
                
                # Generate 3D coordinates
                xyz_content = self.coord_generator.generate_coordinates(
                    smiles, molecule_name, optimize
                )
                
                # Save XYZ file
                xyz_path = output_dir / f"{molecule_name}.xyz"
                self.coord_generator.save_xyz_file(xyz_content, xyz_path)
            
            logger.info(f"Coordinate generation completed. Output: {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"Coordinate generation failed: {str(e)}")
            raise QuantumChemAutomationError(f"Coordinate generation failed: {str(e)}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quantum Chemistry Automation")
    parser.add_argument("smi_file", help="SMILES input file name")
    parser.add_argument("--tag", required=True, help="Tag for output directory")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    
    # MMFF
    parser.add_argument("--force-field", default="MMFF94",
                       choices=["MMFF94", "UFF", "GAFF"],
                       help="Force field to use for optimization")
    parser.add_argument("--optimization-steps", type=int, default=1000,
                       help="Number of optimization steps for force field")
    parser.add_argument("--no-optimize", action="store_true", 
                       help="Skip force field optimization")
    parser.add_argument("--coords-only", action="store_true",
                       help="Generate coordinates only (skip input files)")
    
    
    parser.add_argument("--log-level", default="WARNING", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    
    workflow = QuantumChemWorkflow()
    
    output_dir = workflow.run_coordinate_generation(
                args.smi_file, args.tag, not args.no_optimize
            )
    