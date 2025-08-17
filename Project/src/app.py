from flask import Flask, request, jsonify, render_template, send_file
from generator.documentation import DocumentationGenerator
import threading
import webbrowser
import time
import os
import zipfile
import socket
import signal
import sys
import requests
import tempfile
import shutil
from pathlib import Path
import re
from urllib.parse import urlparse

app = Flask(__name__)

# 从环境变量或配置文件获取OpenAI API密钥
OPENAI_API_KEY = "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"

# 初始化文档生成器
doc_generator = None
if OPENAI_API_KEY and OPENAI_API_KEY != "your-api-key-here":
    doc_generator = DocumentationGenerator(OPENAI_API_KEY)

# 支持的代码文件扩展名
SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', 
                       '.go', '.rs', '.swift', '.kt', '.scala', '.r', '.m', '.pl', 
                       '.sh', '.sql', '.html', '.css', '.vue', '.jsx', '.tsx'}

def find_free_port(start_port=9003, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise Exception(f"无法找到可用端口，从 {start_port} 到 {start_port + max_attempts - 1} 都被占用")

def kill_port_process(port):
    """尝试杀死占用指定端口的进程"""
    try:
        import subprocess
        import platform
        
        system = platform.system()
        if system == "Darwin" or system == "Linux":  # macOS or Linux
            try:
                # 查找占用端口的进程ID
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        subprocess.run(['kill', '-9', pid], check=True)
                    print(f"✅ 已清理端口 {port} 上的进程")
                    time.sleep(1)  # 等待端口释放
                    return True
            except subprocess.CalledProcessError:
                pass
        elif system == "Windows":
            try:
                # Windows端口清理
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) > 4:
                            pid = parts[-1]
                            subprocess.run(['taskkill', '/PID', pid, '/F'], check=True)
                            print(f"✅ 已清理端口 {port} 上的进程")
                            time.sleep(1)
                            return True
            except subprocess.CalledProcessError:
                pass
    except ImportError:
        pass
    return False

def signal_handler(sig, frame):
    """优雅地处理Ctrl+C信号"""
    print('\n🛑 正在停止服务器...')
    sys.exit(0)

def open_browser(port):
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/generate-docs', methods=['POST'])
def generate_docs():
    try:
        if not doc_generator:
            return jsonify({'success': False, 'error': 'OpenAI API密钥未配置或无效'})
            
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('content')
        lang = data.get('lang', 'zh')
        style = data.get('style', 'manual')
        is_batch = data.get('is_batch', False)

        if not filename or not content:
            return jsonify({'success': False, 'error': '文件名和内容不能为空'})

        if is_batch:
            # 批量处理模式
            documentation = doc_generator.generate_batch_documentation(content, filename, lang, style)
        else:
            # 单文件处理模式
            documentation = doc_generator.generate_documentation(content, filename, lang, style)

        # 保存为 Markdown 文件
        output_filename = f"{filename.replace('.zip', '')}_docs.md" if is_batch else "output.md"
        
        # 创建输出目录
        os.makedirs('output', exist_ok=True)
        output_path = os.path.join('output', output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(documentation)

        return jsonify({
            'success': True,
            'documentation': documentation,
            'download': '/download-md',
            'filename': output_filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/process-zip', methods=['POST'])
def process_zip():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})

        # 创建上传目录
        os.makedirs('uploads', exist_ok=True)
        upload_path = os.path.join('uploads', file.filename)
        file.save(upload_path)

        # 解析zip文件
        file_contents = extract_code_files(upload_path)
        
        # 清理上传的文件
        os.remove(upload_path)

        if not file_contents:
            return jsonify({'success': False, 'error': '压缩包中没有找到支持的代码文件'})

        return jsonify({
            'success': True,
            'file_contents': file_contents,
            'filename': file.filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'处理压缩包时出错: {str(e)}'})

def extract_code_files(zip_path):
    """从zip文件中提取所有支持的代码文件"""
    file_contents = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                # 跳过目录和隐藏文件
                if file_info.is_dir() or file_info.filename.startswith('.'):
                    continue
                
                # 检查文件扩展名
                file_path = Path(file_info.filename)
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    try:
                        # 读取文件内容
                        with zip_ref.open(file_info.filename) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            if content.strip():  # 只保存非空文件
                                file_contents[file_info.filename] = content
                    except Exception as e:
                        print(f"无法读取文件 {file_info.filename}: {e}")
                        continue
    
    except Exception as e:
        raise Exception(f"无法解析压缩包: {e}")
    
    return file_contents

@app.route('/analyze-github', methods=['POST'])
def analyze_github():
    try:
        data = request.get_json()
        github_url = data.get('github_url', '').strip()
        
        if not github_url:
            return jsonify({'success': False, 'error': 'GitHub URL不能为空'})
        
        # 验证和规范化GitHub URL
        normalized_url = normalize_github_url(github_url)
        if not normalized_url:
            return jsonify({'success': False, 'error': '无效的GitHub URL格式'})
        
        # 下载并解析GitHub仓库
        print(f"📥 正在下载GitHub仓库: {normalized_url}")
        file_contents, repo_info = download_github_repo(normalized_url)
        
        if not file_contents:
            return jsonify({'success': False, 'error': 'GitHub仓库中没有找到支持的代码文件'})
        
        return jsonify({
            'success': True,
            'file_contents': file_contents,
            'repo_info': repo_info,
            'filename': f"{repo_info['name']}.github"
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'网络请求失败: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'分析GitHub仓库时出错: {str(e)}'})

def normalize_github_url(url):
    """规范化GitHub URL"""
    try:
        # 移除多余的空白和末尾的斜杠
        url = url.strip().rstrip('/')
        
        # 支持的GitHub URL格式
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+)',  # 标准格式
            r'github\.com/([^/]+)/([^/]+)',          # 没有https
            r'([^/]+)/([^/]+)',                      # 只有用户名/仓库名
        ]
        
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                username, repo = match.groups()
                # 移除.git后缀
                repo = repo.replace('.git', '')
                return f"https://github.com/{username}/{repo}"
        
        return None
    except Exception:
        return None

def download_github_repo(github_url):
    """下载GitHub仓库并提取代码文件"""
    try:
        # 解析URL获取用户名和仓库名
        parts = github_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            raise Exception("无效的GitHub URL")
        
        username, repo_name = parts[0], parts[1]
        
        # 获取仓库信息
        api_url = f"https://api.github.com/repos/{username}/{repo_name}"
        repo_response = requests.get(api_url, timeout=10)
        
        if repo_response.status_code == 404:
            raise Exception("仓库不存在或为私有仓库")
        elif repo_response.status_code != 200:
            raise Exception(f"获取仓库信息失败: {repo_response.status_code}")
        
        repo_data = repo_response.json()
        
        # 构建下载URL
        download_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.zip"
        
        # 尝试main分支，如果失败则尝试master分支
        response = requests.get(download_url, timeout=30, stream=True)
        if response.status_code != 200:
            download_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/master.zip"
            response = requests.get(download_url, timeout=30, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"下载仓库失败: HTTP {response.status_code}")
        
        # 创建临时文件保存zip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_zip_path = temp_file.name
        
        try:
            # 解析zip文件
            file_contents = extract_code_files_from_github_zip(temp_zip_path, repo_name)
            
            # 整理仓库信息
            repo_info = {
                'name': repo_data.get('name', repo_name),
                'description': repo_data.get('description', ''),
                'language': repo_data.get('language', ''),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
                'url': github_url,
                'size': repo_data.get('size', 0)
            }
            
            return file_contents, repo_info
            
        finally:
            # 清理临时文件
            os.unlink(temp_zip_path)
            
    except requests.exceptions.Timeout:
        raise Exception("下载超时，请检查网络连接或稍后重试")
    except requests.exceptions.ConnectionError:
        raise Exception("网络连接失败，请检查网络设置")
    except Exception as e:
        raise Exception(str(e))

def extract_code_files_from_github_zip(zip_path, repo_name):
    """从GitHub下载的zip文件中提取代码文件"""
    file_contents = {}
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                # 跳过目录
                if file_info.is_dir():
                    continue
                
                file_path = file_info.filename
                
                # GitHub的zip文件包含一个顶级目录，需要去除
                path_parts = file_path.split('/')
                if len(path_parts) <= 1:
                    continue
                
                # 去除顶级目录（通常是 reponame-main 或 reponame-master）
                relative_path = '/'.join(path_parts[1:])
                
                # 跳过隐藏文件、node_modules、.git等目录
                if should_skip_file(relative_path):
                    continue
                
                # 检查文件扩展名
                file_ext = Path(relative_path).suffix.lower()
                if file_ext in SUPPORTED_EXTENSIONS:
                    try:
                        with zip_ref.open(file_info.filename) as file:
                            content = file.read().decode('utf-8', errors='ignore')
                            if content.strip() and len(content) < 100000:  # 限制文件大小
                                file_contents[relative_path] = content
                    except Exception as e:
                        print(f"无法读取文件 {relative_path}: {e}")
                        continue
    
    except Exception as e:
        raise Exception(f"解析GitHub仓库失败: {e}")
    
    return file_contents

def should_skip_file(file_path):
    """判断是否应该跳过某个文件"""
    skip_patterns = [
        'node_modules/', '.git/', '__pycache__/', '.pytest_cache/',
        'venv/', 'env/', '.env/', 'dist/', 'build/', 'target/',
        '.idea/', '.vscode/', '.DS_Store', 'Thumbs.db',
        'package-lock.json', 'yarn.lock', '.gitignore'
    ]
    
    # 跳过隐藏文件和目录
    if file_path.startswith('.') or ('/.') in file_path:
        return True
    
    # 跳过特定模式
    for pattern in skip_patterns:
        if pattern in file_path:
            return True
    
    return False

@app.route('/download-md')
def download_markdown():
    try:
        output_path = os.path.join('output', 'output.md')
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 智能代码文档生成系统启动中...")
    
    # 检查API密钥
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key-here":
        print("⚠️  警告: OpenAI API密钥未配置！")
        print("请设置环境变量 OPENAI_API_KEY 或在代码中配置密钥")
        print("示例: export OPENAI_API_KEY='your-api-key-here'")
    
    # 尝试清理默认端口
    default_port = 9003
    print(f"🔍 检查端口 {default_port} 是否可用...")
    
    if kill_port_process(default_port):
        port = default_port
    else:
        # 查找可用端口
        try:
            port = find_free_port(default_port)
            if port != default_port:
                print(f"⚠️  端口 {default_port} 被占用，使用端口 {port}")
        except Exception as e:
            print(f"❌ {e}")
            print("💡 请手动清理端口后重试，或重启终端")
            sys.exit(1)
    
    print(f"\n🌐 服务地址: http://localhost:{port}")
    print("📋 使用说明:")
    print("   1. 上传代码文件（支持拖拽）或上传项目压缩包")
    print("   2. 选择语言与想要的风格")
    print("   3. 点击生成文档按钮")
    print("   4. 等待AI分析并生成文档")
    print("   5. 复制或保存生成的文档，支持md和pdf文件导出格式")
    print(f"\n💡 提示: 使用 Ctrl+C (不是 Ctrl+Z) 来正确停止服务器")
    print("⚠️  注意: 请确保您的OpenAI API密钥有效且有足够额度")
    print("=" * 60)
    
    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser, args=(port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 启动Flask应用
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
    except KeyboardInterrupt:
        print('\n👋 服务器已停止')
    except Exception as e:
        print(f'\n❌ 服务器启动失败: {e}')
        sys.exit(1)