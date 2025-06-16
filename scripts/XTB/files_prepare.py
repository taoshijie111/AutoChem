#!/usr/bin/env python3
"""
XYZ File Batch Processor

This script processes .xyz files from an input directory and organizes them
into batches, copying them to separate output directories with individual
folders for each file.

Usage:
    python batch_xyz_files.py input_folder [options]

Arguments:
    input_folder    Path to the folder containing .xyz files

Options:
    -o, --output    Output directory (default: current directory)
    -n, --batch-size    Number of files per batch (default: 1000)
    -p, --prefix    Batch folder prefix (default: "batch")
    -h, --help      Show this help message
"""

import os
import shutil
import argparse
import glob
from pathlib import Path
from typing import List, Tuple


def find_xyz_files(input_folder: str) -> List[str]:
    """
    Find all .xyz files in the specified folder.
    
    Args:
        input_folder: Path to the input directory
        
    Returns:
        List of paths to .xyz files
        
    Raises:
        FileNotFoundError: If the input folder does not exist
        ValueError: If no .xyz files are found
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"Input folder '{input_folder}' does not exist")
    
    # Use glob to find all .xyz files (case-insensitive)
    pattern = os.path.join(input_folder, "*.xyz")
    xyz_files = glob.glob(pattern)
    
    # Also check for uppercase extension
    pattern_upper = os.path.join(input_folder, "*.XYZ")
    xyz_files.extend(glob.glob(pattern_upper))
    
    if not xyz_files:
        raise ValueError(f"No .xyz files found in '{input_folder}'")
    
    # Sort files for consistent ordering
    xyz_files.sort()
    return xyz_files


def create_batches(files: List[str], batch_size: int) -> List[List[str]]:
    """
    Divide the list of files into batches of specified size.
    
    Args:
        files: List of file paths
        batch_size: Maximum number of files per batch
        
    Returns:
        List of batches, where each batch is a list of file paths
    """
    batches = []
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batches.append(batch)
    return batches


def copy_batch(batch_files: List[str], batch_output_dir: str, 
               starting_global_index: int) -> Tuple[int, int]:
    """
    Copy a batch of files to the specified output directory, creating
    individual folders for each file with global indexing.
    
    Args:
        batch_files: List of file paths to copy
        batch_output_dir: Destination batch directory
        starting_global_index: Starting global index for this batch
        
    Returns:
        Tuple of (successful_copies, failed_copies)
    """
    # Create batch output directory if it doesn't exist
    os.makedirs(batch_output_dir, exist_ok=True)
    
    successful = 0
    failed = 0
    global_index = starting_global_index
    
    for file_path in batch_files:
        try:
            # Create individual folder for this file using global index
            file_folder = os.path.join(batch_output_dir, str(global_index))
            os.makedirs(file_folder, exist_ok=True)
            
            # Copy file and rename to molecule.xyz
            destination = os.path.join(file_folder, "molecule.xyz")
            shutil.copy2(file_path, destination)
            
            successful += 1
            
        except Exception as e:
            print(f"Warning: Failed to copy '{file_path}': {e}")
            failed += 1
        
        # Increment global index regardless of success/failure to maintain consistency
        global_index += 1
    
    return successful, failed


def process_xyz_files(input_folder: str, output_folder: str, 
                     batch_size: int, prefix: str) -> None:
    """
    Main processing function that orchestrates the batching operation.
    
    Args:
        input_folder: Path to input directory containing .xyz files
        output_folder: Path to output directory for batch folders
        batch_size: Number of files per batch
        prefix: Prefix for batch folder names
    """
    try:
        # Find all .xyz files
        print(f"Scanning for .xyz files in '{input_folder}'...")
        xyz_files = find_xyz_files(input_folder)
        print(f"Found {len(xyz_files)} .xyz files")
        
        # Create batches
        batches = create_batches(xyz_files, batch_size)
        print(f"Creating {len(batches)} batches with up to {batch_size} files each")
        print(f"Each file will be placed in an individual folder and renamed to 'molecule.xyz'")
        
        # Process each batch
        total_successful = 0
        total_failed = 0
        global_index = 1  # Global index starts at 1
        
        for i, batch in enumerate(batches, 1):
            batch_folder = f"{prefix}_{i}"
            batch_output_dir = os.path.join(output_folder, batch_folder)
            
            print(f"Processing batch {i}/{len(batches)}: {len(batch)} files -> '{batch_folder}'")
            print(f"  Global index range: {global_index} to {global_index + len(batch) - 1}")
            
            successful, failed = copy_batch(batch, batch_output_dir, global_index)
            total_successful += successful
            total_failed += failed
            
            print(f"  Copied: {successful}, Failed: {failed}")
            
            # Update global index for next batch
            global_index += len(batch)
        
        # Summary
        print(f"\nProcessing complete!")
        print(f"Total files processed: {len(xyz_files)}")
        print(f"Successfully copied: {total_successful}")
        print(f"Failed to copy: {total_failed}")
        print(f"Batches created: {len(batches)}")
        print(f"Directory structure: {prefix}_X/Y/molecule.xyz")
        print(f"  where X = batch number, Y = global file index")
        
        if total_failed > 0:
            print(f"\nWarning: {total_failed} files could not be copied. Check the warnings above.")
            
    except Exception as e:
        print(f"Error: {e}")
        return


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Batch process .xyz files into organized folders with individual file directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python batch_xyz_files.py /path/to/xyz/files
    python batch_xyz_files.py /input/folder -o /output/folder -n 500 -p group
    python batch_xyz_files.py ./xyz_data --batch-size 2000 --prefix dataset

Output structure:
    output_folder/
    ├── batch_1/
    │   ├── 1/
    │   │   └── molecule.xyz
    │   ├── 2/
    │   │   └── molecule.xyz
    │   └── ...
    ├── batch_2/
    │   ├── 1001/  (if batch_size is 1000)
    │   │   └── molecule.xyz
    │   └── ...
        """
    )
    
    parser.add_argument(
        "input_folder",
        help="Path to the folder containing .xyz files"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Output directory for batch folders (default: current directory)"
    )
    
    parser.add_argument(
        "-n", "--batch-size",
        type=int,
        default=1000,
        help="Number of files per batch (default: 1000)"
    )
    
    parser.add_argument(
        "-p", "--prefix",
        default="batch",
        help="Prefix for batch folder names (default: 'batch')"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.batch_size <= 0:
        print("Error: Batch size must be a positive integer")
        return
    
    # Convert paths to absolute paths
    input_folder = os.path.abspath(args.input_folder)
    output_folder = os.path.abspath(args.output)
    
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Batch size: {args.batch_size}")
    print(f"Batch prefix: {args.prefix}")
    print("-" * 50)
    
    # Process the files
    process_xyz_files(input_folder, output_folder, args.batch_size, args.prefix)


if __name__ == "__main__":
    main()