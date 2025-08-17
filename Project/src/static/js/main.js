// 所有 JS 逻辑（上传、调用API、模拟进度条、预览、导出）
let selectedFile = null;
let projectData = null;
let githubData = null;
let currentMode = 'single'; // 'single' 或 'project' 或 'github'

const uploadSection = document.getElementById('uploadSection');
const projectUploadSection = document.getElementById('projectUploadSection');
const githubUploadSection = document.getElementById('githubUploadSection');
const fileInput = document.getElementById('fileInput');
const projectInput = document.getElementById('projectInput');
const fileInfo = document.getElementById('fileInfo');
const projectInfo = document.getElementById('projectInfo');
const githubInfo = document.getElementById('githubInfo');
const generateBtn = document.getElementById('generateBtn');

// 切换上传模式
function switchUploadMode(mode) {
  currentMode = mode;

  // 重置状态
  selectedFile = null;
  projectData = null;
  githubData = null;
  fileInfo.classList.remove('show');
  projectInfo.style.display = 'none';
  githubInfo.style.display = 'none';
  generateBtn.disabled = true;
  document.getElementById('resultSection').classList.remove('show');

  // 切换按钮状态
  document.getElementById('singleFileMode').classList.toggle('active', mode === 'single');
  document.getElementById('projectMode').classList.toggle('active', mode === 'project');
  document.getElementById('githubMode').classList.toggle('active', mode === 'github');

  // 切换上传区域
  uploadSection.style.display = mode === 'single' ? 'block' : 'none';
  projectUploadSection.style.display = mode === 'project' ? 'block' : 'none';
  githubUploadSection.style.display = mode === 'github' ? 'block' : 'none';

  // 更新进度提示文本
  const progressTexts = {
    'single': 'AI正在分析您的代码并生成文档，请稍候...',
    'project': 'AI正在分析您的项目结构并生成综合文档，请稍候...',
    'github': 'AI正在分析GitHub仓库并生成项目文档，请稍候...'
  };
  document.getElementById('progressText').textContent = progressTexts[mode];
}

// 单文件上传相关事件
uploadSection.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadSection.classList.add('dragover');
});

uploadSection.addEventListener('dragleave', () => {
  uploadSection.classList.remove('dragover');
});

uploadSection.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadSection.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelect(files[0]);
  }
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    handleFileSelect(e.target.files[0]);
  }
});

// 项目上传相关事件
projectUploadSection.addEventListener('dragover', (e) => {
  e.preventDefault();
  projectUploadSection.classList.add('dragover');
});

projectUploadSection.addEventListener('dragleave', () => {
  projectUploadSection.classList.remove('dragover');
});

projectUploadSection.addEventListener('drop', (e) => {
  e.preventDefault();
  projectUploadSection.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0 && files[0].name.endsWith('.zip')) {
    handleProjectSelect(files[0]);
  } else {
    alert('请上传 .zip 格式的压缩包');
  }
});

projectInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) {
    handleProjectSelect(e.target.files[0]);
  }
});

function handleFileSelect(file) {
  selectedFile = file;
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = `文件大小: ${(file.size / 1024).toFixed(2)} KB`;
  fileInfo.classList.add('show');
  projectInfo.style.display = 'none';
  generateBtn.disabled = false;
}

async function handleProjectSelect(file) {
  if (!file.name.endsWith('.zip')) {
    alert('请选择 .zip 格式的压缩包');
    return;
  }

  // 显示上传进度
  const loadingDiv = document.getElementById('loading');
  loadingDiv.classList.add('show');
  document.getElementById('progressText').textContent = '正在解析压缩包...';

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/process-zip', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      projectData = result;
      displayProjectInfo(result);
      generateBtn.disabled = false;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    alert('处理压缩包失败: ' + error.message);
  } finally {
    loadingDiv.classList.remove('show');
  }
}

// GitHub仓库分析功能
async function analyzeGithubRepo() {
  const githubUrl = document.getElementById('githubUrlInput').value.trim();

  if (!githubUrl) {
    alert('请输入GitHub仓库链接');
    return;
  }

  // 显示加载状态
  const loadingDiv = document.getElementById('loading');
  loadingDiv.classList.add('show');
  document.getElementById('progressText').textContent = '正在下载GitHub仓库...';

  const analyzeBtn = document.querySelector('.github-analyze-btn');
  const originalText = analyzeBtn.textContent;
  analyzeBtn.textContent = '分析中...';
  analyzeBtn.disabled = true;

  try {
    const response = await fetch('/analyze-github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ github_url: githubUrl })
    });

    const result = await response.json();

    if (result.success) {
      githubData = result;
      displayGithubInfo(result);
      generateBtn.disabled = false;
    } else {
      throw new Error(result.error);
    }
  } catch (error) {
    alert('分析GitHub仓库失败: ' + error.message);
  } finally {
    loadingDiv.classList.remove('show');
    analyzeBtn.textContent = originalText;
    analyzeBtn.disabled = false;
  }
}

function displayGithubInfo(data) {
  const { file_contents, repo_info } = data;

  // 分析代码文件
  const totalFiles = Object.keys(file_contents).length;
  const languages = {};

  Object.keys(file_contents).forEach(filepath => {
    const ext = filepath.split('.').pop().toLowerCase();
    const langMap = {
      'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript',
      'java': 'Java', 'cpp': 'C++', 'c': 'C', 'cs': 'C#',
      'php': 'PHP', 'rb': 'Ruby', 'go': 'Go', 'rs': 'Rust'
    };
    const lang = langMap[ext] || ext.toUpperCase();
    languages[lang] = (languages[lang] || 0) + 1;
  });

  const mainLanguage = Object.entries(languages).sort((a, b) => b[1] - a[1])[0]?.[0] || repo_info.language || '混合';

  // 更新仓库信息
  document.getElementById('repoName').textContent = repo_info.name;
  document.getElementById('repoDescription').textContent = repo_info.description || '暂无描述';
  document.getElementById('repoStars').textContent = repo_info.stars || 0;
  document.getElementById('repoForks').textContent = repo_info.forks || 0;
  document.getElementById('repoLanguage').textContent = repo_info.language || 'Mixed';
  document.getElementById('repoLink').href = repo_info.url;

  // 更新分析数据
  document.getElementById('githubCodeFiles').textContent = totalFiles;
  document.getElementById('githubMainLanguage').textContent = mainLanguage;
  document.getElementById('githubRepoSize').textContent = `${repo_info.size || 0} KB`;

  // 显示文件列表
  const fileList = document.getElementById('githubDetectedFiles');
  fileList.innerHTML = '';
  Object.keys(file_contents).slice(0, 15).forEach(filepath => {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.textContent = filepath;
    fileList.appendChild(fileItem);
  });

  if (Object.keys(file_contents).length > 15) {
    const moreItem = document.createElement('div');
    moreItem.className = 'file-item more';
    moreItem.textContent = `... 还有 ${Object.keys(file_contents).length - 15} 个文件`;
    fileList.appendChild(moreItem);
  }

  // 显示GitHub信息区域
  fileInfo.classList.remove('show');
  projectInfo.style.display = 'none';
  githubInfo.style.display = 'block';
}

// **[FIXED]** Added the missing function definition wrapper
function displayProjectInfo(data) {
  const { file_contents, filename } = data;

  // 分析项目数据
  const totalFiles = Object.keys(file_contents).length;
  const languages = {};
  let totalSize = 0;

  Object.entries(file_contents).forEach(([filepath, content]) => {
    // 统计语言
    const ext = filepath.split('.').pop().toLowerCase();
    const langMap = {
      'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript',
      'java': 'Java', 'cpp': 'C++', 'c': 'C', 'cs': 'C#',
      'php': 'PHP', 'rb': 'Ruby', 'go': 'Go', 'rs': 'Rust'
    };
    const lang = langMap[ext] || ext.toUpperCase();
    languages[lang] = (languages[lang] || 0) + 1;

    // 统计大小
    totalSize += content.length;
  });

  const mainLanguage = Object.entries(languages).sort((a, b) => b[1] - a[1])[0]?.[0] || '混合';

  // 更新UI
  document.getElementById('totalFiles').textContent = Object.keys(file_contents).length;
  document.getElementById('codeFiles').textContent = totalFiles;
  document.getElementById('mainLanguage').textContent = mainLanguage;
  document.getElementById('projectSize').textContent = `${(totalSize / 1024).toFixed(2)} KB`;

  // 显示文件列表
  const fileList = document.getElementById('detectedFiles');
  fileList.innerHTML = '';
  Object.keys(file_contents).slice(0, 10).forEach(filepath => {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.textContent = filepath;
    fileList.appendChild(fileItem);
  });

  if (Object.keys(file_contents).length > 10) {
    const moreItem = document.createElement('div');
    moreItem.className = 'file-item more';
    moreItem.textContent = `... 还有 ${Object.keys(file_contents).length - 10} 个文件`;
    fileList.appendChild(moreItem);
  }

  // 显示项目信息区域
  fileInfo.classList.remove('show');
  projectInfo.style.display = 'block';
}


// **[FIXED]** Removed duplicated function and syntax error (stray ';)
async function generateDocumentation() {
  if (currentMode === 'single' && !selectedFile) {
    alert('请先选择一个文件');
    return;
  }

  if (currentMode === 'project' && !projectData) {
    alert('请先上传项目压缩包');
    return;
  }

  if (currentMode === 'github' && !githubData) {
    alert('请先分析GitHub仓库');
    return;
  }

  const loading = document.getElementById('loading');
  const resultSection = document.getElementById('resultSection');
  const docEditor = document.getElementById('documentationEditor');
  const progressBar = document.getElementById('progressBar');

  // 初始化状态
  loading.classList.add('show');
  generateBtn.disabled = true;

  const buttonTexts = {
    'single': '生成中...',
    'project': '分析项目中...',
    'github': '分析仓库中...'
  };
  generateBtn.textContent = buttonTexts[currentMode];

  resultSection.classList.remove('show');
  progressBar.style.width = '0%';

  // 启动模拟进度
  let progress = 0;
  const progressSpeed = currentMode === 'github' ? 600 : (currentMode === 'project' ? 500 : 300);
  const interval = setInterval(() => {
    if (progress >= 95) return;
    progress += Math.random() * 2.5;
    progressBar.style.width = `${Math.min(progress, 95)}%`;
  }, progressSpeed);

  try {
    let requestData;

    if (currentMode === 'single') {
      // 单文件模式
      const fileContent = await readFileContent(selectedFile);
      requestData = {
        filename: selectedFile.name,
        content: fileContent,
        lang: document.getElementById('lang').value,
        style: document.getElementById('style').value,
        is_batch: false
      };
    } else if (currentMode === 'project') {
      // 项目模式
      requestData = {
        filename: projectData.filename,
        content: projectData.file_contents,
        lang: document.getElementById('lang').value,
        style: document.getElementById('style').value,
        is_batch: true
      };
    } else if (currentMode === 'github') {
      // GitHub模式
      requestData = {
        filename: githubData.filename,
        content: githubData.file_contents,
        lang: document.getElementById('lang').value,
        style: document.getElementById('style').value,
        is_batch: true
      };
    }

    const response = await fetch('/generate-docs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });

    const result = await response.json();

    if (result.success) {
      // 设置下载链接
      let nameWithoutExt;
      if (currentMode === 'single') {
        nameWithoutExt = selectedFile.name.split('.').slice(0, -1).join('.');
      } else if (currentMode === 'project') {
        nameWithoutExt = projectData.filename.replace('.zip', '');
      } else if (currentMode === 'github') {
        nameWithoutExt = githubData.repo_info.name;
      }

      const mdLink = document.getElementById('downloadMdBtn');
      mdLink.setAttribute('download', `${nameWithoutExt}-docs.md`);
      mdLink.href = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(result.documentation);

      docEditor.value = result.documentation;
      resultSection.classList.add('show');
      resultSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      throw new Error(result.error || '生成文档失败');
    }

    // 立即进度到 100%
    progressBar.style.width = '100%';
  } catch (error) {
    alert('生成文档时出现错误: ' + error.message);
    progressBar.style.width = '100%';
  } finally {
    clearInterval(interval);
    setTimeout(() => {
      loading.classList.remove('show');
      progressBar.style.width = '0%';
    }, 500);
    generateBtn.disabled = false;
    generateBtn.textContent = '🔄 生成文档';
  }
}

function readFileContent(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsText(file);
  });
}

function copyDocumentation() {
  const documentation = document.getElementById('documentationEditor').value;
  navigator.clipboard.writeText(documentation).then(() => {
    const copyBtn = document.querySelector('.copy-btn');
    const originalText = copyBtn.textContent;
    copyBtn.textContent = '已复制!';
    copyBtn.style.background = 'var(--success-color)';
    setTimeout(() => {
      copyBtn.textContent = originalText;
      copyBtn.style.background = 'var(--warning-color)';
    }, 2000);
  }).catch(() => {
    alert('复制失败，请手动选择文本复制');
  });
}

function renderAndExportPDF() {
  const rawMarkdown = document.getElementById('documentationEditor').value;

  const renderedDiv = document.createElement('div');
  renderedDiv.innerHTML = window.markdownit({ html: true }).render(rawMarkdown);

  renderedDiv.className = 'markdown-body';
  document.body.appendChild(renderedDiv);

  // 设置PDF文件名
  let filename;
  if (currentMode === 'single') {
    filename = `${selectedFile.name.split('.')[0]}-docs.pdf`;
  } else if (currentMode === 'project') {
    filename = `${projectData.filename.replace('.zip', '')}-docs.pdf`;
  } else if (currentMode === 'github') {
    filename = `${githubData.repo_info.name}-docs.pdf`;
  }

  const opt = {
    margin: [5, 10, 10, 10],
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, scrollY: 0 },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    pagebreak: { avoid: ['pre', 'code', 'table'], mode: 'css' }
  };

  html2pdf()
    .set(opt)
    .from(renderedDiv)
    .save()
    .then(() => document.body.removeChild(renderedDiv));
}

// GitHub URL输入框回车事件
document.addEventListener('DOMContentLoaded', function() {
  const githubUrlInput = document.getElementById('githubUrlInput');
  if (githubUrlInput) {
    githubUrlInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        analyzeGithubRepo();
      }
    });
  }
});

function simulateProgress(callback) {
  const progressBar = document.getElementById('progressBar');
  let progress = 0;
  const interval = setInterval(() => {
    if (progress >= 95) {
      clearInterval(interval);
      return;
    }
    progress += Math.random() * 5;
    progressBar.style.width = `${Math.min(progress, 95)}%`;
  }, 300);

  callback(() => {
    clearInterval(interval);
    progressBar.style.width = '100%';
  });
}