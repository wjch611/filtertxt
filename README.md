# Filtertxt.py - 文本处理工具

`filtertxt.py` 是一个基于 Python 的命令行文本处理工具，支持对文本文件进行列操作（替换、提取、编码）和行操作（去重、保留、删除）。它使用正则表达式进行匹配，适合处理结构化或半结构化的文本数据，例如日志文件、HTML 文件或自定义格式的文本。

## 功能特点

### 1. 列操作

- 替换

  ：将每行中匹配正则表达式的部分替换为指定字符串。

  - 命令：`-Creplace <正则表达式> <替换符>`

- 提取

  ：提取每行中匹配正则表达式的部分。

  - 命令：`-Ctake <正则表达式>`

- 编码

  ：

  - HTML 编码

    ：

    - `-CHTML <正则表达式>`：仅对特殊字符（`<`, `>`, `&`, `"`, `'`）进行实体化编码。
    - `-Chtml <正则表达式>`：对所有字符进行实体化编码（转为 `&#xHHHH;` 形式）。

  - Unicode 编码

    ：

    - `-CJS <正则表达式>`：仅对特殊字符（`\`, `"`, `'`, `\n`, `\t`, `\r`）进行 Unicode 编码。
    - `-Cjs <正则表达式>`：对所有字符进行 Unicode 编码（转为 `\uHHHH` 形式）。

  - URL 编码

    ：

    - `-CURL <正则表达式>`：仅对特殊字符（空格, `<`, `>`, `#`, `%`, `{`, `}`, `|`, `\`, `^`, `~`, `[`, `]`, ```, `;`, `/`, `?`, `:`, `@`, `&`, `=`, `+`, `$`, `,`）进行编码。
    - `-Curl <正则表达式>`：对所有字符进行编码（转为 `%XX` 形式）。

### 2. 行操作

- 去重

  ：移除重复行。

  - 命令：`-Rsingle`

- 保留

  ：保留匹配正则表达式的行，支持逻辑运算。

  - 命令：`-Rsave <正则表达式>`
  - 支持逻辑：`a|b|c`（匹配 a 或 b 或 c 的行）；`a&b&c`（同时匹配 a 和 b 和 c 的行）。

- 删除

  ：删除匹配正则表达式的行，支持逻辑运算。

  - 命令：`-Rdel <正则表达式>`
  - 支持逻辑：`a|b|c`（删除匹配 a 或 b 或 c 的行）；`a&b&c`（删除同时匹配 a 和 b 和 c 的行）。

### 3. 文件处理

- 单文件处理

  ：处理单个输入文件。

  - 命令：`-I <输入文件路径>`

- 多文件处理

  ：合并多个输入文件后处理。

  - 命令：`-M <文件1> <文件2> ...`

- 输出文件

  ：指定输出文件路径。

  - 命令：`-O <输出文件路径>`

## 安装

### 1. 依赖

- Python 3.6 或更高版本
- 无需额外安装第三方库（仅使用标准库）

### 2. 下载

将 `filtertxt.py` 下载到本地目录。

### 3. 运行

确保 Python 已安装，然后在命令行中运行：

```bash
python filtertxt.py [参数]
```

## 使用方法

### 基本语法

```bash
python filtertxt.py [选项]
```

### 选项

- `-H`：显示帮助信息和示例。
- `-I <路径>`：指定单文件处理的输入文件路径。
- `-M <路径1> <路径2> ...`：指定多文件处理的输入文件路径（合并处理）。
- `-O <路径>`：指定输出文件路径（必须提供）。
- `-Creplace <正则表达式> <替换符>`：替换操作。
- `-Ctake <正则表达式>`：提取操作。
- `-CURL <正则表达式>`：URL 编码（仅特殊字符）。
- `-Curl <正则表达式>`：URL 编码（所有字符）。
- `-CHTML <正则表达式>`：HTML 编码（仅特殊字符）。
- `-Chtml <正则表达式>`：HTML 编码（所有字符）。
- `-CJS <正则表达式>`：JS 编码（仅特殊字符）。
- `-Cjs <正则表达式>`：JS 编码（所有字符）。
- `-Rsingle`：去重操作。
- `-Rsave <正则表达式>`：保留匹配的行。
- `-Rdel <正则表达式>`：删除匹配的行。

### 注意事项

1. **参数顺序**：列操作（`-Creplace`, `-Ctake`, `-CURL` 等）按命令行顺序执行，行操作（`-Rsingle`, `-Rsave`, `-Rdel`）随后执行。

2. **正则表达式**：所有匹配模式都使用正则表达式，特殊字符（如 `.`, `*`, `|`）需要转义。

3. PowerShell 用户

   ：建议对包含特殊字符的参数使用双引号，例如：

   - 错误：`-CURL .*=.*>`
   - 正确：`-CURL ".*=.*>"`

## 示例

### 示例 1：替换操作

将文件中所有 `example.burpcollaborator.net` 替换为 `1`：

```bash
python filtertxt.py -I input.txt -Creplace "example\.burpcollaborator\.net" "1" -O output.txt
```

- 输入文件 

  ```
  input.txt
  ```

  ：

  ```
  test1 example.burpcollaborator.net test2
  no match here
  another example.burpcollaborator.net end
  ```

- 输出文件 

  ```
  output.txt
  ```

  ：

  ```
  test1 1 test2
  no match here
  another 1 end
  ```

### 示例 2：HTML 编码

对最后一个 `=` 到其后的 `>` 之间的内容进行 HTML 编码（仅特殊字符）：

```bash
python filtertxt.py -I input.txt -CHTML "=[^>]+(?=>)" -O output.txt
```

- 输入文件 

  ```
  input.txt
  ```

  ：

  ```
  <ImG sRc=x OnErRor=print(1)>
  ```

- 输出文件 

  ```
  output.txt
  ```

  ：

  ```
  <ImG sRc=x OnErRor=print(1)>
  ```

### 示例 3：提取操作

提取第一个 `div` 到其后的 `>` 之间的内容：

```bash
python filtertxt.py -I input.txt -Ctake "div[^>]+(?=>)" -O output.txt
```

- 输入文件 

  ```
  input.txt
  ```

  ：

  ```
  <div class="test">content</div>
  ```

- 输出文件 

  ```
  output.txt
  ```

  ：

  ```
  div class="test"
  ```

### 示例 4：综合操作

执行多个操作，按顺序处理：

```bash
python filtertxt.py -I input.txt -Creplace "script[^<]*(?=<)" "DIV" -Ctake "div[^>]+(?=>)" -CHTML "=[^>]+(?=>)" -Cjs "div.*$" -Curl "print\\(1\\).*$" -Rsingle -Rsave "div|onerror" -Rdel "//|/\*" -O output.txt
```

- 说明：
  - 替换最后一个 `script` 到其后的 `<` 之间的内容为 `DIV`。
  - 提取第一个 `div` 到其后的 `>` 之间的内容。
  - 对最后一个 `=` 到其后的 `>` 之间的内容进行 HTML 编码（仅特殊字符）。
  - 对第一个 `div` 到行尾的内容进行 Unicode 编码（所有字符）。
  - 对第一个 `print(1)` 到行尾的内容进行 URL 编码（所有字符）。
  - 移除重复行。
  - 保留包含 `div` 或 `onerror` 的行。
  - 删除包含 `//` 或 `/*` 的行。

## 常见问题

### 1. 正则表达式语法错误

如果正则表达式无效，工具会提示错误。例如：

```
错误：无效的正则表达式 'print(1).*$'：unescaped parentheses
```

**解决方法**：转义特殊字符，例如 `print\(1\)\.*$`。

### 2. 没有匹配内容

如果 `-Ctake` 没有匹配到任何内容，工具会提示：

```
警告：没有行匹配 -Ctake 的正则表达式 'xxx'。请检查输入文件是否包含所需内容。
```

**解决方法**：检查正则表达式是否正确，或者输入文件是否包含匹配的内容。

### 3. PowerShell 特殊字符问题

在 PowerShell 中，特殊字符可能被解析为命令或通配符。例如：

- 错误：`-Rdel //|/*`
- 正确：`-Rdel "//|/*"`

## 贡献

欢迎提交问题或改进建议！请通过 GitHub Issues 联系。

## 许可证

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。