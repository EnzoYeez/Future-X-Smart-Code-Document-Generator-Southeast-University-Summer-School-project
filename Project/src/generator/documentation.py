# generator/documentation.py
from openai import OpenAI
from pathlib import Path
import traceback
import json

class DocumentationGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_language_from_extension(self, filename):
        ext = Path(filename).suffix.lower()
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.java': 'Java',
            '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.php': 'PHP', '.rb': 'Ruby',
            '.go': 'Go', '.rs': 'Rust', '.swift': 'Swift', '.kt': 'Kotlin',
            '.scala': 'Scala', '.r': 'R', '.m': 'Objective-C', '.pl': 'Perl',
            '.sh': 'Shell', '.sql': 'SQL', '.html': 'HTML', '.css': 'CSS',
            '.vue': 'Vue.js', '.jsx': 'React JSX', '.tsx': 'TypeScript React'
        }
        return language_map.get(ext, '未知语言')

    def generate_batch_documentation(self, file_contents, project_name, lang='zh', style='manual'):
        """生成批量文件的综合文档"""
        try:
            # 分析项目结构
            project_analysis = self.analyze_project_structure(file_contents)
            
            # 生成综合文档
            if style == 'tutorial':
                prompt = self.create_batch_tutorial_prompt(file_contents, project_name, project_analysis, lang)
            elif style == 'api':
                prompt = self.create_batch_api_prompt(file_contents, project_name, project_analysis, lang)
            elif style == 'comment':
                prompt = self.create_batch_comment_prompt(file_contents, project_name, project_analysis, lang)
            elif style == 'insight':
                prompt = self.create_batch_insight_prompt(file_contents, project_name, project_analysis, lang)
            else:
                prompt = self.create_batch_manual_prompt(file_contents, project_name, project_analysis, lang)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional software architect and documentation expert. Analyze the entire project structure and generate comprehensive documentation." if lang == 'en'
                        else "你是一个专业的软件架构师和技术文档专家，擅长分析整个项目结构并生成全面的技术文档。请用中文回答，格式清晰易读。"
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"生成批量文档时出错: {str(e)}")

    def analyze_project_structure(self, file_contents):
        """分析项目结构"""
        analysis = {
            'total_files': len(file_contents),
            'languages': {},
            'directories': set(),
            'file_types': {},
            'main_files': [],
            'config_files': [],
            'test_files': []
        }
        
        for filepath, content in file_contents.items():
            # 分析目录结构
            path_parts = Path(filepath).parts
            if len(path_parts) > 1:
                analysis['directories'].add(path_parts[0])
            
            # 分析语言分布
            language = self.get_language_from_extension(filepath)
            analysis['languages'][language] = analysis['languages'].get(language, 0) + 1
            
            # 分析文件类型
            filename = Path(filepath).name.lower()
            if filename in ['main.py', 'app.py', 'index.js', 'main.js', 'index.html']:
                analysis['main_files'].append(filepath)
            elif filename.startswith('test_') or 'test' in filename:
                analysis['test_files'].append(filepath)
            elif filename in ['package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml']:
                analysis['config_files'].append(filepath)
            
            # 统计文件类型
            ext = Path(filepath).suffix
            analysis['file_types'][ext] = analysis['file_types'].get(ext, 0) + 1
        
        analysis['directories'] = list(analysis['directories'])
        return analysis

    def create_batch_manual_prompt(self, file_contents, project_name, analysis, lang='zh'):
        if lang == 'en':
            prompt = f"""
Generate comprehensive technical documentation for the project: {project_name}

Project Analysis:
- Total files: {analysis['total_files']}
- Languages: {', '.join([f"{lang}({count})" for lang, count in analysis['languages'].items()])}
- Main directories: {', '.join(analysis['directories'])}
- Main files: {', '.join(analysis['main_files'])}

Files to analyze:
"""
            for filepath, content in list(file_contents.items())[:10]:  # 限制文件数量避免token超限
                prompt += f"\n**File: {filepath}**\n```\n{content[:1000]}...\n```\n"
            
            prompt += """
Generate documentation including:
- Project Overview
- Architecture Analysis  
- Key Components
- File Structure
- Dependencies
- Usage Instructions
"""
        else:
            # 判断是否为GitHub项目
            is_github = project_name.endswith('.github')
            project_display_name = project_name.replace('.github', '') if is_github else project_name
            
            prompt = f"""
请为{"GitHub仓库" if is_github else "项目"} "{project_display_name}" 生成全面的技术文档。

项目分析概况:
- 文件总数: {analysis['total_files']}
- 编程语言分布: {', '.join([f"{lang}({count}个文件)" for lang, count in analysis['languages'].items()])}
- 主要目录: {', '.join(analysis['directories']) if analysis['directories'] else '无子目录'}
- 核心文件: {', '.join(analysis['main_files']) if analysis['main_files'] else '未检测到明显的入口文件'}
- 配置文件: {', '.join(analysis['config_files']) if analysis['config_files'] else '无'}
- 测试文件: {len(analysis['test_files'])}个

需要分析的文件内容:
"""
            # 只分析前10个文件，避免token超限
            for i, (filepath, content) in enumerate(list(file_contents.items())[:10]):
                prompt += f"\n**文件: {filepath}**\n```\n{content[:1000]}{'...(内容过长已截断)' if len(content) > 1000 else ''}\n```\n"
            
            if len(file_contents) > 10:
                prompt += f"\n（还有 {len(file_contents) - 10} 个文件未完全显示）\n"
            
            github_specific = """
## 🐙 GitHub仓库分析
[基于GitHub仓库的特点进行分析，包括开源项目的特色、贡献指南等]

## 🚀 快速开始
[如何克隆和运行这个GitHub项目]

## 🤝 贡献指南
[如何为该开源项目做贡献]
""" if is_github else ""
            
            prompt += f"""
请按照以下格式生成{"GitHub仓库" if is_github else "项目"}文档：

# 📚 {"GitHub仓库" if is_github else "项目"}技术文档

## 🎯 项目概述
[项目的主要功能、用途和特色]

## 🏗️ 项目架构
[整体架构设计、技术栈选择、模块划分]

## 📁 目录结构
[详细的目录结构说明]

## 🔧 核心组件分析
[主要模块和组件的功能分析]
{github_specific}
## 💡 使用建议
[提供代码使用的最佳实践和建议]

## ⚠️ 注意事项
[使用时需要注意的问题]

## 📋 依赖关系
[项目的外部依赖和内部模块关系]

## 🔮 优化建议
[代码改进和功能扩展建议]

请确保文档详细、准确，并提供实用的分析和建议。
"""
        return prompt

    def create_batch_tutorial_prompt(self, file_contents, project_name, analysis, lang='zh'):
        if lang == 'en':
            return f"""
Create a beginner-friendly tutorial for the project: {project_name}

Project has {analysis['total_files']} files in languages: {', '.join(analysis['languages'].keys())}

Files:
{self._format_files_for_prompt(file_contents, 8)}

Write a step-by-step tutorial explaining how this project works, suitable for beginners.
"""
        else:
            return f"""
请为项目 "{project_name}" 生成适合初学者的中文教程文档。

项目包含 {analysis['total_files']} 个文件，主要使用: {', '.join(analysis['languages'].keys())}

文件内容:
{self._format_files_for_prompt(file_contents, 8)}

请生成详细的教程，包括项目介绍、环境搭建、代码解析、运行步骤等，适合初学者理解。
"""

    def create_batch_api_prompt(self, file_contents, project_name, analysis, lang='zh'):
        if lang == 'en':
            return f"""
Generate API documentation for the project: {project_name}

Files:
{self._format_files_for_prompt(file_contents, 8)}

Focus on endpoints, functions, classes that can be used as APIs. Include parameters, return values, and examples.
"""
        else:
            return f"""
请为项目 "{project_name}" 生成 API 风格的中文文档。

文件内容:
{self._format_files_for_prompt(file_contents, 8)}

重点分析可作为API使用的接口、函数、类，包括参数说明、返回值、使用示例等。
"""

    def create_batch_comment_prompt(self, file_contents, project_name, analysis, lang='zh'):
        if lang == 'en':
            return f"""
Add comprehensive comments to explain the project: {project_name}

Files:
{self._format_files_for_prompt(file_contents, 6)}

Provide detailed explanations for the code logic and structure.
"""
        else:
            return f"""
请为项目 "{project_name}" 的代码添加详细的中文注释说明。

文件内容:
{self._format_files_for_prompt(file_contents, 6)}

为关键代码添加注释，解释逻辑和实现思路。
"""

    def create_batch_insight_prompt(self, file_contents, project_name, analysis, lang='zh'):
        if lang == 'en':
            return f"""
Provide deep architectural analysis for the project: {project_name}

Project Analysis:
- {analysis['total_files']} files
- Languages: {analysis['languages']}
- Structure: {analysis['directories']}

Files:
{self._format_files_for_prompt(file_contents, 8)}

Analyze architecture, performance, scalability, and provide optimization suggestions.
"""
        else:
            return f"""
请对项目 "{project_name}" 进行深度架构分析。

项目概况:
- 文件数量: {analysis['total_files']}
- 语言分布: {analysis['languages']}
- 目录结构: {analysis['directories']}

文件内容:
{self._format_files_for_prompt(file_contents, 8)}

请从架构、性能、可扩展性等角度进行深入分析，并提供优化建议和重构思路。分析要尽可能详细和专业。
"""

    def _format_files_for_prompt(self, file_contents, max_files=8):
        """格式化文件内容用于prompt"""
        formatted = ""
        for i, (filepath, content) in enumerate(list(file_contents.items())[:max_files]):
            formatted += f"\n**文件: {filepath}**\n```\n{content[:800]}{'...(截断)' if len(content) > 800 else ''}\n```\n"
        
        if len(file_contents) > max_files:
            formatted += f"\n（还有 {len(file_contents) - max_files} 个文件未完全显示）\n"
        
        return formatted

    def generate_documentation(self, code, filename, lang='zh', style='manual'):
        """原有的单文件文档生成方法"""
        try:
            language = self.get_language_from_extension(filename)
            if style == 'tutorial':
                prompt = self.create_tutorial_prompt(code, language, filename, lang)
            elif style == 'api':
                prompt = self.create_api_prompt(code, language, filename, lang)
            elif style == 'comment':
                prompt = self.create_comment_prompt(code, language, filename, lang)
            elif style == 'insight':
                prompt = self.create_insight_prompt(code, language, filename, lang)
            else:
                prompt = self.create_manual_prompt(code, language, filename, lang)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional documentation generator AI. Write clean, accurate, readable documentation." if lang == 'en'
                        else "你是一个专业的技术文档编写专家，擅长为各种编程语言的代码生成清晰、全面、实用的技术文档。请用中文回答，并且格式要清晰易读。"
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"生成文档时出错: {str(e)}")

    def create_manual_prompt(self, code, language, filename, lang):
        return self.create_documentation_prompt(code, language, filename, lang)

    def create_tutorial_prompt(self, code, language, filename, lang):
        if lang == 'en':
            return f"""
Write a beginner-friendly tutorial for the following {language} code.

Filename: {filename}
Language: {language}

Code:
{code}

Explain each function/module in plain English, with practical use-cases, step-by-step guidance, and example usages.
"""
        else:
            return f"""
请为以下{language}代码生成适合初学者的中文教程。

文件名: {filename}
语言: {language}

代码:
{code}

要求包含每个函数/模块的详细解释，使用步骤、用途说明和使用示例。
"""

    def create_api_prompt(self, code, language, filename, lang):
        if lang == 'en':
            return f"""
Generate RESTful API style documentation for the following {language} code.
Include endpoint descriptions, parameters, request/response examples, and status codes if applicable.

Filename: {filename}
Language: {language}

Code:
{code}
"""
        else:
            return f"""
请为以下{language}代码生成 RESTful 风格的中文 API 文档，包括接口描述、参数说明、请求/响应示例及状态码（如适用）。

文件名: {filename}
语言: {language}

代码:
{code}
"""

    def create_comment_prompt(self, code, language, filename, lang):
        if lang == 'en':
            return f"""
Add inline comments to the following {language} code to explain the logic clearly.
Avoid changing the original structure.

Filename: {filename}
Language: {language}

Code:
{code}
"""
        else:
            return f"""
请为以下{language}代码添加中文注释，解释每个关键步骤的作用，避免改动代码结构。

文件名: {filename}
语言: {language}

代码:
{code}
"""

    def create_insight_prompt(self, code, language, filename, lang):
        if lang == 'en':
            return f"""
Provide a deep architecture-level analysis and optimization suggestions for the following {language} code.
Explain performance trade-offs, scalability, and refactoring opportunities.

Filename: {filename}
Language: {language}

Code:
{code}
"""
        else:
            return f"""
请对以下{language}代码从架构层面进行深入分析，分析地越详细越好，内容尽可能详细丰富多样化，并提出性能优化、可扩展性建议及重构思路。

文件名: {filename}
语言: {language}

代码:
{code}
"""

    def create_documentation_prompt(self, code, language, filename, lang='zh'):
        if lang == 'en':
            return f"""
Generate a full technical documentation for the following {language} code in Markdown format.

**Filename**: {filename}
**Language**: {language}

**Code**:
{code}

The documentation should include:
- Overview
- Architecture
- Functions and Methods (name, params, return, usage)
- Classes (if any)
- Best Practices
- External Dependencies

Write clear, accurate and helpful documentation.
"""
        else:
            return f"""
请为以下{language}代码生成全面的技术文档。文档应该包含以下几个部分：

**文件名**: {filename}
**编程语言**: {language}

**代码内容**:
{language.lower()}
{code}

请按照以下格式生成文档：

# 📋 代码文档

## 📖 概述
[简要描述这个文件/模块的主要功能和用途]

## 🏗️ 整体架构
[描述代码的整体结构和设计思路]

## 📚 函数/方法详解

### 函数名称
**功能描述**: [详细说明函数的作用]
**参数说明**:
- 参数名 (类型): 参数描述

**返回值**: [返回值类型和说明]
**使用示例**:
{language.lower()}
[提供具体的使用示例]

---

## 🔧 类详解 (如果有类的话)

### 类名
**功能描述**: [类的主要功能]
**属性**:
- 属性名 (类型): 属性描述

**方法**:
- 方法名(): 方法功能描述

**使用示例**:
{language.lower()}
[类的使用示例]

---

## 💡 使用建议
[提供代码使用的最佳实践和建议]

## ⚠️ 注意事项
[列出使用时需要注意的问题]

## 🔗 依赖关系
[列出代码的外部依赖]

请确保文档详细、准确，并提供实用的示例。对于每个重要的函数和类都要有清晰的说明。
"""