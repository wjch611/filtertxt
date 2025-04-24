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

def parse_indexed_pattern(pattern: str) -> Tuple[bool, str, int, str, int]:
    """解析形如 'Yabc@-1~aaa^1' 的模式，返回 (include_ends, start_str, start_index, end_str, end_index)。"""
    if pattern == '~':
        return True, '', 0, '', 0
    
    if '~' not in pattern:
        raise ValueError(f"模式 '{pattern}' 必须包含 '~'，如 'start@n~' 或 '~end@m'")

    include_ends = True
    if pattern.startswith('Y'):
        pattern = pattern[1:]
    elif pattern.startswith('N'):
        include_ends = False
        pattern = pattern[1:]
    
    start_part, end_part = pattern.split('~', 1)
    
    start_str, start_index = '', 0
    if start_part:
        if '@' in start_part:
            start_str, index_str = start_part.rsplit('@', 1)
            start_index = int(index_str)
        elif '^' in start_part:
            start_str, index_str = start_part.rsplit('^', 1)
            start_index = int(index_str) * 1000
            if start_index <= 0:
                raise ValueError(f"模式 '{pattern}' 中 '^' 索引必须为正数")
        else:
            start_str = start_part
            start_index = 1
    
    end_str, end_index = '', 0
    if end_part:
        if '@' in end_part:
            end_str, index_str = end_part.rsplit('@', 1)
            end_index = int(index_str)
        elif '^' in end_part:
            end_str, index_str = end_part.rsplit('^', 1)
            end_index = int(index_str) * 1000
            if end_index <= 0:
                raise ValueError(f"模式 '{pattern}' 中 '^' 索引必须为正数")
        else:
            end_str = end_part
            end_index = 1
    
    return include_ends, start_str, start_index, end_str, end_index

def find_nth_occurrence(line: str, substr: str, n: int) -> int:
    """查找字符串中第 n 次出现 substr 的起始位置（n 可正可负）。"""
    if not substr:
        return 0 if n == 0 else -1
    
    if n > 0:
        pos = -1
        for _ in range(n):
            pos = line.find(substr, pos + 1)
            if pos == -1:
                return -1
        return pos
    else:
        matches = [i for i in range(len(line)) if line.startswith(substr, i)]
        if len(matches) < abs(n):
            return -1
        return matches[n]

def find_relative_occurrence(line: str, base_str: str, base_pos: int, target_str: str, n: int) -> int:
    """查找相对于 base_pos 的第 n 个 target_str 的位置（n 必须为正数）。"""
    if not target_str:
        return len(line) if n == 0 else -1
    
    matches = [i for i in range(len(line)) if line.startswith(target_str, i)]
    
    if n > 0:
        for pos in matches:
            if pos > base_pos:
                n -= 1
                if n == 0:
                    return pos
        return -1
    else:
        raise ValueError("相对索引 '^' 必须为正数")
        return -1

def encode_url_special(text: str) -> str:
    """只对 URL 特殊字符进行编码（如空格、<、>、& 等）。"""
    return urllib.parse.quote(text, safe='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~')

def encode_url_all(text: str) -> str:
    """对所有字符进行 URL 编码（每个字符转为 %XX）。"""
    return ''.join(f'%{ord(c):02X}' for c in text)

def encode_html_special(text: str) -> str:
    """只对 HTML 特殊字符进行实体化编码（如 <, >, &, ", '）。"""
    html_entities = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }
    return ''.join(html_entities.get(c, c) for c in text)

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
    """对匹配内容进行编码（URL/HTML/JS），保留原行结构。"""
    include_ends, start_str, start_index, end_str, end_index = parse_indexed_pattern(pattern)
    
    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        
        if pattern == '~':
            encoded = encode_func(line_no_newline)
            result.append(encoded + '\n')
            continue
        
        # 查找开始位置
        if start_index >= 1000:
            base_pos = find_nth_occurrence(line_no_newline, end_str, end_index // 1000)
            if base_pos == -1:
                result.append(line)
                continue
            start_pos = find_relative_occurrence(line_no_newline, end_str, base_pos, start_str, start_index // 1000)
        else:
            start_pos = find_nth_occurrence(line_no_newline, start_str, start_index)
        if start_pos == -1:
            result.append(line)
            continue
        
        # 查找结束位置
        if end_index >= 1000:
            end_pos = find_relative_occurrence(line_no_newline, start_str, start_pos, end_str, end_index // 1000)
        else:
            end_pos = find_nth_occurrence(line_no_newline, end_str, end_index)
        if end_pos == -1:
            end_pos = len(line_no_newline) if not end_str else -1
        if end_pos == -1:
            result.append(line)
            continue
        
        # 调整包含/不包含首位
        if not include_ends:
            start_pos += len(start_str)
        else:
            end_pos += len(end_str) if end_str else 0
        
        # 提取并编码
        content = line_no_newline[start_pos:end_pos]
        if not content:
            result.append(line)
            continue
        encoded_content = encode_func(content)
        new_line = line_no_newline[:start_pos] + encoded_content + line_no_newline[end_pos:]
        result.append(new_line + '\n')
    
    return result

def replace_column(lines: List[str], pattern: str, new_str: str) -> List[str]:
    """在每行中将由 pattern 指定的内容替换为 new_str，支持 'Yabc@-1~aaa^1' 语法。"""
    include_ends, start_str, start_index, end_str, end_index = parse_indexed_pattern(pattern)
    
    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        
        if pattern == '~':
            result.append(new_str + '\n')
            continue
        
        # 查找开始位置
        if start_index >= 1000:
            base_pos = find_nth_occurrence(line_no_newline, end_str, end_index // 1000)
            if base_pos == -1:
                result.append(line)
                continue
            start_pos = find_relative_occurrence(line_no_newline, end_str, base_pos, start_str, start_index // 1000)
        else:
            start_pos = find_nth_occurrence(line_no_newline, start_str, start_index)
        if start_pos == -1:
            result.append(line)
            continue
        
        # 查找结束位置
        if end_index >= 1000:
            end_pos = find_relative_occurrence(line_no_newline, start_str, start_pos, end_str, end_index // 1000)
        else:
            end_pos = find_nth_occurrence(line_no_newline, end_str, end_index)
        if end_pos == -1:
            end_pos = len(line_no_newline) if not end_str else -1
        if end_pos == -1:
            result.append(line)
            continue
        
        # 调整包含/不包含首位
        if not include_ends:
            start_pos += len(start_str)
        else:
            end_pos += len(end_str) if end_str else 0
        
        new_line = line_no_newline[:start_pos] + new_str + line_no_newline[end_pos:]
        result.append(new_line + '\n')
    
    return result

def take_column(lines: List[str], pattern: str) -> List[str]:
    """提取每行中由 pattern 指定的内容，支持 'Yaaa@2~bbb^1' 语法。"""
    include_ends, start_str, start_index, end_str, end_index = parse_indexed_pattern(pattern)
    
    result = []
    for line in lines:
        line_no_newline = line.rstrip('\n')
        
        if pattern == '~':
            result.append(line)
            continue
        
        # 查找开始位置
        if start_index >= 1000:
            base_pos = find_nth_occurrence(line_no_newline, end_str, end_index // 1000)
            if base_pos == -1:
                continue
            start_idx = find_relative_occurrence(line_no_newline, end_str, base_pos, start_str, start_index // 1000)
        else:
            start_idx = find_nth_occurrence(line_no_newline, start_str, start_index)
        if start_idx == -1:
            continue
        
        # 查找结束位置
        if end_index >= 1000:
            end_idx = find_relative_occurrence(line_no_newline, start_str, start_idx, end_str, end_index // 1000)
        else:
            end_idx = find_nth_occurrence(line_no_newline, end_str, end_index)
        if end_idx == -1:
            end_idx = len(line_no_newline) if not end_str else -1
        if end_idx == -1:
            continue
        
        # 调整包含/不包含首位
        if not include_ends:
            start_idx += len(start_str)
        else:
            end_idx += len(end_str) if end_str else 0
        
        extracted = line_no_newline[start_idx:end_idx]
        result.append(extracted + '\n' if not extracted.endswith('\n') else extracted)
    
    if not result:
        print(f"警告：没有行匹配 -Ctake 的模式 '{pattern}'。请检查输入文件是否包含所需字符串。")
    return result

def single_row(lines: List[str]) -> List[str]:
    """去除重复行。"""
    return list(dict.fromkeys(lines))

def save_row(lines: List[str], keyword: str) -> List[str]:
    """保留包含关键字的行，支持 | (或)、& (与)。"""
    def match_keyword(line: str, key: str) -> bool:
        pattern = re.escape(key)
        return bool(re.search(pattern, line))

    if '|' in keyword:
        keywords = keyword.split('|')
        return [line for line in lines if any(match_keyword(line, k) for k in keywords)]
    elif '&' in keyword:
        keywords = keyword.split('&')
        return [line for line in lines if all(match_keyword(line, k) for k in keywords)]
    else:
        return [line for line in lines if match_keyword(line, keyword)]

def delete_row(lines: List[str], keyword: str) -> List[str]:
    """去除包含关键字的行，支持 | (或)、& (与)。"""
    def match_keyword(line: str, key: str) -> bool:
        pattern = re.escape(key)
        return bool(re.search(pattern, line))

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

注意：所有参数都不需要强制使用双引号（"），但建议对包含空格或特殊字符（如 *、|、&、~、@、^、=）的参数使用双引号，特别是在 PowerShell 中。
-Creplace 需要两个参数（匹配符 替换符），-Ctake、-CHTML、-Chtml、-CJS、-Cjs、-CURL、-Curl 只需要一个参数（模式）。
所有列操作严格按命令行顺序执行。
编码操作仅对匹配内容编码，保留原行其他部分不变。
所有输出行均保证以换行符（\\n）结尾。

核心功能：
1. 单文件处理：
   - 列操作：
     * 替换：将每行中由匹配符指定的内容替换为替换符 (-Creplace 匹配符 替换符)
       - 支持索引语法：-Creplace "[Y/N]start@n~end@m" 替换符
         - Y: 包含 start 和 end（默认）；N: 不包含 start 和 end
         - start@n: 第 n 个 start（n>0 从左到右，n<0 从右到左）
         - end@m: 第 m 个 end（n>0 从左到右，n<0 从右到左）
         - start^n: 相对于 end 的第 n 个 start（n>0 右边）
         - end^m: 相对于 start 的第 m 个 end（m>0 右边）
         - 特殊情况：-Creplace "~" 替换符（替换整行）
       - 注意：匹配符必须包含 ~，如 "start@n~"（从第 n 个 start 到行尾）或 "~end@m"（从行首到第 m 个 end）
     * 提取：提取每行中由模式指定的内容 (-Ctake 模式)
       - 支持索引语法：-Ctake "[Y/N]start@n~end@m"
       - 特殊情况：-Ctake "~"（提取整行）
       - 注意：模式必须包含 ~，如 "start@n~" 或 "~end@m"
     * HTML 编码：
       - -CHTML 模式: 仅对特殊字符（<, >, &, ", '）进行实体化编码
       - -Chtml 模式: 对所有字符进行实体化编码（转为 &#xHHHH; 形式）
       - 支持索引语法："[Y/N]start@n~end@m"
       - 特殊情况： "~"（编码整行）
       - 注意：模式必须包含 ~，如 "start@n~" 或 "~end@m"
     * Unicode 编码：
       - -CJS 模式: 仅对特殊字符（\\, ", ', \\n, \\t, \\r）进行 Unicode 编码
       - -Cjs 模式: 对所有字符进行 Unicode 编码（转为 \\uHHHH 形式）
       - 支持索引语法："[Y/N]start@n~end@m"
       - 特殊情况： "~"（编码整行）
       - 注意：模式必须包含 ~，如 "start@n~" 或 "~end@m"
     * URL 编码：
       - -CURL 模式: 仅对特殊字符（空格, <, >, #, %, {, }, |, \\, ^, ~, [, ], `, ;, /, ?, :, @, &, =, +, $, ,）进行编码
       - -Curl 模式: 对所有字符进行编码（转为 %XX 形式）
       - 支持索引语法："[Y/N]start@n~end@m"
       - 特殊情况： "~"（编码整行）
       - 注意：模式必须包含 ~，如 "start@n~" 或 "~end@m"
   - 行操作：
     * 去重：移除重复行 (-Rsingle)
     * 保留：保留包含指定关键字的行 (-Rsave 关键字)
       - 支持逻辑：a|b|c（保留包含 a 或 b 或 c 的行）；a&b&c（保留同时包含 a 和 b 和 c 的行）
     * 删除：去除包含指定关键字的行 (-Rdel 关键字)
       - 支持逻辑：a|b|c（删除包含 a 或 b 或 c 的行）；a&b&c（删除同时包含 a 和 b 和 c 的行）

2. 多文件处理：
   - 合并多个输入文件 (-M)，然后对合并后的文件应用相同的列和行操作

PowerShell 使用注意：
- 特殊字符（如 *、|、&、~、@、^、=）可能被 PowerShell 解析为命令或通配符，必须用双引号包裹参数。例如：
  - 错误：-CURL N=@-1~>^1
  - 正确：-CURL "N=@-1~>^1"
  - 错误：-Rdel //|/*
  - 正确：-Rdel "//|/*"
- 文件路径建议也使用双引号包裹，以避免路径中的特殊字符引发问题。

示例：
1. 单文件处理（对倒数第一个 = 到其右边第一个 > 的内容进行 HTML 编码，仅特殊字符）：
   python filtertxt.py -I input.txt -CHTML "N=@-1~>^1" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：<ImG sRc=x OnErRor=print(1)>

2. 单文件处理（对整行进行 Unicode 编码，所有字符）：
   python filtertxt.py -I input.txt -Cjs "~" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：\\u003c\\u0049\\u006d\\u0047\\u0020\\u0073\\u0052\\u0063\\u003d\\u0078\\u0020\\u004f\\u006e\\u0045\\u0072\\u0052\\u006f\\u0072\\u003d\\u0070\\u0072\\u0069\\u006e\\u0074\\u0028\\u0031\\u0029\\u003e

3. 单文件处理（对从第一个 print(1) 到行尾的内容进行 URL 编码，仅特殊字符）：
   python filtertxt.py -I input.txt -CURL "print(1)@1~" -O output.txt
   输入：<ImG sRc=x OnErRor=print(1)>
   输出：<ImG sRc=x OnErRor=print%28%31%29>

4. 单文件处理（综合操作，严格按顺序执行）：
   python filtertxt.py -I input.txt -Creplace "Yscript@-1~<^1" "DIV" -Ctake "Ndiv@1~>^1" -CHTML "N=@-1~>^1" -Cjs "div@1~" -Curl "print(1)@1~" -Rsingle -Rsave "div|onerror" -Rdel "//|/*" -O output.txt
   说明：
   - 替换从倒数第一个 script 到其右边第一个 < 的内容为 DIV，包含首位
   - 提取从第一个 div 到其右边第一个 > 的内容，不包含首位
   - 对倒数第一个 = 到其右边第一个 > 的内容进行 HTML 编码（仅特殊字符）
   - 对从第一个 div 到行尾的内容进行 Unicode 编码（所有字符）
   - 对从第一个 print(1) 到行尾的内容进行 URL 编码（所有字符）
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
    parser.add_argument('-Creplace', nargs=2, action='append', default=[], help="替换操作：匹配符 替换符")
    parser.add_argument('-Ctake', nargs=1, action='append', default=[], help="提取操作：模式")
    parser.add_argument('-CURL', nargs=1, action='append', default=[], help="URL 编码操作（特殊字符）：模式")
    parser.add_argument('-Curl', nargs=1, action='append', default=[], help="URL 编码操作（所有字符）：模式")
    parser.add_argument('-CHTML', nargs=1, action='append', default=[], help="HTML 编码操作（特殊字符）：模式")
    parser.add_argument('-Chtml', nargs=1, action='append', default=[], help="HTML 编码操作（所有字符）：模式")
    parser.add_argument('-CJS', nargs=1, action='append', default=[], help="JS 编码操作（特殊字符）：模式")
    parser.add_argument('-Cjs', nargs=1, action='append', default=[], help="JS 编码操作（所有字符）：模式")
    parser.add_argument('-Rsingle', action='append_const', const=('single', ''), default=[], help="去重操作")
    parser.add_argument('-Rsave', action='append', default=[], help="保留操作：关键字")
    parser.add_argument('-Rdel', action='append', default=[], help="删除操作：关键字")
    
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
    for op, old, new in args.Creplace:
        column_ops.append(('replace', old, new))
    for pattern in args.Ctake:
        column_ops.append(('take', pattern[0], None))
    for pattern in args.CURL:
        column_ops.append(('URL', pattern[0], encode_url_special))
    for pattern in args.Curl:
        column_ops.append(('url', pattern[0], encode_url_all))
    for pattern in args.CHTML:
        column_ops.append(('HTML', pattern[0], encode_html_special))
    for pattern in args.Chtml:
        column_ops.append(('html', pattern[0], encode_html_all))
    for pattern in args.CJS:
        column_ops.append(('JS', pattern[0], encode_js_special))
    for pattern in args.Cjs:
        column_ops.append(('js', pattern[0], encode_js_all))
    
    row_ops = args.Rsingle
    for keyword in args.Rsave:
        row_ops.append(('save', keyword))
    for keyword in args.Rdel:
        row_ops.append(('delete', keyword))
    
    if input_path:
        process_file(input_path, column_ops, row_ops, output_path)
    else:
        merge_and_process_files(input_paths, column_ops, row_ops, output_path)

if __name__ == "__main__":
    main()