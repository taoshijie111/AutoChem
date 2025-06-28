# Quantum Chemistry Automation Tool

This tool provides automated workflows for quantum chemistry calculations, featuring SMILES-to-3D coordinate generation using OpenBabel and quantum chemistry calculations using XTB (extended tight-binding). The application supports batch processing and parallel execution for efficient handling of large molecular datasets.

## Features

The tool offers three primary workflows for computational chemistry automation.

**Coordinate Generation** converts SMILES strings to optimized 3D molecular coordinates using OpenBabel with configurable force fields including MMFF94, UFF, and GAFF. The system includes comprehensive error logging for failed conversions and supports batch processing of molecular datasets with progress tracking.

**XTB Calculations** performs quantum chemistry calculations using XTB with configurable calculation steps defined through YAML configuration files. The system supports parallel execution across multiple CPU cores and handles both geometry optimization and property calculations such as vertical ionization potential and electron affinity calculations.

**Combined Workflow** integrates both coordinate generation and XTB calculations in a single automated pipeline, streamlining the process from SMILES input to quantum chemistry results without manual intervention between steps.

## Installation Requirements

The application requires OpenBabel and XTB to be installed and accessible from the command line. Python dependencies include PyYAML for configuration management, tqdm for progress tracking, and standard libraries for multiprocessing and file operations. Ensure both OpenBabel and XTB executables are available in your system PATH.

## Configuration

XTB calculations require a YAML configuration file specifying the calculation commands to be executed. The system will automatically generate a sample configuration file if none exists at the specified path. The configuration supports sequential command execution with placeholders for input files and customizable calculation parameters.

Example configuration structure:

```yaml
xtb:
  command:
    - 'xtb {} --opt normal -P 1'
    - 'xtb xtbopt.xyz --vipea --gbsa benzene'
```

The placeholder `{}` in commands will be replaced with the appropriate input filename during execution. Commands are executed sequentially, allowing for multi-step calculation workflows.

## Usage Examples

**Generate 3D coordinates from SMILES:**

```bash
export OMP_NUM_THREADS=1
python main.py coords input.smi --tag molecular_set_01
```

This command reads SMILES strings from `input.smi` and generates optimized 3D coordinates, creating an output directory tagged with "molecular_set_01" and the current timestamp.

**Run XTB calculations on existing XYZ files:**

```bash
export OMP_NUM_THREADS=1
python main.py xtb /path/to/xyz/directory --config config.yaml
```

This command processes all XYZ files in the specified directory using the calculation steps defined in the configuration file.

**Run XTB calculations to output xyz files:**

```bash
export OMP_NUM_THREADS=1
python main.py xtb /path/to/xyz/directory --config config.yaml --out_xyz
```
This command will yield the molecular structure optimized using xtb.

**Execute complete SMILES-to-XTB workflow:**

```bash
export OMP_NUM_THREADS=1
python main.py combined input.smi --config config.yaml
```

This command performs the entire workflow from SMILES input through coordinate generation to XTB calculations in a single execution.

**Run XTB calculations with parallel processing:**

```bash
python main.py xtb input.smi --config config.yaml --max-workers 8
```

This command utilizes up to 8 parallel workers for XTB calculations, significantly reducing processing time for large molecular datasets.

## Input File Format

SMILES input files should contain one SMILES string per line in plain text format with .smi extension. The system automatically generates sequential molecule names in the format `molecule_1`, `molecule_2`, etc. Empty lines are ignored, and the system handles error logging for problematic SMILES strings that cannot be processed.

## Output Organization

The application creates timestamped output directories following systematic naming conventions that include the source filename, execution timestamp, and workflow type. Coordinate generation outputs include XYZ files with enhanced metadata containing original SMILES strings and chemical formulas in the comment line.

XTB calculation outputs are organized in individual directories per molecule, with each directory containing the input XYZ file, calculation log files, and result files such as optimized geometries and property calculations. The hierarchical organization facilitates easy result analysis and data management.

## Error Handling and Logging

The system provides comprehensive error logging with detailed timestamps and failure reasons for problematic molecules. Failed SMILES conversions are logged to dedicated error files with structured format including timestamp, original SMILES, molecule name, and error description for subsequent analysis and debugging.

The logging system supports configurable verbosity levels ranging from DEBUG to ERROR, allowing users to control the amount of information displayed during execution. This flexibility supports both detailed debugging scenarios and streamlined production environments.

## Command Line Options

The application supports various command-line options for customizing execution behavior. Force field selection allows users to choose between MMFF94, UFF, and GAFF for coordinate optimization. The number of optimization steps can be specified to balance computational cost with structural accuracy.

Parallel worker configuration enables users to optimize XTB calculations for their available computational resources. Output format options include the ability to convert optimized geometries back to standard XYZ format for compatibility with other software packages.

Additional options include the ability to skip force field optimization during coordinate generation and configurable logging levels for different operational requirements.

## Getting Started

To begin using the tool, ensure OpenBabel and XTB are properly installed and accessible. Place your SMILES input file in the working directory and run the desired workflow command. For XTB calculations, the system will create a sample configuration file if none exists, which can then be customized according to your computational requirements.

For detailed command-line options and additional examples, use the `--help` flag with any command to display comprehensive usage information and available parameters.