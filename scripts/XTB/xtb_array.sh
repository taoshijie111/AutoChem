#!/bin/bash
#SBATCH --job-name=xtb             # Job name
#SBATCH --nodes=1                  # Number of nodes
#SBATCH --ntasks-per-node=1       # Number of cores (or tasks) per node
#SBATCH --time=24:00:00            # Time limit in HH:MM:SS
#SBATCH --partition=cpu192
#SBATCH --array=1-64               # Job array with indices 1-64

# Directory containing all the numbered folders
BASE_DIR=$(pwd)

# Calculate folders per job array task (10000 folders from 1-10000)
TOTAL_FOLDERS=1000
FOLDERS_PER_TASK=$((TOTAL_FOLDERS / 64 + 1))
# Calculate start and end folder indices for this task
START_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) * FOLDERS_PER_TASK + 1 ))
END_IDX=$(( START_IDX + FOLDERS_PER_TASK - 1 ))
# Ensure we don't exceed the maximum folder number
if [ ${END_IDX} -gt 1000 ]; then
    END_IDX=1000
fi

echo "Processing folders from ${START_IDX} to ${END_IDX}"

# Loop through the range of folders assigned to this task
for i in $(seq ${START_IDX} ${END_IDX}); do
    # Format folder name with leading zeros (5 digits)
    FOLDER_NUM=$(printf ${i})
    WORK_DIR="${BASE_DIR}/${FOLDER_NUM}"
    OUTPUT_FILE="${WORK_DIR}/xtb_output.log"
    
    # Check if the folder exists and contains molecule.xyz
    if [ -d "${WORK_DIR}" ]; then
#        # Check if output file already exists and contains "normal termination of xtb"
#        if [ -f "${OUTPUT_FILE}" ] && grep -q "normal termination of xtb" "${OUTPUT_FILE}"; then
#            echo "Skipping folder ${FOLDER_NUM} - XTB calculation already completed successfully"
#            continue
#        fi
        
        echo "Processing folder: ${FOLDER_NUM}"
        
        # Change to the working directory
        cd "${WORK_DIR}"
        
        # Run xtb with the specified options and redirect output to file
        xtb molecule.xyz --ohess --raman --ptb > xtb_output.log 2>&1
        
        # Check the exit status
        if [ $? -ne 0 ]; then
            echo "Error: XTB calculation failed in folder ${FOLDER_NUM}"
        else
            # Verify output file contains successful termination message
            if grep -q "normal termination of xtb" xtb_output.log; then
                echo "XTB calculation completed successfully in folder ${FOLDER_NUM}"
            else
                echo "Warning: XTB calculation in folder ${FOLDER_NUM} finished but might have issues"
            fi
        fi
        
        # Return to base directory for next folder
        cd "${BASE_DIR}"
    else
        echo "Skipping folder ${FOLDER_NUM} - directory does not exist or molecule.xyz not found"
    fi
done

exit 0


