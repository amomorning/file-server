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
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB最大文件大小

# 支持的图片格式
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'ico'}

# 可在网页端预览的文件类型
PREVIEWABLE_EXTENSIONS = {
    # 文档类
    'md', 'html', 'htm', 'txt', 'json', 'xml', 'csv', 'log',
    'ini', 'conf', 'yaml', 'yml', 'toml', 'pdf',
    # 图片类
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico'
}

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
        return send_file(file_path, as_attachment=True)
    return "File not found!", 404


@app.route('/preview/<path:filename>')
def preview_file(filename):
    """处理文件预览请求"""
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
        return '<div class="empty-state"><div class="em-num">404</div><div class="em-text">PATH NOT FOUND</div></div>'

    files = sorted(os.listdir(path))

    if not files:
        return '<div class="empty-state"><div class="em-num">&#8709;</div><div class="em-text">EMPTY DIRECTORY</div></div>'

    html_parts = []
    for file in files:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            html_parts.append(generate_file_card(file, folder))
        else:
            html_parts.append(generate_folder_card(file, folder))

    return '\n'.join(html_parts)


def generate_file_card(filename, folder):
    """Swiss-style file card: thumbnail + name + meta + actions."""
    ext = get_file_extension(filename)
    file_type = get_file_type(ext)
    file_path = format_path(folder) + filename

    # Get file size
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
    file_size = format_file_size(os.path.getsize(full_path)) if os.path.exists(full_path) else '—'

    # Determine previewability
    previewable = is_previewable(filename)
    glyph = get_file_glyph(ext)

    # Build thumbnail block.
    # For non-image files a CSS-drawn Bauhaus shape (.shape) is emitted;
    # its form (circle / square / triangle) and color are set by data-type.
    if is_image(filename):
        thumb_html = f"""
            <span class="type-tag">IMG</span>
            <a href="/preview{file_path}" target="_blank">
                <img src="/preview{file_path}" alt="{filename}">
            </a>"""
    else:
        thumb_html = f"""
            <span class="type-tag">{glyph}</span>
            <div class="shape"></div>"""

    # Build action buttons
    if previewable:
        actions_html = f"""
            <a href="/preview{file_path}" class="preview-btn" target="_blank">PREVIEW</a>
            <a href="/download{file_path}" class="download-btn">DOWNLOAD</a>"""
    else:
        actions_html = f'<a href="/download{file_path}" class="download-btn full-btn">DOWNLOAD</a>'

    meta_html = f'{file_size} <span class="sep">/</span> {file_type.upper()}'

    return f"""
    <div class="file-card" data-type="{file_type}">
        <div class="thumb">{thumb_html}
        </div>
        <div class="file-name">{filename}</div>
        <div class="file-meta">{meta_html}</div>
        <div class="file-actions">{actions_html}
        </div>
    </div>"""


def generate_folder_card(folder_name, parent_folder):
    """Bauhaus-style folder card: black square with yellow outline."""
    folder_path = format_path(parent_folder) + folder_name
    return f"""
    <div class="file-card" data-type="folder">
        <div class="thumb">
            <span class="type-tag">DIR</span>
            <div class="shape"></div>
        </div>
        <div class="file-name">{folder_name}</div>
        <div class="file-meta">FOLDER</div>
        <div class="file-actions">
            <a href="{folder_path}" class="folder-btn full-btn">OPEN</a>
        </div>
    </div>"""


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


# Short uppercase glyph shown inside each file's thumbnail block.
# Replaces decorative emoji with abstract, typographic labels
# in keeping with Swiss International Style.
EXT_GLYPHS = {
    'pdf': 'PDF',
    'doc': 'DOC', 'docx': 'DOC',
    'xls': 'XLS', 'xlsx': 'XLS',
    'ppt': 'PPT', 'pptx': 'PPT',
    'txt': 'TXT', 'md': 'MD', 'rtf': 'RTF',
    'zip': 'ZIP', 'rar': 'ZIP', '7z': 'ZIP',
    'tar': 'TAR', 'gz': 'GZ', 'bz2': 'BZ2',
    'mp3': 'AUD', 'wav': 'AUD', 'flac': 'AUD',
    'mp4': 'VID', 'avi': 'VID', 'mkv': 'VID',
    'mov': 'MOV', 'wmv': 'VID', 'flv': 'VID',
    'py': 'PY', 'js': 'JS', 'jsx': 'JSX',
    'ts': 'TS', 'tsx': 'TSX',
    'html': 'HTM', 'htm': 'HTM', 'css': 'CSS',
    'json': 'JSN', 'xml': 'XML',
    'yaml': 'YML', 'yml': 'YML', 'toml': 'TOML',
    'ini': 'INI', 'conf': 'CFG', 'cfg': 'CFG',
    'csv': 'CSV', 'log': 'LOG', 'sql': 'SQL',
    'sh': 'SH', 'bash': 'SH',
    'go': 'GO', 'rs': 'RS', 'java': 'JV',
    'c': 'C', 'cpp': 'C++', 'h': 'H', 'hpp': 'HPP',
    'cs': 'CS', 'php': 'PHP', 'rb': 'RB',
    'kt': 'KT', 'swift': 'SW',
    'vue': 'VUE', 'svg': 'SVG',
    'exe': 'EXE', 'msi': 'MSI',
    'dockerfile': 'DKR', 'makefile': 'MK',
}


def get_file_glyph(ext):
    """Return short uppercase glyph for a file extension (Swiss-style)."""
    if not ext:
        return 'FILE'
    return EXT_GLYPHS.get(ext, ext.upper()[:3])


def generate_breadcrumb(folder):
    """
    Swiss-style breadcrumb.
    e.g. ROOT / DOCS / 2024  (last segment highlighted in vermilion)
    """
    # Normalize to forward slashes for cross-platform paths
    parts = [p for p in folder.replace('\\', '/').split('/') if p]

    breadcrumb = '<a href="/">ROOT</a>'

    current_path = ''
    for i, part in enumerate(parts):
        current_path += '/' + part
        is_last = (i == len(parts) - 1)
        cls = ' class="current"' if is_last else ''
        breadcrumb += f' <span class="sep">/</span> <a href="{current_path}"{cls}>{part.upper()}</a>'

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


def format_file_size(size_bytes):
    """
    格式化文件大小为人类可读格式
    例如: 1024 -> 1 KB, 1048576 -> 1 MB
    """
    if size_bytes == 0:
        return '0 B'

    size_names = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f'{size:.1f} {size_names[i]}'


def is_previewable(filename):
    """判断文件是否可在网页端直接预览"""
    ext = get_file_extension(filename)
    return ext in PREVIEWABLE_EXTENSIONS


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
