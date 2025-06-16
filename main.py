from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse
import logging
from tqdm import tqdm

from core.file_manager import FileManager
from core.config_manager import ConfigManager
from calculation.openbabel_generator import OpenBabelGenerator
from calculation.xtb_calculator import XTBCalculator

from utils.logging_config import setup_logging
from utils.exceptions import QuantumChemAutomationError, ConfigurationError

logger = logging.getLogger(__name__)


class QuantumChemWorkflow:
    """Main workflow coordinator for quantum chemistry automation"""
    
    def __init__(self, args):
        """Initialize workflow with command line arguments"""
        self.args = args
        self.file_manager = FileManager()
        
        # Initialize coordinate generator if needed
        if hasattr(args, 'force_field'):
            self.coord_generator = OpenBabelGenerator(
                force_field=args.force_field, 
                optimization_steps=args.optimization_steps
            )
        else:
            self.coord_generator = None
        
        # Initialize configuration manager
        self.config_manager = None
        self.xtb_calculator = None
        
        config_path = getattr(args, 'config', None)
        if config_path:
            self.config_manager = ConfigManager(config_path)
            if self.config_manager.has_xtb_config():
                xtb_config = self.config_manager.get_xtb_config()
                self.xtb_calculator = XTBCalculator(
                    xtb_config, 
                    max_workers=getattr(args, 'max_workers', None)
                )
        
    def run_coordinate_generation(self, smi_filename: str, tag: str, 
                                optimize: bool = True) -> Path:
        """
        Execute coordinate generation workflow from SMILES file
        
        Args:
            smi_filename: Name of the .smi file in input_files directory
            tag: Tag for output directory naming
            optimize: Whether to perform force field optimization
            
        Returns:
            Path to output directory containing generated XYZ files
        """
        logger.info(f"Initiating coordinate generation workflow for {smi_filename}")
        
        if not self.coord_generator:
            raise QuantumChemAutomationError("Coordinate generator not initialized")
        
        try:
            # Read SMILES from input file
            smiles_list = self.file_manager.read_smi_file(smi_filename)
            logger.info(f"Loaded {len(smiles_list)} SMILES from {smi_filename}")
            
            # Create output directory for coordinate generation
            output_dir = self.file_manager.create_output_directory(smi_filename, tag)
            
            # Generate coordinates for each SMILES entry
            for i, smiles in enumerate(tqdm(smiles_list, desc="Generating coordinates")):
                molecule_name = f"molecule_{i+1}"
                
                # Generate 3D coordinates using OpenBabel
                xyz_content = self.coord_generator.generate_coordinates(
                    smiles, molecule_name, optimize
                )
                
                # Save XYZ file to output directory
                xyz_path = output_dir / f"{molecule_name}.xyz"
                self.coord_generator.save_xyz_file(xyz_content, xyz_path)
            
            logger.info(f"Coordinate generation completed successfully. Output directory: {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"Coordinate generation workflow failed: {str(e)}")
            raise QuantumChemAutomationError(f"Coordinate generation failed: {str(e)}")
    
    def run_xtb_calculation(self, xyz_source: str, source_type: str = "auto") -> Path:
        """
        Execute XTB calculation workflow
        
        Args:
            xyz_source: Either SMI filename or path to XYZ directory
            source_type: Type of source - 'smi', 'xyz_dir', or 'auto'
            
        Returns:
            Path to XTB output directory
        """
        if not self.xtb_calculator:
            raise QuantumChemAutomationError("XTB calculator not initialized. Configuration file required.")
        
        # Determine source type automatically if not specified
        if source_type == "auto":
            if xyz_source.endswith('.smi'):
                source_type = "smi"
            elif Path(xyz_source).is_dir():
                source_type = "xyz_dir"
            else:
                raise ValueError(f"Cannot determine source type for: {xyz_source}")
        
        logger.info(f"Starting XTB calculation workflow. Source: {xyz_source}, Type: {source_type}")
        
        try:
            # Obtain XYZ files based on source type
            if source_type == "smi":
                xyz_files = self._process_smi_for_xtb(xyz_source)
                source_identifier = xyz_source
            elif source_type == "xyz_dir":
                xyz_files = self._process_xyz_directory(xyz_source)
                source_identifier = Path(xyz_source).name
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            # Create XTB output directory
            xtb_output_dir = self.file_manager.create_xtb_output_directory(source_identifier)
            
            # Execute XTB calculations
            results = self.xtb_calculator.calculate_batch(xyz_files, xtb_output_dir)
            
            logger.info(f"XTB calculation workflow completed. Results: {results['success']}/{results['total']} successful")
            
            # Convert XYZ files if requested
            if self.args.out_xyz:
                save_dir = xtb_output_dir.parent / f"{xtb_output_dir.name}_xyz"
                save_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Converting XYZ files to {save_dir}")
                # Process each XYZ file in the output directory
                for xyz_file in [child for child in xtb_output_dir.iterdir() if child.is_dir()]:
                    name = list(xyz_file.glob('molecule_*.xyz'))[0]
                    if (xyz_file / 'xtbopt.xyz').exists():
                        with open(xyz_file / 'xtbopt.xyz', 'r') as f:
                            coord_lines = f.readlines()[2:]
                        with open(name, 'r') as f:
                            title_lines = f.readlines()[:2]
                        
                        with open(save_dir / f"{name.stem}.xyz", 'w') as f:
                            f.writelines(title_lines + coord_lines)                    
                    
                logger.info(f"Converted XYZ files saved to {xtb_output_dir}")
            return xtb_output_dir
            
        except Exception as e:
            logger.error(f"XTB calculation workflow failed: {str(e)}")
            raise QuantumChemAutomationError(f"XTB calculation failed: {str(e)}")
    
    def _process_smi_for_xtb(self, smi_filename: str) -> List[Path]:
        """
        Process SMI file to generate XYZ files for XTB calculation
        
        Args:
            smi_filename: Name of SMI file
            
        Returns:
            List of generated XYZ file paths
        """
        if not self.coord_generator:
            raise QuantumChemAutomationError("Coordinate generator required for SMI processing")
        
        # Generate coordinates first
        coord_output_dir = self.run_coordinate_generation(
            smi_filename, 
            "coords_for_xtb", 
            not self.args.no_optimize
        )
        
        # Return list of generated XYZ files
        return self.file_manager.list_xyz_files(coord_output_dir)
    
    def _process_xyz_directory(self, xyz_dir_path: str) -> List[Path]:
        """
        Process directory containing XYZ files for XTB calculation
        
        Args:
            xyz_dir_path: Path to directory containing XYZ files
            
        Returns:
            List of XYZ file paths
        """
        # Validate directory and find XYZ files
        validated_dir = self.file_manager.validate_xyz_directory(xyz_dir_path)
        return self.file_manager.list_xyz_files(validated_dir)
    
    def run_combined_workflow(self, smi_filename: str) -> Path:
        """
        Execute combined workflow: SMILES to coordinates to XTB calculation
        
        Args:
            smi_filename: Name of SMI file
            
        Returns:
            Path to final XTB output directory
        """
        logger.info(f"Starting combined SMILES-to-XTB workflow for {smi_filename}")
        
        if not self.coord_generator or not self.xtb_calculator:
            raise QuantumChemAutomationError("Both coordinate generator and XTB calculator required for combined workflow")
        
        # Execute XTB calculation workflow with SMI source
        return self.run_xtb_calculation(smi_filename, "smi")


def create_sample_config_if_needed(config_path: Path) -> None:
    """Create sample configuration file if it doesn't exist"""
    if not config_path.exists():
        logger.info(f"Configuration file not found. Creating sample at {config_path}")
        ConfigManager.create_sample_config(config_path)
        logger.info("Please edit the configuration file and run again.")
        return True
    return False


def main():
    """Main entry point for quantum chemistry automation"""
    parser = argparse.ArgumentParser(
        description="Quantum Chemistry Automation with SMILES-to-XYZ and XTB calculation support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate coordinates only
  python main.py coords input.smi --tag my_molecules
  
  # Run XTB calculations on SMI file (requires config.yaml)
  python main.py xtb input.smi --config config.yaml
  
  # Run XTB calculations on XYZ directory
  python main.py xtb /path/to/xyz/files --config config.yaml
  
  # Combined workflow (SMI -> XYZ -> XTB)
  python main.py combined input.smi --config config.yaml
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Coordinate generation command
    coords_parser = subparsers.add_parser('coords', help='Generate 3D coordinates from SMILES')
    coords_parser.add_argument("smi_file", help="SMILES input file name")
    coords_parser.add_argument("--tag", required=True, help="Tag for output directory")
    coords_parser.add_argument("--force-field", default="MMFF94",
                              choices=["MMFF94", "UFF", "GAFF"],
                              help="Force field for optimization")
    coords_parser.add_argument("--optimization-steps", type=int, default=1000,
                              help="Number of optimization steps")
    coords_parser.add_argument("--no-optimize", action="store_true", 
                              help="Skip force field optimization")
    
    # XTB calculation command
    xtb_parser = subparsers.add_parser('xtb', help='Run XTB calculations')
    xtb_parser.add_argument("source", help="SMI file name or XYZ directory path")
    xtb_parser.add_argument("--config", type=Path, required=True, 
                           help="Configuration YAML file")
    xtb_parser.add_argument("--max-workers", type=int, 
                           help="Maximum number of parallel workers")
    xtb_parser.add_argument("--force-field", default="MMFF94",
                           choices=["MMFF94", "UFF", "GAFF"],
                           help="Force field for coordinate generation (if needed)")
    xtb_parser.add_argument("--optimization-steps", type=int, default=1000,
                           help="Number of optimization steps for coordinates")
    xtb_parser.add_argument("--no-optimize", action="store_true", 
                           help="Skip force field optimization for coordinates")
    xtb_parser.add_argument("--out_xyz", action="store_true", 
                           help="Convert xyz file from XTB")
    
    # Combined workflow command
    combined_parser = subparsers.add_parser('combined', help='Run complete SMILES-to-XTB workflow')
    combined_parser.add_argument("smi_file", help="SMILES input file name")
    combined_parser.add_argument("--config", type=Path, required=True, 
                                help="Configuration YAML file")
    combined_parser.add_argument("--max-workers", type=int, 
                                help="Maximum number of parallel workers")
    combined_parser.add_argument("--force-field", default="MMFF94",
                                choices=["MMFF94", "UFF", "GAFF"],
                                help="Force field for coordinate generation")
    combined_parser.add_argument("--optimization-steps", type=int, default=1000,
                                help="Number of optimization steps")
    combined_parser.add_argument("--no-optimize", action="store_true", 
                                help="Skip force field optimization")
    combined_parser.add_argument("--out_xyz", action="store_true", 
                           help="Convert xyz file from XTB")
    
    # Global arguments
    parser.add_argument("--log-level", default="WARNING", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Initialize workflow
        workflow = QuantumChemWorkflow(args)
        
        # Execute based on command
        if args.command == 'coords':
            output_dir = workflow.run_coordinate_generation(
                args.smi_file, args.tag, not args.no_optimize
            )
            logger.info(f"Coordinate generation completed. Output: {output_dir}")
            
        elif args.command == 'xtb':
            # Check if config file exists, create sample if needed
            if create_sample_config_if_needed(args.config):
                return
            
            output_dir = workflow.run_xtb_calculation(args.source)
            logger.info(f"XTB calculation completed. Output: {output_dir}")
            
        elif args.command == 'combined':
            # Check if config file exists, create sample if needed
            if create_sample_config_if_needed(args.config):
                return
            
            output_dir = workflow.run_combined_workflow(args.smi_file)
            logger.info(f"Combined workflow completed. Output: {output_dir}")
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())