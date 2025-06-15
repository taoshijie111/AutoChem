# 从smiles.smi生成.xyz文件
不执行力场优化：python main.py test.smi --coords-only --tag test --no-optimize 
选择力场： python main.py test.smi --coords-only --tag test --force-field MMFF94 --optimization-steps 1000