# Generate coordinates only
python main.py coords input.smi --tag my_molecules

# Run XTB calculations on SMI file (requires config.yaml)
python main.py xtb input.smi --config config.yaml

# Run XTB calculations on XYZ directory
python main.py xtb /path/to/xyz/files --config config.yaml

# Combined workflow (SMI -> XYZ -> XTB)
python main.py combined input.smi --config config.yaml