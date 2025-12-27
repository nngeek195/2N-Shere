import os
import threading
import webbrowser
import socket
import logging
import sys
import io
import base64
import mimetypes
import qrcode
from flask import Flask, request, send_from_directory, jsonify, render_template_string
from werkzeug.utils import secure_filename
from tkinter import Tk, Button, Label
import ctypes

# -----------------------------
# Admin check (firewall hint)
# -----------------------------
try:
    ctypes.windll.shell32.IsUserAnAdmin()
except:
    pass

# -----------------------------
# Base directory (EXE safe)
# -----------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

ALLOWED_EXTENSIONS = {
    'txt','pdf','png','jpg','jpeg','gif',
    'doc','docx','xls','xlsx','ppt','pptx',
    'zip','rar','7z','mp4','mp3','wav',
    'mov','avi','mkv','apk','exe','iso'
}

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# -----------------------------
# Helpers
# -----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def generate_qr_base64(url):
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    files = []
    for f in sorted(os.listdir(UPLOAD_FOLDER), reverse=True):
        path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(path):
            mime, _ = mimetypes.guess_type(path)
            files.append({
                "name": f,
                "size": os.path.getsize(path),
                "mime": mime or "application/octet-stream"
            })

    ip = get_local_ip()
    port = 5000
    url = f"http://{ip}:{port}"

    return render_template_string(
        INDEX_HTML,
        files=files,
        server_ip=ip,
        server_port=port,
        qr_code=generate_qr_base64(url)
    )

@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify(success=False), 400

    for file in request.files.getlist('files'):
        if file and allowed_file(file.filename):
            name = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, name)

            count = 1
            base, ext = os.path.splitext(name)
            while os.path.exists(path):
                name = f"{base}_{count}{ext}"
                path = os.path.join(UPLOAD_FOLDER, name)
                count += 1

            file.save(path)

    return jsonify(success=True)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if os.path.exists(path):
        os.remove(path)
    return jsonify(success=True)

# ✅ FIXED NAME
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# -----------------------------
# HTML (UNCHANGED UI)
# -----------------------------
INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2N Share</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --glass-bg: rgba(255, 255, 255, 0.95);
        }
        body {
            background: #f0f2f5;
            background-image: radial-gradient(#dfe4ea 1px, transparent 1px);
            background-size: 20px 20px;
            min-height: 100vh;
            padding-bottom: 60px;
        }
        .navbar { background: var(--primary-gradient); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .main-card {
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.05);
        }
        .upload-zone {
            border: 2px dashed #cbd5e0;
            border-radius: 12px;
            padding: 40px 20px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #f8fafc;
        }
        .upload-zone:hover, .upload-zone.dragover {
            border-color: #667eea;
            background: #edf2ff;
        }
        .file-item {
            transition: background 0.2s;
            border-bottom: 1px solid #eee;
            padding: 12px 15px;
            display: flex;
            align-items: center;
        }
        .file-item:hover { background-color: #f8f9fa; }
        .progress-wrapper { display: none; margin-top: 20px; }
        .progress { height: 10px; border-radius: 5px; }
        .speed-badge {
            background: #eef2ff;
            color: #667eea;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .btn-delete {
            color: #dc3545;
            background: transparent;
            border: none;
            padding: 5px 10px;
            transition: all 0.2s;
        }
        .btn-delete:hover {
            background: #fee2e2;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#"><i class="fas fa-cloud-upload-alt me-2"></i>2N Share</a>
        </div>
    </nav>

    <div class="container">
        <div class="row g-4">
            <div class="col-md-8">
                <div class="main-card p-4 h-100">
                    <h5 class="mb-4 text-secondary"><i class="fas fa-arrow-circle-up me-2"></i>Send Files</h5>
                    
                    <div id="dropZone" class="upload-zone">
                        <i class="fas fa-cloud-upload-alt fa-3x mb-3 text-primary"></i>
                        <h5 class="fw-bold text-dark">Drag & Drop files</h5>
                        <p class="text-muted mb-0">Max 10 GB per upload</p>
                        <input type="file" id="fileInput" multiple hidden>
                    </div>

                    <div class="progress-wrapper" id="progressWrapper">
                        <div class="d-flex justify-content-between mb-1">
                            <span class="small fw-bold">Uploading...</span>
                            <div>
                                <span id="speedMeter" class="speed-badge me-2">0 MB/s</span>
                                <span class="small fw-bold" id="progressPercent">0%</span>
                            </div>
                        </div>
                        <div class="progress">
                            <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" style="width: 0%"></div>
                        </div>
                    </div>

                    <button id="uploadBtn" class="btn btn-primary w-100 mt-4 py-2 fw-bold" style="background: var(--primary-gradient); border:none;">
                        Start Upload
                    </button>
                </div>
            </div>

            <div class="col-md-4">
                <div class="main-card p-4 h-100 text-center">
                    <h5 class="mb-4 text-secondary"><i class="fas fa-mobile-alt me-2"></i>Connect Mobile</h5>
                    <img src="{{ qr_code }}" alt="Scan QR" class="img-fluid border rounded p-1 mb-2" style="max-width: 180px;">
                    <div class="fw-bold text-primary">{{ server_ip }}:{{ server_port }}</div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="main-card">
                    <div class="card-header bg-white p-3">
                        <h5 class="mb-0 text-secondary"><i class="fas fa-folder-open me-2"></i>Shared Files</h5>
                    </div>
                    <div class="list-group list-group-flush" style="max-height: 400px; overflow-y: auto;">
                        {% for file in files %}
                        <div class="file-item">
                            <i class="fas fa-file me-3 text-secondary fa-lg"></i>
                            <div class="flex-grow-1">
                                <a href="{{ url_for('uploaded_file', filename=file.name) }}" target="_blank" class="text-decoration-none text-dark fw-medium">
                                    {{ file.name }}
                                </a>
                                <div class="small text-muted">{{ "%.2f"|format(file.size / 1024 / 1024) }} MB</div>
                            </div>
                            <div class="d-flex align-items-center">
                                <a href="{{ url_for('uploaded_file', filename=file.name) }}" class="btn btn-sm btn-light me-2" download title="Download">
                                    <i class="fas fa-download"></i>
                                </a>
                                <button onclick="deleteFile('{{ file.name }}')" class="btn-delete" title="Delete File">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </div>
                        {% endfor %}
                        {% if not files %}
                            <div class="p-4 text-center text-muted">No files shared yet.</div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const progressWrapper = document.getElementById('progressWrapper');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const speedMeter = document.getElementById('speedMeter');

        // Drag & Drop
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) fileInput.files = e.dataTransfer.files;
        });

        // Delete Function
        function deleteFile(filename) {
            if(confirm('Are you sure you want to delete ' + filename + '?')) {
                fetch('/delete/' + filename, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if(data.success) location.reload();
                    else alert('Failed to delete file');
                });
            }
        }

        // Upload with Speed Meter
        uploadBtn.addEventListener('click', () => {
            if (fileInput.files.length === 0) return alert('Select files first!');

            progressWrapper.style.display = 'block';
            uploadBtn.disabled = true;
            
            const formData = new FormData();
            for (let file of fileInput.files) formData.append('files', file);

            const xhr = new XMLHttpRequest();
            let startTime = new Date().getTime();
            let lastLoaded = 0;

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    progressPercent.innerText = percent + '%';

                    // Speed Calc
                    const currentTime = new Date().getTime();
                    const timeDiff = (currentTime - startTime) / 1000; 
                    if (timeDiff > 0.5) { 
                        const speed = (e.loaded - lastLoaded) / timeDiff;
                        const speedMB = (speed / 1024 / 1024).toFixed(2);
                        speedMeter.innerText = speedMB + ' MB/s';
                        startTime = currentTime;
                        lastLoaded = e.loaded;
                    }
                }
            });

            xhr.onreadystatechange = () => {
                if (xhr.readyState === 4) {
                    uploadBtn.disabled = false;
                    if (xhr.status === 200) location.reload();
                    else alert('Upload failed. Check if file is too large or network connection.');
                }
            };

            xhr.open('POST', '/upload', true);
            xhr.send(formData);
        });
    </script>
</body>
</html>
'''

# -----------------------------
# Server + GUI
# -----------------------------
def run_server():
    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True,
        debug=False,
        use_reloader=False
    )

def start():
    threading.Thread(target=run_server, daemon=True).start()
    webbrowser.open(f"http://{get_local_ip()}:5000")
    start_btn.config(text="Server Running", state="disabled")

def create_gui():
    global start_btn
    root = Tk()
    root.title("2N Share")
    root.geometry("300x200")

    Label(root, text="2N Share", font=("Segoe UI", 20, "bold")).pack(pady=20)

    start_btn = Button(
        root,
        text="🚀 Start Server",
        command=start,
        bg="#4361ee",
        fg="white",
        font=("Segoe UI", 12)
    )
    start_btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
