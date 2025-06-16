1. 准备xyz文件
2. 执行python files_prepare.py /input/folder -o /output/folder -n 500 -p group 准备输入文件
3. 执行for num in {2..10}; do cp xtb_array.sh batch_${num}; cd batch_${num}; sbatch xtb_array.sh; cd ..; done 提交任务