# -*- coding: utf-8 -*-
import argparse
import sys
import os
import re
import html
import urllib.parse
from typing import List, Tuple

def read_file(file_path: str) -> List[str]:
    """读取文件内容并返回行列表，每行保留换行符。"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return [line if line.endswith('\n') else line + '\n' for line in lines]

def write_file(lines: List[str], output_path: str):
    """将行列表写入文件，确保每行以换行符结尾。"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if not line.endswith('\n'):
                line += '\n'
            f.write(line)

def encode_url_special(text: str) -> str:
    """只对 URL 特殊字符进行编码（如空格、<、>、& 等）。"""
    return urllib.parse.quote(text, safe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~')

def encode_url_all(text: str) -> str:
    """对所有字符进行 URL 编码（每个字符转为 %XX）。"""
    return ''.join(f'%{ord(c):02X}' for c in text)

def encode_html_special(text: str) -> str:
    """只对 HTML 特殊字符进行实体化编码（如 <, >, &, ", '）。"""
    return html.escape(text)

def encode_html_all(text: str) -> str:
    """对所有字符进行 HTML 实体化编码（转为 &#xHHHH; 形式）。"""
    return ''.join(f'&#x{ord(c):04x};' for c in text)

def encode_js_special(text: str) -> str:
    """只对 JS 特殊字符进行 Unicode 编码（如 \\, \", \', \\n, \\t）。"""
    js_entities = {
        '\\': '\\u005c',
        '"': '\\u0022',
        "'": '\\u0027',
        '\n': '\\u000a',
        '\t': '\\u0009',
        '\r': '\\u000d'
    }
    return ''.join(js_entities.get(c, c) for c in text)

def encode_js_all(text: str) -> str:
    """对所有字符进行 Unicode 编码（转为 \\uHHHH 形式）。"""
    return ''.join(f'\\u{ord(c):04x}' for c in text)

def encode_column(lines: List[str], pattern: str, encode_func) -> List[str]:
    """对匹配正则表达式的部分进行编码（URL/HTML/JS）。"""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        print(f"错误：无效的正则表达式 '{pattern}'：{e}")
        return lines

    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        match = regex.search(line_no_newline)
        if not match:
            result.append(line)
            continue

        # 获取匹配的部分
        start_pos, end_pos = match.start(), match.end()
        content = line_no_newline[start_pos:end_pos]
        if not content:
            result.append(line)
            continue

        # 编码匹配的部分
        encoded_content = encode_func(content)
        new_line = line_no_newline[:start_pos] + encoded_content + line_no_newline[end_pos:]
        result.append(new_line + '\n')
    
    return result

def replace_column(lines: List[str], pattern: str, new_str: str) -> List[str]:
    """将匹配正则表达式的部分替换为 new_str。"""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        print(f"错误：无效的正则表达式 '{pattern}'：{e}")
        return lines

    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        match = regex.search(line_no_newline)
        if not match:
            result.append(line)
            continue

        start_pos, end_pos = match.start(), match.end()
        new_line = line_no_newline[:start_pos] + new_str + line_no_newline[end_pos:]
        result.append(new_line + '\n')
    
    return result

def take_column(lines: List[str], pattern: str) -> List[str]:
    """提取每行中匹配正则表达式的部分。"""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        print(f"错误：无效的正则表达式 '{pattern}'：{e}")
        return []

    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        match = regex.search(line_no_newline)
        if not match:
            continue

        extracted = match.group(0)
        result.append(extracted + '\n' if not extracted.endswith('\n') else extracted)
    
    if not result:
        print(f"警告：没有行匹配 -Ctake 的正则表达式 '{pattern}'。请检查输入文件是否包含所需内容。")
    return result

def single_row(lines: List[str]) -> List[str]:
    """去除重复行。"""
    return list(dict.fromkeys(lines))

def save_row(lines: List[str], keyword: str) -> List[str]:
    """保留匹配正则表达式的行，支持 | (或)、& (与)。"""
    def match_keyword(line: str, key: str) -> bool:
        try:
            return bool(re.search(key, line))
        except re.error as e:
            print(f"错误：无效的正则表达式 '{key}'：{e}")
            return False

    if '|' in keyword:
        keywords = keyword.split('|')
        return [line for line in lines if any(match_keyword(line, k) for k in keywords)]
    elif '&' in keyword:
        keywords = keyword.split('&')
        return [line for line in lines if all(match_keyword(line, k) for k in keywords)]
    else:
        return [line for line in lines if match_keyword(line, keyword)]

def delete_row(lines: List[str], keyword: str) -> List[str]:
    """去除匹配正则表达式的行，支持 | (或)、& (与)。"""
    def match_keyword(line: str, key: str) -> bool:
        try:
            return bool(re.search(key, line))
        except re.error as e:
            print(f"错误：无效的正则表达式 '{key}'：{e}")
            return False

    if '|' in keyword:
        keywords = keyword.split('|')
        return [line for line in lines if not any(match_keyword(line, k) for k in keywords)]
    elif '&' in keyword:
        keywords = keyword.split('&')
        return [line for line in lines if not all(match_keyword(line, k) for k in keywords)]
    else:
        return [line for line in lines if not match_keyword(line, keyword)]

def process_file(input_path: str, column_ops: List[Tuple[str, str, str]], row_ops: List[Tuple[str, str]], output_path: str):
    """处理单个文件，执行列和行操作。"""
    lines = read_file(input_path)
    
    for op, arg1, arg2 in column_ops:
        if op == 'replace':
            lines = replace_column(lines, arg1, arg2)
        elif op == 'take':
            lines = take_column(lines, arg1)
            if not lines:
                print(f"错误：-Ctake '{arg1}' 未匹配任何内容，输出文件将为空")
                return
        elif op == 'URL':
            lines = encode_column(lines, arg1, encode_url_special)
        elif op == 'url':
            lines = encode_column(lines, arg1, encode_url_all)
        elif op == 'HTML':
            lines = encode_column(lines, arg1, encode_html_special)
        elif op == 'html':
            lines = encode_column(lines, arg1, encode_html_all)
        elif op == 'JS':
            lines = encode_column(lines, arg1, encode_js_special)
        elif op == 'js':
            lines = encode_column(lines, arg1, encode_js_all)
    
    for op, arg1 in row_ops:
        if op == 'single':
            lines = single_row(lines)
        elif op == 'save':
            lines = save_row(lines, arg1)
        elif op == 'delete':
            lines = delete_row(lines, arg1)
    
    write_file(lines, output_path)

def merge_and_process_files(input_paths: List[str], column_ops: List[Tuple[str, str, str]], row_ops: List[Tuple[str, str]], output_path: str):
    """合并多个文件并处理。"""
    merged_lines = []
    for path in input_paths:
        merged_lines.extend(read_file(path))
    
    for op, arg1, arg2 in column_ops:
        if op == 'replace':
            merged_lines = replace_column(merged_lines, arg1, arg2)
        elif op == 'take':
            merged_lines = take_column(merged_lines, arg1)
            if not merged_lines:
                print(f"错误：-Ctake '{arg1}' 未匹配任何内容，输出文件将为空")
                return
        elif op == 'URL':
            merged_lines = encode_column(merged_lines, arg1, encode_url_special)
        elif op == 'url':
            merged_lines = encode_column(merged_lines, arg1, encode_url_all)
        elif op == 'HTML':
            merged_lines = encode_column(merged_lines, arg1, encode_html_special)
        elif op == 'html':
            merged_lines = encode_column(merged_lines, arg1, encode_html_all)
        elif op == 'JS':
            merged_lines = encode_column(merged_lines, arg1, encode_js_special)
        elif op == 'js':
            merged_lines = encode_column(merged_lines, arg1, encode_js_all)
    
    for op, arg1 in row_ops:
        if op == 'single':
            merged_lines = single_row(merged_lines)
        elif op == 'save':
            merged_lines = save_row(merged_lines, arg1)
        elif op == 'delete':
            merged_lines = delete_row(merged_lines, arg1)
    
    write_file(merged_lines, output_path)

def print_help():
    """打印帮助信息，包含核心功能和示例（中文）。"""
    help_text = """Filtertxt.py: 文本处理工具

注意：所有参数都不需要强制使用双引号（"），但建议对包含空格或特殊字符（如 *、|、&、.、[、]）的参数使用双引号，特别是在 PowerShell 中。
-Creplace 需要两个参数（正则表达式 替换符），-Ctake、-CHTML、-Chtml、-CJS、-Cjs、-CURL、-Curl 只需要一个参数（正则表达式）。
所有列操作严格按命令行顺序执行。
编码操作仅对匹配内容编码，保留原行其他部分不变。
所有输出行均保证以换行符（\\n）结尾。

核心功能：
1. 单文件处理：
   - 列操作：
     * 替换：将每行中匹配正则表达式的部分替换为替换符 (-Creplace 正则表达式 替换符)
     * 提取：提取每行中匹配正则表达式的部分 (-Ctake 正则表达式)
     * HTML 编码：
       - -CHTML 正则表达式: 仅对特殊字符（<, >, &, ", '）进行实体化编码
       - -Chtml 正则表达式: 对所有字符进行实体化编码（转为 &#xHHHH; 形式）
     * Unicode 编码：
       - -CJS 正则表达式: 仅对特殊字符（\\, ", ', \\n, \\t, \\r）进行 Unicode 编码
       - -Cjs 正则表达式: 对所有字符进行 Unicode 编码（转为 \\uHHHH 形式）
     * URL 编码：
       - -CURL 正则表达式: 仅对特殊字符（空格, <, >, #, %, {, }, |, \\, ^, ~, [, ], `, ;, /, ?, :, @, &, =, +, $, ,）进行编码
       - -Curl 正则表达式: 对所有字符进行编码（转为 %XX 形式）
   - 行操作：
     * 去重：移除重复行 (-Rsingle)
     * 保留：保留匹配正则表达式的行 (-Rsave 正则表达式)
       - 支持逻辑：a|b|c（保留匹配 a 或 b 或 c 的行）；a&b&c（保留同时匹配 a 和 b 和 c 的行）
     * 删除：去除匹配正则表达式的行 (-Rdel 正则表达式)
       - 支持逻辑：a|b|c（删除匹配 a 或 b 或 c 的行）；a&b&c（删除同时匹配 a 和 b 和 c 的行）

2. 多文件处理：
   - 合并多个输入文件 (-M)，然后对合并后的文件应用相同的列和行操作

PowerShell 使用注意：
- 特殊字符（如 *、|、&、.、[、]）可能被 PowerShell 解析为命令或通配符，必须用双引号包裹参数。例如：
  - 错误：-CURL .*=.*>
  - 正确：-CURL ".*=.*>"
  - 错误：-Rdel //|/*
  - 正确：-Rdel "//|/*"
- 文件路径建议也使用双引号包裹，以避免路径中的特殊字符引发问题。

示例：
1. 单文件处理（对最后一个 = 到其后的 > 之间的内容进行 HTML 编码，仅特殊字符）：
   python filtertxt.py -I input.txt -CHTML "=[^>]+(?=>)" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：<ImG sRc=x OnErRor=print(1)>

2. 单文件处理（对整行进行 Unicode 编码，所有字符）：
   python filtertxt.py -I input.txt -Cjs ".*" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：\\u003c\\u0049\\u006d\\u0047\\u0020\\u0073\\u0052\\u0063\\u003d\\u0078\\u0020\\u004f\\u006e\\u0045\\u0072\\u0052\\u006f\\u0072\\u003d\\u0070\\u0072\\u0069\\u006e\\u0074\\u0028\\u0031\\u0029\\u003e

3. 单文件处理（对第一个 print(1) 到行尾的内容进行 URL 编码，仅特殊字符）：
   python filtertxt.py -I input.txt -CURL "print\\(1\\).*$" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：<ImG sRc=x OnErRor=print%28%31%29>

4. 单文件处理（综合操作，严格按顺序执行）：
   python filtertxt.py -I input.txt -Creplace "script[^<]*(?=<)" "DIV" -Ctake "div[^>]+(?=>)" -CHTML "=[^>]+(?=>)" -Cjs "div.*$" -Curl "print\\(1\\).*$" -Rsingle -Rsave "div|onerror" -Rdel "//|/\*" -O output.txt
   说明：
   - 替换最后一个 script 到其后的 < 之间的内容为 DIV
   - 提取第一个 div 到其后的 > 之间的内容
   - 对最后一个 = 到其后的 > 之间的内容进行 HTML 编码（仅特殊字符）
   - 对第一个 div 到行尾的内容进行 Unicode 编码（所有字符）
   - 对第一个 print(1) 到行尾的内容进行 URL 编码（所有字符）
   - 移除重复行
   - 保留包含 div 或 onerror 的行
   - 删除包含 // 或 /* 的行
"""
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description="文本文件处理器", add_help=False)
    parser.add_argument('-H', action='store_true', help="显示帮助和示例")
    parser.add_argument('-I', type=str, help="单文件处理的输入文件路径")
    parser.add_argument('-M', nargs='+', help="多文件处理的输入文件路径")
    parser.add_argument('-O', type=str, help="输出文件路径")
    parser.add_argument('-Creplace', nargs=2, action='append', default=[], help="替换操作：正则表达式 替换符")
    parser.add_argument('-Ctake', nargs=1, action='append', default=[], help="提取操作：正则表达式")
    parser.add_argument('-CURL', nargs=1, action='append', default=[], help="URL 编码操作（特殊字符）：正则表达式")
    parser.add_argument('-Curl', nargs=1, action='append', default=[], help="URL 编码操作（所有字符）：正则表达式")
    parser.add_argument('-CHTML', nargs=1, action='append', default=[], help="HTML 编码操作（特殊字符）：正则表达式")
    parser.add_argument('-Chtml', nargs=1, action='append', default=[], help="HTML 编码操作（所有字符）：正则表达式")
    parser.add_argument('-CJS', nargs=1, action='append', default=[], help="JS 编码操作（特殊字符）：正则表达式")
    parser.add_argument('-Cjs', nargs=1, action='append', default=[], help="JS 编码操作（所有字符）：正则表达式")
    parser.add_argument('-Rsingle', action='append_const', const=('single', ''), default=[], help="去重操作")
    parser.add_argument('-Rsave', action='append', default=[], help="保留操作：正则表达式")
    parser.add_argument('-Rdel', action='append', default=[], help="删除操作：正则表达式")
    
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
    
    input_path = args.I
    input_paths = args.M if args.M else []
    output_path = args.O
    
    if input_path and not os.path.exists(input_path):
        print(f"错误：输入文件 '{input_path}' 不存在")
        return
    for path in input_paths:
        if not os.path.exists(path):
            print(f"错误：输入文件 '{path}' 不存在")
            return
    
    column_ops = []
    for old, new in args.Creplace or []:
        column_ops.append(('replace', old, new))
    for pattern in args.Ctake or []:
        column_ops.append(('take', pattern[0], None))
    for pattern in args.CURL or []:
        column_ops.append(('URL', pattern[0], encode_url_special))
    for pattern in args.Curl or []:
        column_ops.append(('url', pattern[0], encode_url_all))
    for pattern in args.CHTML or []:
        column_ops.append(('HTML', pattern[0], encode_html_special))
    for pattern in args.Chtml or []:
        column_ops.append(('html', pattern[0], encode_html_all))
    for pattern in args.CJS or []:
        column_ops.append(('JS', pattern[0], encode_js_special))
    for pattern in args.Cjs or []:
        column_ops.append(('js', pattern[0], encode_js_all))
    
    row_ops = args.Rsingle
    for keyword in args.Rsave or []:
        row_ops.append(('save', keyword))
    for keyword in args.Rdel or []:
        row_ops.append(('delete', keyword))
    
    if input_path:
        process_file(input_path, column_ops, row_ops, output_path)
    else:
        merge_and_process_files(input_paths, column_ops, row_ops, output_path)

if __name__ == "__main__":
    main()