# -*- coding: utf-8 -*-
import os, sys, socket, logging, click
from flask import Flask, request, url_for, send_from_directory, send_file
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

html = '''
    <!DOCTYPE html>
    <title>Upload File</title>
    <h1>File Upload</h1>
    <form method=post enctype=multipart/form-data>
         <input type=file name=file>
         <input type=submit value=upload name=upload>
    </form>
    '''
    
@app.route('/upload/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<path:filename>')
def download_file(filename):
    file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file):
        return send_file(file)
    else:
        return html + "File not found!"


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def upload_file(path=''):
    if request.method == 'POST':
        file = request.files['file']
        if file and request.form['upload'] == 'upload':
            filename = file.filename
            file.save(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], path), filename))
            file_url = url_for('uploaded_file', filename=filename)
    return html + get_file_list(path)


def is_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']

def get_file_list(folder=""):
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    ret = f"<p>Here are the files in the {path} directory:</p>"
    ret += "<ul style='display:flex;flex-direction: column;flex-wrap: wrap;'>"
    if folder=="" or folder[0] != '/': folder = '/' + folder
    if folder[-1] != '/': folder += '/'
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            if is_image(file):
                ret += f"<li><a href='/download{folder}{file}'><img src='/download{folder}{file}' width='100px'></a></li>"
            else:
                ret += f"<li><a href='/download{folder}{file}'>{file}</a></li>"
        else:
            ret += f"<li><a href='{folder}{file}'>{file}</a></li>"
    ret += "</ul>"
    return ret

def get_ip_addr():
    if sys.platform == 'win32':
        return socket.gethostbyname(socket.gethostname())
    elif sys.platform == 'darwin':
        return os.popen("ipconfig getifaddr en0").read().strip('\n')
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ret = s.getsockname()[0]
        s.close()
        return ret

@click.command()
@click.option('--dir', default=os.path.join(os.getcwd()), help="Usage:python main.py --dir='D:\amomorning\Desktop\\tmp'")
def main(dir):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.config['UPLOAD_FOLDER'] = os.path.abspath(dir)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    host = get_ip_addr()
    port = 32198
    print(f" * Running on http://{host}:{port}")
    print(f" * Syncing folder {app.config['UPLOAD_FOLDER']}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
