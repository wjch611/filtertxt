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