# -*- coding: utf-8 -*-
"""
File sharer — a small Flask server that shares a local directory over HTTP.
Supports drag-and-drop upload, in-browser preview, and folder navigation.
"""

import os
import sys
import socket
import logging

import click
from flask import Flask, render_template, request, send_from_directory, send_file

# Flask app setup
app = Flask(__name__, template_folder='assets')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB upload cap

# Image extensions (rendered as thumbnails)
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'ico'}

# File types renderable inline in the browser
PREVIEWABLE_EXTENSIONS = {
    # documents
    'md', 'html', 'htm', 'txt', 'json', 'xml', 'csv', 'log',
    'ini', 'conf', 'yaml', 'yml', 'toml', 'pdf',
    # images
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico'
}

# Document extensions
DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md'}

# Source-code extensions
CODE_EXTENSIONS = {
    'py', 'js', 'html', 'css', 'json', 'xml', 'java', 'c', 'cpp', 'h', 'hpp',
    'cs', 'php', 'rb', 'go', 'rs', 'kt', 'swift', 'ts', 'jsx', 'tsx', 'vue',
    'sql', 'sh', 'bash', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
    'csv', 'typ', 'log', 'dockerfile', 'makefile', 'r', 'm', 'scala', 'dart'
}

# Audio / video extensions
MEDIA_EXTENSIONS = {'mp3', 'wav', 'flac', 'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'}

# Archive extensions
ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}


# ==================== Routes ====================

@app.route('/upload/<path:filename>')
def uploaded_file(filename):
    """Serve an already-uploaded file from UPLOAD_FOLDER."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def _serve_file(filename, as_attachment):
    """Serve a file from UPLOAD_FOLDER, or 404 if it is missing."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=as_attachment)
    return "File not found!", 404


@app.route('/download/<path:filename>')
def download_file(filename):
    """Serve a file as a download (Content-Disposition: attachment)."""
    return _serve_file(filename, as_attachment=True)


@app.route('/preview/<path:filename>')
def preview_file(filename):
    """Serve a file inline for in-browser preview."""
    return _serve_file(filename, as_attachment=False)


@app.route('/favicon.ico')
def favicon():
    """Return the site favicon."""
    return send_file('assets/favicon_32.png')


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def index(path=''):
    """
    Index route.
    - GET:  render the file list for the path
    - POST: handle a file upload into the path
    """
    if request.method == 'POST':
        handle_file_upload(path)

    breadcrumb = generate_breadcrumb(path)
    file_grid = generate_file_grid(path)

    return render_template('index.html',
                         breadcrumb=breadcrumb,
                         file_grid=file_grid)


# ==================== File handling ====================

def handle_file_upload(path):
    """Read the uploaded file from the POST body and save it under `path`."""
    if 'file' not in request.files:
        return

    file = request.files['file']
    if file and request.form.get('upload') == 'upload':
        save_file(file, path)


def save_file(file, path):
    """Persist the uploaded file under UPLOAD_FOLDER/`path`."""
    filename = file.filename
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], path)
    file.save(os.path.join(upload_path, filename))


def generate_file_grid(folder=""):
    """
    Build the HTML for the file grid under `folder`.
    Returns one card per file/subfolder, sorted by name.
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
    """Bauhaus-style file card: thumbnail + name + meta + actions."""
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


# ==================== Helpers ====================

def get_file_type(ext):
    """
    Map a file extension to a coarse type bucket.
    Returns one of: image, document, code, media, archive, other.
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
# in keeping with the Bauhaus style.
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
    Bauhaus-style breadcrumb.
    e.g. ROOT / DOCS / 2024  (last segment highlighted in yellow)
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
    """Normalize `folder` so it both starts and ends with '/'."""
    if not folder:
        return '/'

    if folder[0] != '/':
        folder = '/' + folder

    if folder[-1] != '/':
        folder += '/'

    return folder


def is_image(filename):
    """True if `filename` has an image extension."""
    return '.' in filename and get_file_extension(filename) in IMAGE_EXTENSIONS


def get_file_extension(filename):
    """Return the lowercase extension of `filename` (no leading dot), or ''."""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def format_file_size(size_bytes):
    """
    Format a byte count as a human-readable string.
    e.g. 1024 -> '1.0 KB', 1048576 -> '1.0 MB'.
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
    """True if the file can be rendered inline in the browser."""
    ext = get_file_extension(filename)
    return ext in PREVIEWABLE_EXTENSIONS


def get_ip_addr():
    """
    Best-effort lookup of the host's LAN IP address.
    Supports Windows, macOS, and Linux.
    """
    if sys.platform == 'win32':
        return socket.gethostbyname(socket.gethostname())
    elif sys.platform == 'darwin':
        return os.popen("ipconfig getifaddr en0").read().strip('\n')
    elif sys.platform == 'linux':
        return os.popen("hostname -I").read().strip('\n').split(' ')[0]
    else:
        # Fallback: open a UDP socket to learn the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ret = s.getsockname()[0]
        s.close()
        return ret


# ==================== CLI entry ====================

@click.command()
@click.argument('dir', default=os.getcwd())
@click.option('--port', default=32198, help='Port to listen on')
@click.option('--debug', is_flag=True, help='Enable Flask debug mode')
def main(dir, port, debug):
    """
    File sharer — share a local directory over HTTP.

    Supports drag-and-drop upload, preview, and download from any
    device on the same LAN.

    \b
    Examples:
        python main.py                    # share the current directory
        python main.py /path/to/folder    # share a specific directory
        python main.py . --port 8080      # use a custom port
    """
    # Silence Flask's request logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Shared directory (absolute path)
    app.config['UPLOAD_FOLDER'] = os.path.abspath(dir)

    # Best-effort LAN IP for the printed URL
    host = get_ip_addr()

    print("🚀 文件共享器启动成功!")
    print(f"📂 共享目录: {app.config['UPLOAD_FOLDER']}")
    print(f"🌐 访问地址: http://{host}:{port}")
    print("💡 提示: 在同一局域网的设备都可以访问此地址")
    print("⚠️  按 Ctrl+C 停止服务器\n")

    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
