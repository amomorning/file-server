# -*- coding: utf-8 -*-
import os, sys, socket, logging, click
from flask import Flask, request, url_for, send_from_directory, send_file

app = Flask(__name__)

html = '''
    <!DOCTYPE html>
    <title>Upload File</title>
    <h1>File Upload</h1>
    <form method=post enctype=multipart/form-data>
         <input type=file name=file>
         <input type=submit value=upload>
    </form>
    '''
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_url = url_for('uploaded_file', filename=filename)
            return html + get_file_list()
    return html + get_file_list()

def get_file_list():
    ret = "<p>Here are the files in the download directory:</p>"
    ret += "<ul>"
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        ret += f"<li><a href='/download/{file}'>{file}</a></li>"
    ret += "</ul>"
    return ret

def get_ip_addr():
    if sys.platform == 'win32':
        return socket.gethostbyname(socket.gethostname())
    elif sys.platform == 'darwin':
        return os.popen("ipconfig getifaddr en0").read().strip('\n')

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
