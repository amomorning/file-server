# -*- coding: utf-8 -*-
"""
文件共享器 - 一个简单的文件共享服务
支持拖放上传、文件预览、文件夹导航等功能
"""

import os
import sys
import socket
import logging

import click
from flask import Flask, render_template, request, send_from_directory, send_file

# 初始化Flask应用
app = Flask(__name__, template_folder='assets')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大文件大小

# 支持的图片格式
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

# 文档类型扩展名
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md'}

# 代码文件扩展名
CODE_EXTENSIONS = {
    'py', 'js', 'html', 'css', 'json', 'xml', 'java', 'c', 'cpp', 'h', 'hpp',
    'cs', 'php', 'rb', 'go', 'rs', 'kt', 'swift', 'ts', 'jsx', 'tsx', 'vue',
    'sql', 'sh', 'bash', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
    'csv', 'typ', 'log', 'dockerfile', 'makefile', 'r', 'm', 'scala', 'dart'
}

# 音视频扩展名
MEDIA_EXTENSIONS = {'mp3', 'wav', 'flac', 'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'}

# 压缩包扩展名
ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}

# 文件类型图标映射
FILE_ICONS = {
    'pdf': '📄',
    'doc': '📝', 'docx': '📝',
    'xls': '📊', 'xlsx': '📊',
    'ppt': '📽', 'pptx': '📽',
    'txt': '📃',
    'zip': '📦', 'rar': '📦', '7z': '📦',
    'mp3': '🎵', 'wav': '🎵', 'flac': '🎵',
    'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬',
    # 编程语言图标
    'py': '🐍', 'python': '🐍',
    'js': '📜', 'jsx': '⚛️', 'ts': '💎', 'tsx': '💎',
    'html': '🌐', 'css': '🎨',
    'java': '☕', 'c': '⚙', 'cpp': '⚙', 'h': '📋', 'hpp': '📋',
    'cs': '💠', 'php': '🐘',
    'rb': '💎', 'go': '🐹', 'rs': '⚙️',
    'swift': '🍎', 'kt': '🤖',
    'sql': '🗃️', 'sh': '💻', 'bash': '💻',
    'json': '📋', 'xml': '📋', 'yaml': '⚙️', 'yml': '⚙️',
    'csv': '📊', 'typ': '📝',
    'vue': '💚', 'dockerfile': '🐳',
    'r': '📊', 'm': '📊',
    'exe': '⚙', 'msi': '⚙',
}


# ==================== 路由处理 ====================

@app.route('/upload/<path:filename>')
def uploaded_file(filename):
    """处理已上传文件的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<path:filename>')
def download_file(filename):
    """处理文件下载请求"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        return send_file(file_path)
    return "File not found!", 404


@app.route('/favicon.ico')
def favicon():
    """返回网站图标"""
    return send_file('assets/favicon_32.png')


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def index(path=''):
    """
    主页面路由
    - GET: 显示文件列表
    - POST: 处理文件上传
    """
    if request.method == 'POST':
        handle_file_upload(path)

    breadcrumb = generate_breadcrumb(path)
    file_grid = generate_file_grid(path)

    return render_template('index.html',
                         breadcrumb=breadcrumb,
                         file_grid=file_grid)


# ==================== 文件处理函数 ====================

def handle_file_upload(path):
    """处理文件上传"""
    if 'file' not in request.files:
        return

    file = request.files['file']
    if file and request.form.get('upload') == 'upload':
        save_file(file, path)


def save_file(file, path):
    """保存上传的文件"""
    filename = file.filename
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    file.save(os.path.join(upload_path, filename))


def generate_file_grid(folder=""):
    """
    生成文件网格HTML
    返回包含所有文件和文件夹的卡片式布局
    """
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder)

    if not os.path.exists(path):
        return '<div class="empty-state"><div>路径不存在</div></div>'

    files = sorted(os.listdir(path))

    if not files:
        return '<div class="empty-state"><div style="font-size: 48px; margin-bottom: 16px;">📭</div><div>此文件夹为空</div></div>'

    html_parts = []
    for file in files:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            html_parts.append(generate_file_card(file, folder))
        else:
            html_parts.append(generate_folder_card(file, folder))

    return '\n'.join(html_parts)


def generate_file_card(filename, folder):
    """生成单个文件的卡片HTML"""
    ext = get_file_extension(filename)
    file_type = get_file_type(ext)

    if is_image(filename):
        return f"""
        <div class="file-card" data-type="image">
            <a href="/download{format_path(folder)}{filename}" target="_blank">
                <img src="/download{format_path(folder)}{filename}" alt="{filename}">
            </a>
            <div class="file-name">{filename}</div>
            <div class="file-actions">
                <a href="/download{format_path(folder)}{filename}" class="download-btn" target="_blank">⬇ 下载</a>
            </div>
        </div>
        """
    else:
        icon = FILE_ICONS.get(ext, '📄')
        return f"""
        <div class="file-card" data-type="{file_type}">
            <div class="file-icon">{icon}</div>
            <div class="file-name">{filename}</div>
            <div class="file-actions">
                <a href="/download{format_path(folder)}{filename}" class="download-btn" target="_blank">⬇ 下载</a>
            </div>
        </div>
        """


def generate_folder_card(folder_name, parent_folder):
    """生成文件夹的卡片HTML"""
    folder_path = format_path(parent_folder) + folder_name
    return f"""
    <div class="file-card" data-type="folder">
        <div class="file-icon">📁</div>
        <div class="file-name">{folder_name}</div>
        <div class="file-actions">
            <a href="{folder_path}" class="folder-btn">📂 打开</a>
        </div>
    </div>
    """


# ==================== 辅助函数 ====================

def get_file_type(ext):
    """
    根据文件扩展名返回文件类型
    返回值: folder, image, document, code, media, archive, other
    """
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    elif ext in DOCUMENT_EXTENSIONS:
        return 'document'
    elif ext in CODE_EXTENSIONS:
        return 'code'
    elif ext in MEDIA_EXTENSIONS:
        return 'media'
    elif ext in ARCHIVE_EXTENSIONS:
        return 'archive'
    else:
        return 'other'


def generate_breadcrumb(folder):
    """
    生成面包屑导航HTML
    例如: 🏠 根目录 / photos / 2024
    """
    # 统一使用正斜杠分割,兼容Windows和Unix
    parts = [p for p in folder.replace('\\', '/').split('/') if p]

    breadcrumb = '<a href="/">🏠 根目录</a>'

    current_path = ''
    for part in parts:
        current_path += '/' + part
        breadcrumb += f' / <a href="{current_path}">{part}</a>'

    return breadcrumb


def format_path(folder):
    """格式化路径,确保以/开头和结尾"""
    if not folder:
        return '/'

    if folder[0] != '/':
        folder = '/' + folder

    if folder[-1] != '/':
        folder += '/'

    return folder


def is_image(filename):
    """判断文件是否为图片"""
    return '.' in filename and get_file_extension(filename) in IMAGE_EXTENSIONS


def get_file_extension(filename):
    """获取文件扩展名(小写)"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_ip_addr():
    """
    获取本机IP地址
    支持Windows、macOS和Linux系统
    """
    if sys.platform == 'win32':
        return socket.gethostbyname(socket.gethostname())
    elif sys.platform == 'darwin':
        return os.popen("ipconfig getifaddr en0").read().strip('\n')
    elif sys.platform == 'linux':
        return os.popen("hostname -I").read().strip('\n').split(' ')[0]
    else:
        # 通用方法:创建UDP连接获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ret = s.getsockname()[0]
        s.close()
        return ret


# ==================== 命令行入口 ====================

@click.command()
@click.argument('dir', default=os.getcwd())
@click.option('--port', default=32198, help='端口号')
@click.option('--debug', is_flag=True, help='启用调试模式')
def main(dir, port, debug):
    """
    文件共享器

    启动一个简单的文件共享服务器,支持文件上传和下载。

    \b
    示例:
        python main.py                    # 共享当前目录
        python main.py /path/to/folder    # 共享指定目录
        python main.py . --port 8080      # 使用自定义端口
    """
    # 隐藏Flask的日志信息
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # 设置上传目录
    app.config['UPLOAD_FOLDER'] = os.path.abspath(dir)

    # 获取本机IP
    host = get_ip_addr()

    print("🚀 文件共享器启动成功!")
    print(f"📂 共享目录: {app.config['UPLOAD_FOLDER']}")
    print(f"🌐 访问地址: http://{host}:{port}")
    print("💡 提示: 在同一局域网的设备都可以访问此地址")
    print("⚠️  按 Ctrl+C 停止服务器\n")

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
