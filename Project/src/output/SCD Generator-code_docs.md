# Smart Code Document Generator API 文档

## 1. 项目概述

"SCD Generator-code.zip" 是一个智能代码文档生成器项目，提供了通过上传代码文件或项目压缩包，利用AI生成全面技术文档的功能。

## 2. API 列表

### 2.1 `app.py`

#### 2.1.1 `app` 模块

- **描述**：Flask应用程序的模块
- **依赖**：`Flask`, `requests`, `tempfile`, `shutil`, `pathlib`, `re`, `urllib`

#### 2.1.2 `OPENAI_API_KEY`

- **描述**：OpenAI API 密钥
- **类型**：字符串
- **默认值**：`"your-api-key-here"`

#### 2.1.3 `doc_generator`

- **描述**：文档生成器实例
- **类型**：`DocumentationGenerator` 对象
- **初始化**：根据 `OPENAI_API_KEY` 创建实例

#### 2.1.4 `SUPPORTED_EXTENSIONS`

- **描述**：支持的代码文件扩展名集合
- **类型**：集合
- **示例**：`{'.py', '.js', '.ts', ...}`

### 2.2 `documentation.py`

#### 2.2.1 `DocumentationGenerator` 类

- **描述**：文档生成器类
- **方法**：
  - `__init__(api_key)`: 初始化方法
  - `get_language_from_extension(filename)`: 根据文件扩展名获取语言

## 3. 使用示例

```python
from app import app

# 设置 OpenAI API 密钥
app.config['OPENAI_API_KEY'] = "your-api-key-here"

# 创建文档生成器实例
doc_generator = DocumentationGenerator(app.config['OPENAI_API_KEY'])

# 生成文档
language = doc_generator.get_language_from_extension('example.py')
print(f"Detected language: {language}")
```

## 4. 注意事项

- 请确保正确配置 `OPENAI_API_KEY`，否则文档生成功能将无法正常工作。
- 请注意支持的代码文件扩展名，确保上传的文件符合要求。

以上是对 "SCD Generator-code.zip" 项目中的 API 的分析和使用说明，希望对您有帮助。