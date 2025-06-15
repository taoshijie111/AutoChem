"""
XTB calculation module for quantum chemistry automation
"""
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from multiprocessing import Pool, cpu_count
import shutil
import logging
from tqdm import tqdm

from core.base import BaseCalculator
from utils.exceptions import CalculationError

logger = logging.getLogger('XTB Calculator')


class XTBCalculator(BaseCalculator):
    """XTB calculator for quantum chemistry calculations"""
    
    def __init__(self, config: Dict[str, Any], max_workers: Optional[int] = None):
        """
        Initialize XTB calculator
        
        Args:
            config: XTB configuration from YAML
            max_workers: Maximum number of parallel workers
        """
        self.config = config
        self.commands = config.get('command', [])
        self.max_workers = max_workers or min(cpu_count(), 30)
        
        if not self.commands:
            raise ValueError("No XTB commands specified in configuration")
    
    def _prepare_molecule_directory(self, xyz_file: Path, work_dir: Path) -> Path:
        """
        Prepare individual directory for each molecule
        
        Args:
            xyz_file: Source XYZ file
            work_dir: Base working directory
            
        Returns:
            Path to molecule-specific directory
        """
        molecule_name = xyz_file.stem
        molecule_dir = work_dir / molecule_name
        molecule_dir.mkdir(exist_ok=True)
        
        # Copy XYZ file to molecule directory
        dest_xyz = molecule_dir / xyz_file.name
        shutil.copy2(xyz_file, dest_xyz)
        
        return molecule_dir
    
    def _execute_xtb_commands(self, work_item: Tuple[Path, str]) -> str:
        """
        Worker function to execute XTB commands for a single molecule
        
        Args:
            work_item: Tuple of (molecule_directory, xyz_filename)
            
        Returns:
            Result message
        """
        molecule_dir, xyz_filename = work_item
        process_id = os.getpid()
        
        try:
            logger.info(f"[PID {process_id}] Processing {xyz_filename} in {molecule_dir}")
            
            for i, command_template in enumerate(self.commands):
                 # Replace placeholder if present, otherwise use command as-is
                if '{}' in command_template:
                    command = command_template.format(xyz_filename)
                else:
                    command = command_template
                
                # Create log file for this command
                log_file = molecule_dir / f"xtb_step_{i+1}.log"
                
                logger.info(f"[PID {process_id}] Executing: {command}")
                
                with open(log_file, "w") as log:
                    result = subprocess.run(
                        command.split(),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        cwd=molecule_dir,
                        check=True
                    )
                
                # Check if expected output files exist for multi-step calculations
                if i == 0 and len(self.commands) > 1:
                    expected_output = molecule_dir / "xtbopt.xyz"
                    if not expected_output.exists():
                        raise Exception(f"Expected output file {expected_output} not found after step {i+1}")
            
            logger.info(f"[PID {process_id}] Completed processing: {xyz_filename}")
            return f"SUCCESS: {molecule_dir}/{xyz_filename}"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"XTB command failed for {xyz_filename}: {e}"
            logger.error(f"[PID {process_id}] {error_msg}")
            return f"ERROR: {error_msg}"
        except Exception as e:
            error_msg = f"Processing error for {xyz_filename}: {str(e)}"
            logger.error(f"[PID {process_id}] {error_msg}")
            return f"ERROR: {error_msg}"
    
    def calculate_batch(self, xyz_files: List[Path], output_dir: Path) -> Dict[str, str]:
        """
        Perform XTB calculations on batch of XYZ files
        
        Args:
            xyz_files: List of XYZ file paths
            output_dir: Output directory for results
            
        Returns:
            Dictionary with calculation results
        """
        if not xyz_files:
            logger.warning("No XYZ files provided for calculation")
            return {}
        
        logger.info(f"Starting XTB batch calculation for {len(xyz_files)} molecules")
        logger.info(f"Using {self.max_workers} parallel workers")
        
        # Prepare work items
        work_items = []
        for xyz_file in xyz_files:
            molecule_dir = self._prepare_molecule_directory(xyz_file, output_dir)
            work_items.append((molecule_dir, xyz_file.name))
        
        # Execute calculations in parallel
        with Pool(processes=self.max_workers) as pool:
            results = list(tqdm(
                pool.imap(self._execute_xtb_commands, work_items),
                total=len(work_items),
                desc="XTB Calculations"
            ))
        
        # Process results
        success_count = sum(1 for r in results if r.startswith("SUCCESS"))
        error_count = len(results) - success_count
        
        logger.info(f"XTB batch calculation completed: {success_count} successful, {error_count} failed")
        
        # Log error details
        for result in results:
            if result.startswith("ERROR"):
                logger.error(result)
        
        return {
            'total': len(xyz_files),
            'success': success_count,
            'errors': error_count,
            'results': results
        }
    
    def calculate_single(self, xyz_file: Path, output_dir: Path) -> str:
        """
        Perform XTB calculation on single XYZ file
        
        Args:
            xyz_file: XYZ file path
            output_dir: Output directory for results
            
        Returns:
            Result message
        """
        molecule_dir = self._prepare_molecule_directory(xyz_file, output_dir)
        work_item = (molecule_dir, xyz_file.name)
        return self._execute_xtb_commands(work_item)
    