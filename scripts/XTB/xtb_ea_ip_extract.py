import os
import re
import pandas as pd
import sys
import argparse
from pathlib import Path


def extract_ip_ea_from_vipea_log(log_file_path):
    """
    从 vipea.log 文件中提取 IP 和 EA 数值
    
    Args:
        log_file_path (str): vipea.log 文件的完整路径
    
    Returns:
        tuple: (IP值, EA值) 或 (None, None) 如果提取失败
    """
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 使用正则表达式提取 IP 和 EA 数值
        ip_pattern = r'delta SCC IP \(eV\):\s+([\d.-]+)'
        ea_pattern = r'delta SCC EA \(eV\):\s+([\d.-]+)'
        
        ip_match = re.search(ip_pattern, content)
        ea_match = re.search(ea_pattern, content)
        
        ip_value = float(ip_match.group(1)) if ip_match else None
        ea_value = float(ea_match.group(1)) if ea_match else None
        
        return ip_value, ea_value
        
    except FileNotFoundError:
        print(f"错误：文件 {log_file_path} 不存在")
        return None, None
    except UnicodeDecodeError:
        # 尝试使用不同的编码
        try:
            with open(log_file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            
            ip_pattern = r'delta SCC IP \(eV\):\s+([\d.-]+)'
            ea_pattern = r'delta SCC EA \(eV\):\s+([\d.-]+)'
            
            ip_match = re.search(ip_pattern, content)
            ea_match = re.search(ea_pattern, content)
            
            ip_value = float(ip_match.group(1)) if ip_match else None
            ea_value = float(ea_match.group(1)) if ea_match else None
            
            return ip_value, ea_value
            
        except Exception as e:
            print(f"编码错误：无法读取文件 {log_file_path}: {e}")
            return None, None
    except ValueError as e:
        print(f"数值转换错误：文件 {log_file_path} 中的数据格式有误: {e}")
        return None, None
    except Exception as e:
        print(f"读取文件 {log_file_path} 时发生未知错误: {e}")
        return None, None


def find_and_extract_vipea_data(root_directory, file_name='vipea.log', output_file=None, include_incomplete=False):
    """
    递归遍历目录，查找所有 vipea.log 文件并提取 IP/EA 数据
    
    Args:
        root_directory (str): 要搜索的根目录
        output_file (str, optional): 输出 CSV 文件的路径
        include_incomplete (bool): 是否包含缺失 IP 或 EA 数据的条目
    
    Returns:
        pandas.DataFrame: 包含 name, IP, EA 列的数据框
    """
    
    print(f"开始在目录 {root_directory} 中搜索 {file_name} 文件...")
    
    data_list = []
    found_files = 0
    successful_extractions = 0
    
    # 递归遍历所有目录
    for root, dirs, files in os.walk(root_directory):
        if file_name in files:
            found_files += 1
            vipea_log_path = os.path.join(root, file_name)
            
            # 获取父目录名称作为 name
            parent_dir_name = os.path.basename(root)
            
            print(f"处理文件: {vipea_log_path}")
            print(f"目录名称: {parent_dir_name}")
            
            # 提取 IP 和 EA 数值
            ip_value, ea_value = extract_ip_ea_from_vipea_log(vipea_log_path)
            
            # 根据设置决定是否包含不完整的数据
            if include_incomplete or (ip_value is not None and ea_value is not None):
                data_list.append({
                    'name': parent_dir_name,
                    'IP': ip_value,
                    'EA': ea_value,
                })
                
                if ip_value is not None and ea_value is not None:
                    successful_extractions += 1
                    print(f"  ✓ IP: {ip_value:.4f} eV, EA: {ea_value:.4f} eV")
                else:
                    print(f"  ⚠ 数据不完整 - IP: {ip_value}, EA: {ea_value}")
            else:
                print(f"  ✗ 跳过不完整的数据")
    
    print(f"\n搜索完成！")
    print(f"找到 {file_name} 文件: {found_files} 个")
    print(f"成功提取完整数据: {successful_extractions} 个")
    print(f"总数据条目: {len(data_list)} 个")
    
    if not data_list:
        print("警告：没有找到任何数据！")
        return pd.DataFrame(columns=['name', 'IP', 'EA'])
    
    # 创建 DataFrame
    df = pd.DataFrame(data_list)
    
    # 按 name 列排序
    df = df.sort_values('name').reset_index(drop=True)
    
    # 显示统计信息
    print(f"\nDataFrame 统计信息:")
    print(f"总行数: {len(df)}")
    print(f"IP 数据完整性: {df['IP'].notna().sum()}/{len(df)}")
    print(f"EA 数据完整性: {df['EA'].notna().sum()}/{len(df)}")
    
    if len(df) > 0:
        print(f"\nIP 统计:")
        print(f"  范围: {df['IP'].min():.4f} - {df['IP'].max():.4f} eV")
        print(f"  平均值: {df['IP'].mean():.4f} eV")
        
        print(f"\nEA 统计:")
        print(f"  范围: {df['EA'].min():.4f} - {df['EA'].max():.4f} eV")
        print(f"  平均值: {df['EA'].mean():.4f} eV")
    
    # 保存到文件
    if output_file:
        try:
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n数据已保存到: {output_file}")
        except Exception as e:
            print(f"保存文件时发生错误: {e}")
    
    # 显示前几行数据
    print(f"\n前 10 行数据预览:")
    print(df.head(10).to_string(index=False))
    
    return df


if __name__ == '__main__':
    parers = argparse.ArgumentParser(description='Extract EA and IP from xtb log files')
    parers.add_argument('root', help='root file of log files')
    parers.add_argument('--log_name', default='xtb_step_2.log', help='name of eaip log files')
    parers.add_argument('-o', '--output_file', help='path of save result')
    args = parers.parse_args()
    
    find_and_extract_vipea_data(args.root, file_name=args.log_name, output_file=args.output_file, include_incomplete=False)
    