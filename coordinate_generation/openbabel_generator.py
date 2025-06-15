"""
OpenBabel-based coordinate generation
"""
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import subprocess
import tempfile
import logging
import os
import re
from datetime import datetime
from tqdm import tqdm

from core.base import BaseCoordinateGenerator
from utils.exceptions import CoordinateGenerationError

logger = logging.getLogger('OpenBabel Coordinate Generation')


class OpenBabelGenerator(BaseCoordinateGenerator):
    """Coordinate generator using OpenBabel"""
    
    def __init__(self, force_field: str = "MMFF94", optimization_steps: int = 1000, 
                 error_log_path: Optional[Path] = None):
        self.force_field = force_field
        self.optimization_steps = optimization_steps
        self.error_log_path = error_log_path or Path("error.log")
        self._initialize_error_log()
    
    def _initialize_error_log(self) -> None:
        """Initialize error log file with header information"""
        try:
            with open(self.error_log_path, 'w') as f:
                f.write("# Error Log for SMILES Coordinate Generation\n")
                f.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Format: TIMESTAMP | SMILES | MOLECULE_NAME | ERROR_MESSAGE\n")
                f.write("# " + "="*80 + "\n\n")
        except Exception as e:
            logger.warning(f"Failed to initialize error log {self.error_log_path}: {e}")
    
    def _log_failed_smiles(self, smiles: str, molecule_name: str, error_message: str) -> None:
        """
        Log failed SMILES generation to error log file
        
        Args:
            smiles: The SMILES string that failed
            molecule_name: Name of the molecule
            error_message: Description of the error
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} | {smiles} | {molecule_name} | {error_message}\n"
            
            with open(self.error_log_path, 'a') as f:
                f.write(log_entry)
                
            logger.debug(f"Logged failed SMILES to {self.error_log_path}: {molecule_name}")
            
        except Exception as e:
            logger.warning(f"Failed to write to error log {self.error_log_path}: {e}")
    
    def run_command(self, command: str) -> Tuple[Optional[str], Optional[str], int]:
        """
        Run a shell command and return its output.

        Args:
            command: Command to run

        Returns:
            tuple: (stdout, stderr, return_code)
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            return stdout, stderr, process.returncode
        except Exception as e:
            logger.error(f"Error running command '{command}': {e}")
            return None, str(e), 1
        
    def extract_formula(self, xyz_file: Path) -> str:
        """
        Extract chemical formula from XYZ file by directly parsing atomic symbols.

        Args:
            xyz_file: Path to XYZ file

        Returns:
            Chemical formula in standard format (e.g., C6H12O6)
        """
        try:
            with open(xyz_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 3:  # Must have at least header, comment, and one atom line
                return "Unknown"
            
            # Parse atom count from first line
            try:
                atom_count = int(lines[0].strip())
            except ValueError:
                return "Unknown"
            
            # Count elements from coordinate lines (skip first two lines)
            element_counts = {}
            coordinate_lines = lines[2:2+atom_count]  # Ensure we don't read beyond expected atoms
            
            for line in coordinate_lines:
                parts = line.strip().split()
                if len(parts) >= 4:  # Element symbol + 3 coordinates
                    element = parts[0].strip()
                    # Handle cases where element might have numbers (unlikely in XYZ but defensive)
                    element = re.sub(r'\d+', '', element)
                    element_counts[element] = element_counts.get(element, 0) + 1
            
            if not element_counts:
                return "Unknown"
            
            # Format formula in standard order: C, H, then alphabetical
            formula_parts = []
            
            # Add carbon first if present
            if 'C' in element_counts:
                count = element_counts['C']
                formula_parts.append('C' if count == 1 else f'C{count}')
                del element_counts['C']
            
            # Add hydrogen second if present
            if 'H' in element_counts:
                count = element_counts['H']
                formula_parts.append('H' if count == 1 else f'H{count}')
                del element_counts['H']
            
            # Add remaining elements in alphabetical order
            for element in sorted(element_counts.keys()):
                count = element_counts[element]
                formula_parts.append(element if count == 1 else f'{element}{count}')
            
            return ''.join(formula_parts)
            
        except Exception as e:
            logger.warning(f"Failed to extract formula from {xyz_file}: {e}")
            return "Unknown"
    
    
    
    def generate_coordinates(self, smiles: str, molecule_name: str, 
                           optimize: bool = True, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate 3D coordinates from SMILES using OpenBabel
        
        Args:
            smiles: SMILES string
            molecule_name: Name for the molecule
            optimize: Whether to perform force field optimization
            parameters: Additional parameters for coordinate generation
                - ff (str): Force field to use
                - steps (int): Number of optimization steps
        
        Returns:
            XYZ coordinates as string with enhanced metadata
        """
        # Handle parameters
        if parameters is None:
            parameters = {}
        
        force_field = parameters.get('ff', self.force_field)
        steps = parameters.get('steps', self.optimization_steps)
        
        try:
            # Create temporary file for SMILES string
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.smi', delete=False) as temp_smi:
                temp_smi.write(smiles)
                temp_smi_path = temp_smi.name
            
            # Create temporary file for XYZ output
            temp_xyz_fd, temp_xyz_path = tempfile.mkstemp(suffix='.xyz')
            os.close(temp_xyz_fd)  # Close file descriptor immediately
            
            # Build OpenBabel command
            if optimize:
                command = (
                    f"obabel {temp_smi_path} -O {temp_xyz_path} --gen3d --minimize "
                    f"--steps {steps} --ff {force_field} --addtotitle 'SMILES: {smiles}'"
                )
            else:
                command = (
                    f"obabel {temp_smi_path} -O {temp_xyz_path} --gen3d "
                    f"--addtotitle 'SMILES: {smiles}'"
                )
            
            # Execute command
            stdout, stderr, return_code = self.run_command(command)
            
            # Clean up temporary SMILES file
            if os.path.exists(temp_smi_path):
                os.unlink(temp_smi_path)
            
            if return_code != 0:
                error_msg = f"OpenBabel command failed for {molecule_name}: {stderr}"
                logger.error(error_msg)
                self._log_failed_smiles(smiles, molecule_name, error_msg)
                raise CoordinateGenerationError(error_msg)
            
            # Check if output file was created
            if not os.path.exists(temp_xyz_path):
                error_msg = f"Output file {temp_xyz_path} not created for {molecule_name}"
                logger.error(error_msg)
                self._log_failed_smiles(smiles, molecule_name, error_msg)
                raise CoordinateGenerationError(error_msg)
            
            # Read and enhance XYZ content with metadata
            xyz_content = self._enhance_xyz_with_metadata(temp_xyz_path, smiles, molecule_name)
            
            # Clean up temporary XYZ file
            if os.path.exists(temp_xyz_path):
                os.unlink(temp_xyz_path)
            
            logger.info(f"Generated coordinates for {molecule_name}, optimized: {optimize}, "
                       f"force field: {force_field}, steps: {steps}")
            return xyz_content
            
        except CoordinateGenerationError:
            # Re-raise coordinate generation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error generating coordinates for {molecule_name}: {str(e)}"
            logger.error(error_msg)
            self._log_failed_smiles(smiles, molecule_name, error_msg)
            raise CoordinateGenerationError(error_msg)
    
    def _enhance_xyz_with_metadata(self, xyz_file_path: str, smiles: str, molecule_name: str) -> str:
        """
        Enhance XYZ file with metadata in comment line
        
        Args:
            xyz_file_path: Path to temporary XYZ file
            smiles: Original SMILES string
            molecule_name: Molecule name
            
        Returns:
            Enhanced XYZ content as string
        """
        try:
            # Read XYZ file content
            with open(xyz_file_path, 'r') as f:
                xyz_lines = f.readlines()
            
            if len(xyz_lines) < 2:
                logger.warning(f"Invalid XYZ file format for {molecule_name}")
                return ''.join(xyz_lines)
            
            # Extract chemical formula
            formula = self.extract_formula(Path(xyz_file_path))
            
            # Create enhanced comment line with metadata
            comment = f"{molecule_name} - SMILES: {smiles} - Formula: {formula}"
            xyz_lines[1] = comment + '\n'
            
            return ''.join(xyz_lines)
            
        except Exception as e:
            logger.warning(f"Failed to enhance XYZ metadata for {molecule_name}: {e}")
            # Return original content if enhancement fails
            with open(xyz_file_path, 'r') as f:
                return f.read()
                    
    def save_xyz_file(self, xyz_content: str, output_path: Path) -> None:
        """Save XYZ content to file with proper directory creation"""
        try:
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write XYZ content
            with open(output_path, 'w') as f:
                f.write(xyz_content)
                
            logger.info(f"Saved XYZ file: {output_path}")
            
        except Exception as e:
            error_msg = f"Failed to save XYZ file {output_path}: {str(e)}"
            logger.error(error_msg)
            raise CoordinateGenerationError(error_msg)
        
    def batch_generate_coordinates(self, smiles_list: list, molecule_names: list,
                                 optimize: bool = True, 
                                 parameters: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Generate coordinates for multiple SMILES strings
        
        Args:
            smiles_list: List of SMILES strings
            molecule_names: List of molecule names
            optimize: Whether to perform force field optimization
            parameters: Additional parameters for coordinate generation
            
        Returns:
            Dictionary mapping molecule names to XYZ content
        """
        if len(smiles_list) != len(molecule_names):
            raise ValueError("SMILES list and molecule names list must have the same length")
        
        results = {}
        failed_molecules = []
        
        for smiles, name in tqdm(zip(smiles_list, molecule_names)):
            try:
                xyz_content = self.generate_coordinates(smiles, name, optimize, parameters)
                results[name] = xyz_content
            except CoordinateGenerationError as e:
                logger.error(f"Failed to generate coordinates for {name}: {e}")
                failed_molecules.append(name)
                # Error logging is already handled in generate_coordinates method
                continue
        
        success_count = len(results)
        total_count = len(smiles_list)
        failure_count = len(failed_molecules)
        
        if failed_molecules:
            logger.warning(f"Failed to generate coordinates for {failure_count} molecules. "
                          f"Check {self.error_log_path} for detailed error information.")
        
        logger.info(f"Batch coordinate generation completed: {success_count}/{total_count} successful. "
                   f"Failed molecules logged to {self.error_log_path}")
        
        return results