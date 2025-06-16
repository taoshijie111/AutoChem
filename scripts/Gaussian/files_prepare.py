#!/usr/bin/env python3
"""
XYZ to Gaussian GJF Converter

This script converts molecular coordinates from .xyz files to Gaussian .gjf files
based on computational parameters specified in a YAML configuration file.

Usage:
    python xyz_to_gjf.py --xyz_dir <xyz_directory> --config <config.yaml> --output_dir <output_directory>

Requirements:
    - PyYAML for YAML parsing
    - Standard Python libraries (argparse, os, pathlib)
"""

import argparse
import os
import yaml
from pathlib import Path
import sys


class XYZToGJFConverter:
    """Converter class for transforming XYZ files to Gaussian GJF format."""
    
    def __init__(self, xyz_dir, config_file, output_dir, batch_size=None, batch_prefix="batch"):
        """
        Initialize the converter with input and output directories.
        
        Args:
            xyz_dir (str): Directory containing .xyz files
            config_file (str): Path to the YAML configuration file
            output_dir (str): Directory for output .gjf files
            batch_size (int): Maximum number of files per batch (None for no batching)
            batch_prefix (str): Prefix for batch folder names
        """
        self.xyz_dir = Path(xyz_dir)
        self.config_file = Path(config_file)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        self.batch_prefix = batch_prefix
        self.global_index = 1  # Global index counter for individual file folders
        
        # Validate input paths
        self._validate_inputs()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _validate_inputs(self):
        """Validate that input directories and files exist."""
        if not self.xyz_dir.exists():
            raise FileNotFoundError(f"XYZ directory not found: {self.xyz_dir}")
        
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
    
    def _load_config(self):
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
            
            if 'Gaussian' not in config or 'command' not in config['Gaussian']:
                raise ValueError("Invalid configuration format. Expected 'Gaussian.command' structure.")
            
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
    
    def _read_xyz_file(self, xyz_path):
        """
        Read and parse an XYZ file.
        
        Args:
            xyz_path (Path): Path to the .xyz file
            
        Returns:
            tuple: (atom_count, comment_lines, coordinates)
        """
        try:
            with open(xyz_path, 'r') as file:
                lines = file.readlines()
            
            # Parse XYZ format
            atom_count = int(lines[0].strip())
            comment_lines = lines[1].strip()
            
            coordinates = []
            for i in range(2, 2 + atom_count):
                line = lines[i].strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        atom = parts[0]
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        coordinates.append((atom, x, y, z))
            
            return atom_count, comment_lines, coordinates
            
        except (IndexError, ValueError) as e:
            raise ValueError(f"Error parsing XYZ file {xyz_path}: {e}")
    
    def _read_header_file(self, header_path):
        """
        Read computational parameters from a header .gjf file.
        
        Args:
            header_path (Path): Path to the header file
            
        Returns:
            tuple: (clean_header_content, charge, multiplicity)
        """
        try:
            with open(header_path, 'r') as file:
                content = file.read().strip()
            
            # Parse content to extract charge and multiplicity, and clean header
            lines = content.split('\n')
            charge = 0
            multiplicity = 1
            clean_lines = []
            has_charge_mult = False
            
            # Process each line to separate header content from charge/multiplicity
            for line in lines:
                line_stripped = line.strip()
                
                # Skip empty lines when processing
                if not line_stripped:
                    clean_lines.append(line)
                    continue
                
                # Keep computational parameter lines (% and # lines)
                if line_stripped.startswith('%') or line_stripped.startswith('#'):
                    clean_lines.append(line)
                    continue
                
                # Check if this line contains charge and multiplicity
                parts = line_stripped.split()
                if len(parts) == 2:
                    try:
                        charge = int(parts[0])
                        multiplicity = int(parts[1])
                        has_charge_mult = True
                        # Skip this line - don't add it to clean_lines
                        continue
                    except ValueError:
                        # Not a charge/multiplicity line, keep it
                        clean_lines.append(line)
                else:
                    # Not a charge/multiplicity line, keep it
                    clean_lines.append(line)
            
            # Remove trailing empty lines from header
            while clean_lines and not clean_lines[-1].strip():
                clean_lines.pop()
            
            clean_header_content = '\n'.join(clean_lines)
            return clean_header_content, has_charge_mult, charge, multiplicity
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Header file not found: {header_path}")
    
    def _generate_gjf_content(self, header_content, comment_lines, coordinates, 
                             charge=0, multiplicity=1):
        """
        Generate the content for a .gjf file.
        
        Args:
            header_content (str): Computational parameters from header file
            comment_lines (str): Comment lines from XYZ file
            coordinates (list): List of (atom, x, y, z) tuples
            charge (int): Molecular charge (default: 0)
            multiplicity (int): Spin multiplicity (default: 1)
            
        Returns:
            str: Complete .gjf file content
        """
        gjf_lines = []
        
        # Add header content (computational parameters)
        gjf_lines.append(header_content)
        gjf_lines.append("")  # Blank line after header
        
        # Add comment/title section
        gjf_lines.append(comment_lines if comment_lines else "Generated from XYZ file")
        gjf_lines.append("")  # Blank line after title
        
        # Add charge and multiplicity only if not already present in header
        gjf_lines.append(f"{charge} {multiplicity}")
        
        # Add coordinates
        for atom, x, y, z in coordinates:
            gjf_lines.append(f"{atom:2s} {x:12.6f} {y:12.6f} {z:12.6f}")
        
        # Add final blank line
        gjf_lines.append("")
        gjf_lines.append("")
        
        return "\n".join(gjf_lines)
    
    def _get_batch_directory(self, batch_number):
        """
        Get the directory path for a specific batch.
        
        Args:
            batch_number (int): Batch number
            
        Returns:
            Path: Directory path for the batch
        """
        batch_dir = self.output_dir / f"{self.batch_prefix}_{batch_number}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        return batch_dir
    
    def _get_file_directory(self, batch_dir, file_index):
        """
        Get the directory path for a specific file within a batch.
        
        Args:
            batch_dir (Path): Batch directory path
            file_index (int): Global file index
            
        Returns:
            Path: Directory path for the file
        """
        file_dir = batch_dir / str(file_index)
        file_dir.mkdir(parents=True, exist_ok=True)
        return file_dir
    
    def _get_output_filename(self, xyz_filename, step_number=None):
        """
        Generate output filename for .gjf file.
        
        Args:
            xyz_filename (str): Original XYZ filename
            step_number (int): Step number for multi-step calculations
            
        Returns:
            str: Output filename
        """
        base_name = Path(xyz_filename).stem
        if step_number is not None:
            return f"{base_name}_step{step_number:02d}.gjf"
        else:
            return f"{base_name}.gjf"
    
    def convert_file(self, xyz_filename, charge=None, multiplicity=None, override_charge_mult=False, 
                     output_directory=None, gjf_name=None):
        """
        Convert a single XYZ file to Gaussian GJF format.
        
        Args:
            xyz_filename (str): Name of the XYZ file to convert
            charge (int): Molecular charge (override header if override_charge_mult=True)
            multiplicity (int): Spin multiplicity (override header if override_charge_mult=True)
            override_charge_mult (bool): Whether to override charge/multiplicity from header
            output_directory (Path): Specific output directory (overrides default batching)
            gjf_name (str): Name for the output .gjf file (if not specified, uses original .xyz filename)
            
        Returns:
            list: List of generated file paths
        """
        xyz_path = self.xyz_dir / xyz_filename
        
        if not xyz_path.exists():
            raise FileNotFoundError(f"XYZ file not found: {xyz_path}")
        
        # Read XYZ file
        atom_count, comment_lines, coordinates = self._read_xyz_file(xyz_path)
        
        # Get header files from configuration
        header_files = self.config['Gaussian']['command']
        
        if not isinstance(header_files, list):
            header_files = [header_files]
        
        generated_files = []
        
        # Use provided output directory or default output directory
        if output_directory is None:
            output_directory = self.output_dir
        
        # Process each step
        for step_idx, header_file in enumerate(header_files):
            # Resolve header file path (relative to config file directory)
            header_path = self.config_file.parent / header_file
            
            # Read header content and parse charge/multiplicity
            header_content, has_charge_mult, header_charge, header_mult = self._read_header_file(header_path)
            
            # Determine final charge and multiplicity
            final_charge = charge if (charge is not None and override_charge_mult) else (header_charge if has_charge_mult else (charge or 0))
            final_mult = multiplicity if (multiplicity is not None and override_charge_mult) else (header_mult if has_charge_mult else (multiplicity or 1))
            
            # Generate GJF content
            gjf_content = self._generate_gjf_content(
                header_content, comment_lines, coordinates, 
                final_charge, final_mult
            )
            
            # Determine output filename
            if gjf_name:
                output_filename = gjf_name
            else:
                output_filename = self._get_output_filename(xyz_filename)
            
            output_path = output_directory / output_filename
            
            # Write GJF file
            with open(output_path, 'w') as file:
                file.write(gjf_content)
            
            generated_files.append(output_path)
            print(f"Generated: {output_path}")
            
            if has_charge_mult and not override_charge_mult:
                print(f"  Using charge={final_charge}, multiplicity={final_mult} from header file")
            elif override_charge_mult:
                print(f"  Overriding with charge={final_charge}, multiplicity={final_mult}")
        
        return generated_files
    
    def convert_all_xyz_files(self, charge=None, multiplicity=None, override_charge_mult=False, gjf_name=None):
        """
        Convert all .xyz files in the input directory with optional batching.
        
        Args:
            charge (int): Molecular charge (override header if override_charge_mult=True)
            multiplicity (int): Spin multiplicity (override header if override_charge_mult=True)
            override_charge_mult (bool): Whether to override charge/multiplicity from header
        """
        xyz_files = list(self.xyz_dir.glob("*.xyz"))
        
        if not xyz_files:
            print(f"No .xyz files found in directory: {self.xyz_dir}")
            return
        
        print(f"Found {len(xyz_files)} .xyz files to convert")
        
        if self.batch_size is None:
            # No batching - process all files in the main output directory
            print("Processing all files without batching")
            for xyz_file in xyz_files:
                try:
                    self.convert_file(xyz_file.name, charge, multiplicity, override_charge_mult, gjf_name)
                except Exception as e:
                    print(f"Error converting {xyz_file.name}: {e}")
        else:
            # Process files in batches
            print(f"Processing files in batches of {self.batch_size}")
            batch_number = 1
            
            for i in range(0, len(xyz_files), self.batch_size):
                batch_files = xyz_files[i:i + self.batch_size]
                batch_dir = self._get_batch_directory(batch_number)
                
                print(f"\nProcessing {self.batch_prefix}_{batch_number} ({len(batch_files)} files)")
                
                for xyz_file in batch_files:
                    try:
                        # Create individual file directory within batch
                        file_dir = self._get_file_directory(batch_dir, self.global_index)
                        
                        # Convert file to the individual directory
                        generated_files = self.convert_file(
                            xyz_file.name, charge, multiplicity, override_charge_mult, file_dir, gjf_name
                        )
                        
                        print(f"  Files for {xyz_file.name} placed in directory: {file_dir}")
                        
                        # Increment global index
                        self.global_index += 1
                        
                    except Exception as e:
                        print(f"Error converting {xyz_file.name}: {e}")
                        # Still increment global index to maintain consistency
                        self.global_index += 1
                
                batch_number += 1
            
            print(f"\nBatching complete. Created {batch_number - 1} batches.")
            print(f"Total files processed: {self.global_index - 1}")
        
        print("Conversion completed successfully.")


def main():
    """Main function to handle command line arguments and execute conversion."""
    parser = argparse.ArgumentParser(
        description="Convert XYZ files to Gaussian GJF format based on YAML configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
    # Use charge/multiplicity from header files
    python xyz_to_gjf.py --xyz_dir ./molecules --config config.yaml --output_dir ./gaussian_inputs
    
    # Override charge/multiplicity from header files
    python xyz_to_gjf.py --xyz_dir ./molecules --config config.yaml --output_dir ./gaussian_inputs --charge -1 --multiplicity 2 --override
    
    # Process files in batches of 10 with custom prefix
    python xyz_to_gjf.py --xyz_dir ./molecules --config config.yaml --output_dir ./gaussian_inputs --batch_size 10 --batch_prefix job
    
    # Provide charge/multiplicity for headers that don't have them
    python xyz_to_gjf.py --xyz_dir ./molecules --config config.yaml --output_dir ./gaussian_inputs --charge 0 --multiplicity 1
        """
    )
    
    parser.add_argument('-i', '--xyz_dir', required=True,
                        help='Directory containing .xyz files')
    
    parser.add_argument('--config', required=True,
                        help='Path to the YAML configuration file')
    
    parser.add_argument('-o', '--output_dir', required=True,
                        help='Directory for output .gjf files')
    
    parser.add_argument('-b', '--batch_size', type=int, default=None,
                        help='Maximum number of files per batch (no batching if not specified)')
    
    parser.add_argument('-p', '--batch_prefix', type=str, default='batch',
                        help='Prefix for batch folder names (default: "batch")')
    
    parser.add_argument('--charge', type=int, default=None,
                        help='Molecular charge (uses header value if not specified, or if --override not used)')
    
    parser.add_argument('--multiplicity', type=int, default=None,
                        help='Spin multiplicity (uses header value if not specified, or if --override not used)')
    
    parser.add_argument('--override', action='store_true',
                        help='Override charge and multiplicity from header files with command line values')
    
    parser.add_argument('-name', '--gjf_name', type=str, default=None,
                        help='Name for the output .gjf file (if not specified, uses original .xyz filename)')
    
    parser.add_argument('--file', type=str,
                        help='Convert specific .xyz file instead of all files in directory')
    
    
    args = parser.parse_args()
    
    try:
        # Initialize converter
        converter = XYZToGJFConverter(
            args.xyz_dir, args.config, args.output_dir, 
            args.batch_size, args.batch_prefix
        )
        
        # Convert files
        if args.file:
            converter.convert_file(args.file, args.charge, args.multiplicity, args.override, args.gjf_name)
        else:
            converter.convert_all_xyz_files(args.charge, args.multiplicity, args.override, args.gjf_name)
        
        print("Conversion completed successfully.")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()