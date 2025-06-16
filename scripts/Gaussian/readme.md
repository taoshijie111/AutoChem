1. 准备xyz文件
2. 配置config.yaml参数，支持连续计算
3. 执行 python files_prepare.py --xyz_dir ../../output_files/xtb_smiles_list_20250616_074317_xyz/ --config config.yaml -o gaussian_input -b 9  -name molecule.gjf
4. 执行for num in {2..10}; do cp g16_array.sh batch_${num}; cd batch_${num}; sbatch g16_array.sh; cd ..; done 提交任务