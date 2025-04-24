import argparse
import sys
import os
from typing import List, Tuple

def read_file(file_path: str) -> List[str]:
    """读取文件内容并返回行列表。"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def write_file(lines: List[str], output_path: str):
    """将行列表写入文件。"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def replace_column(lines: List[str], old_str: str, new_str: str) -> List[str]:
    """在每行中将old_str替换为new_str。"""
    return [line.replace(old_str, new_str) for line in lines]

def take_column(lines: List[str], start: str, end: str) -> List[str]:
    """提取每行中从第一个start到最后一个end的内容。"""
    result = []
    for line in lines:
        start_idx = 0 if start == '0' else line.find(start)
        if start_idx == -1:
            continue  # 跳过不包含start的行
        end_idx = len(line) if end == '-1' else line.rfind(end)
        if end_idx == -1 or end_idx < start_idx:
            continue  # 跳过不包含end或end在start之前的行
        # 提取从start开始到end结束（包括end字符串）的内容
        result.append(line[start_idx:end_idx + len(end) if end != '-1' else len(line)])
    if not result:
        print(f"警告：没有行匹配 -Ctake 的开始 '{start}' 和结束 '{end}' 条件。请检查输入文件是否包含 '{start}'。")
    return result

def single_row(lines: List[str]) -> List[str]:
    """去除重复行。"""
    return list(dict.fromkeys(lines))

def save_row(lines: List[str], keyword: str) -> List[str]:
    """保留包含关键字的行。"""
    return [line for line in lines if keyword in line]

def process_file(input_path: str, column_ops: List[Tuple[str, str, str]], row_ops: List[Tuple[str, str]], output_path: str):
    """处理单个文件，执行列和行操作。"""
    lines = read_file(input_path)
    
    # 列操作，按命令行顺序执行
    for op, arg1, arg2 in column_ops:
        if op == 'replace':
            lines = replace_column(lines, arg1, arg2)
        elif op == 'take':
            lines = take_column(lines, arg1, arg2)
            if not lines:
                print(f"错误：-Ctake '{arg1}' '{arg2}' 未匹配任何内容，输出文件将为空")
                return
    
    # 行操作
    for op, arg1 in row_ops:
        if op == 'single':
            lines = single_row(lines)
        elif op == 'save':
            lines = save_row(lines, arg1)
    
    write_file(lines, output_path)

def merge_and_process_files(input_paths: List[str], column_ops: List[Tuple[str, str, str]], row_ops: List[Tuple[str, str]], output_path: str):
    """合并多个文件并处理。"""
    merged_lines = []
    for path in input_paths:
        merged_lines.extend(read_file(path))
    
    # 列操作，按命令行顺序执行
    for op, arg1, arg2 in column_ops:
        if op == 'replace':
            merged_lines = replace_column(merged_lines, arg1, arg2)
        elif op == 'take':
            merged_lines = take_column(merged_lines, arg1, arg2)
            if not merged_lines:
                print(f"错误：-Ctake '{arg1}' '{arg2}' 未匹配任何内容，输出文件将为空")
                return
    
    # 行操作
    for op, arg1 in row_ops:
        if op == 'single':
            merged_lines = single_row(merged_lines)
        elif op == 'save':
            merged_lines = save_row(merged_lines, arg1)
    
    write_file(merged_lines, output_path)

def print_help():
    """打印帮助信息，包含核心功能和示例（中文）。"""
    help_text = """Filtertxt.py: 文本处理工具

注意：所有参数都不需要强制使用双引号（"），但建议对包含空格或特殊字符的参数使用双引号。-Creplace 和 -Ctake 的两个参数使用空格分隔。
-Ctake 特殊情况：可以使用不带双引号的 -1（表示行尾）或 0（表示行首）。-Ctake 从第一个开始字符串（从左到右）匹配到最后一个结束字符串（从右到左）。
操作顺序：-Creplace 和 -Ctake 严格按命令行中指定的顺序执行，先出现的操作先执行。

核心功能：
1. 单文件处理：
   - 列操作：
     * 替换：将每行中的指定文本替换为新文本 (-Creplace 旧文本 新文本)
     * 提取：提取每行中从第一个开始到最后一个结束的内容 (-Ctake 开始 结束 或 -Ctake 开始 -1 或 -Ctake 0 结束)
   - 行操作：
     * 去重：移除重复行 (-Rsingle)
     * 保留：保留包含指定关键字的行 (-Rsave 关键字)

2. 多文件处理：
   - 合并多个输入文件 (-M)，然后对合并后的文件应用相同的列和行操作

示例：
1. 单文件处理（先 -Ctake 后 -Creplace）：
   python filtertxt.py -I input.txt -Ctake http -1 -Creplace http https -Rsingle -Rsave https -O output.txt
   说明：
   - 提取每行中从第一个“http”到行尾的内容
   - 将“http”替换为“https”
   - 移除重复行
   - 保留包含“https”的行

2. 单文件处理（先 -Creplace 后 -Ctake）：
   python filtertxt.py -I input.txt -Creplace http https -Ctake https -1 -Rsingle -O output.txt
   说明：
   - 将“http”替换为“https”
   - 提取从“https”到行尾的内容
   - 移除重复行
3. 合并 > 单文件处理
    python filtertxt.py -M input1.txt input2.txt input3.txt -Creplace http https -Ctake https -1 -Rsingle -O output.txt

3. 处理复杂参数：
   python filtertxt.py -I E:\\SecTools\\payloads\\BlindXSS\\example_blind_ssrf_xss_filtered.txt -Ctake https://webhook.site -1 -Creplace https://webhook.site aaaaaaaaaaaaa -Rsingle -O E:\\SecTools\\payloads\\BlindXSS\\example_blind_ssrf_xss_filtered1.txt
"""
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description="文本文件处理器", add_help=False)
    parser.add_argument('-H', action='store_true', help="显示帮助和示例")
    parser.add_argument('-I', type=str, help="单文件处理的输入文件路径")
    parser.add_argument('-M', nargs='+', help="多文件处理的输入文件路径")
    parser.add_argument('-O', type=str, help="输出文件路径")
    parser.add_argument('-Creplace', nargs=2, action='append', default=[], help="替换操作：旧文本 新文本")
    parser.add_argument('-Ctake', nargs=2, action='append', default=[], help="提取操作：开始 结束 或 开始 -1 或 0 结束")
    parser.add_argument('-Rsingle', action='append_const', const=('single', ''), default=[], help="去重操作")
    parser.add_argument('-Rsave', action='append', default=[], help="保留操作：关键字")
    
    args = parser.parse_args()
    
    if args.H:
        print_help()
        return
    
    if not args.I and not args.M:
        print("错误：必须指定 -I 或 -M 之一")
        return
    
    if (args.I or args.M) and not args.O:
        print("错误：指定 -I 或 -M 时必须提供 -O")
        return
    
    # 处理文件路径
    input_path = args.I
    input_paths = args.M if args.M else []
    output_path = args.O
    
    # 验证文件路径是否存在
    if input_path and not os.path.exists(input_path):
        print(f"错误：输入文件 '{input_path}' 不存在")
        return
    for path in input_paths:
        if not os.path.exists(path):
            print(f"错误：输入文件 '{path}' 不存在")
            return
    
    # 处理列操作，严格按照命令行顺序
    column_ops = []
    i = 1  # 从 sys.argv[1] 开始，跳过脚本名
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-Creplace' and i + 2 < len(sys.argv):
            old, new = sys.argv[i + 1], sys.argv[i + 2]
            column_ops.append(('replace', old, new))
            i += 3
        elif arg == '-Ctake' and i + 2 < len(sys.argv):
            start, end = sys.argv[i + 1], sys.argv[i + 2]
            column_ops.append(('take', start, end))
            i += 3
        else:
            i += 1
    
    # 处理行操作
    row_ops = args.Rsingle
    for keyword in args.Rsave:
        row_ops.append(('save', keyword))
    
    # 处理文件
    if input_path:
        process_file(input_path, column_ops, row_ops, output_path)
    else:  # input_paths
        merge_and_process_files(input_paths, column_ops, row_ops, output_path)

if __name__ == "__main__":
    main()